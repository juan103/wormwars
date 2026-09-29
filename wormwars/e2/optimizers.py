"""E2's optimizers beside 02's GA (docs/E2/DESIGN.md): OpenAI-ES and random sampling.

**Encoding.** A genome's 5 404 evolved parameters become one vector z = (w / 0.08, g / 0.04,
ln τ / 0.15, bias / 0.05): the GA's own mutation scales, so a single noise scale σ fits every
coordinate. `decode` maps z back and clamps to the genome's bounds; `project` puts a vector back
inside them.

**OpenAI-ES**, as the design fixes it: antithetic pairs, utilities from centred average ranks (equal
fitness, equal utility; a generation with every fitness equal, or with every antithetic pair tied
within itself, makes no update), Adam on the estimated
gradient, no weight decay. The gradient uses the unclamped perturbations.

**Random sampling** keeps the best genome seen since the last checkpoint (ties to the earliest).
"""

from __future__ import annotations

import numpy as np
import torch
from scipy.stats import rankdata

from ..brain import BrainSpec, Genome

SCALES = {"w": 0.08, "g": 0.04, "tau": 0.15, "bias": 0.05}  # the GA's mutation sigmas (02)


def n_params(spec: BrainSpec) -> int:
    return spec.n_chem + spec.n_gap + 2 * spec.n


def encode(genome: Genome) -> torch.Tensor:
    """[strains, parameters]: the genome in the ES's coordinates."""
    return torch.cat([genome.w / SCALES["w"], genome.g / SCALES["g"],
                      torch.log(genome.tau) / SCALES["tau"], genome.bias / SCALES["bias"]], dim=1)


def decode(z: torch.Tensor, template: Genome) -> Genome:
    """Genomes from ES coordinates, on `template`'s spec and config, clamped to its bounds."""
    spec = template.spec
    z = torch.as_tensor(z, dtype=template.w.dtype, device=template.device)
    a, b, c = spec.n_chem, spec.n_chem + spec.n_gap, spec.n_chem + spec.n_gap + spec.n
    params = {"w": z[:, :a] * SCALES["w"], "g": z[:, a:b] * SCALES["g"],
              "tau": torch.exp(z[:, b:c] * SCALES["tau"]), "bias": z[:, c:] * SCALES["bias"]}
    if template.dale_sign is not None:
        params["dale_sign"] = template.dale_sign[:1].expand(z.shape[0], -1)
    return template.with_params(**params).clamp_()


def project(z: torch.Tensor, template: Genome) -> torch.Tensor:
    """One vector put back inside the bounds (decoded, clamped and re-encoded)."""
    return encode(decode(z[None], template.select([0])))[0]


def utilities(fitness: np.ndarray) -> np.ndarray:
    """Centred average ranks in [-0.5, 0.5]; equal fitness gets equal utility; all equal gives zeros."""
    f = np.asarray(fitness, dtype=np.float64)
    if f.size < 2 or np.all(f == f[0]):
        return np.zeros_like(f)
    r = rankdata(f, method="average")
    return (r - 1) / (f.size - 1) - 0.5


class OpenAIES:
    """One search distribution N(mean, σ²) in the ES coordinates, updated by Adam."""

    def __init__(self, mean: np.ndarray, sigma: float, lr: float, pairs: int, generator: np.random.Generator,
                 beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.mean = np.asarray(mean, dtype=np.float64).copy()
        self.sigma, self.lr, self.pairs, self.rng = float(sigma), float(lr), int(pairs), generator
        self.b1, self.b2, self.eps = beta1, beta2, eps
        self.m = np.zeros_like(self.mean)
        self.v = np.zeros_like(self.mean)
        self.t = 0
        self.flat_generations = 0
        self._noise = None

    def ask(self) -> np.ndarray:
        """[2 × pairs, parameters]: mean + σ ε and mean − σ ε, interleaved."""
        e = self.rng.standard_normal((self.pairs, self.mean.size))
        self._noise = e
        c = np.empty((2 * self.pairs, self.mean.size))
        c[0::2] = self.mean + self.sigma * e
        c[1::2] = self.mean - self.sigma * e
        return c

    def tell(self, fitness: np.ndarray) -> None:
        u = utilities(fitness)
        diff = u[0::2] - u[1::2]
        if not np.any(diff):  # a flat batch, or every pair tied within itself: no information, no update
            self.flat_generations += 1
            return
        grad = diff @ self._noise / (2 * self.pairs * self.sigma)
        self.t += 1
        self.m = self.b1 * self.m + (1 - self.b1) * grad
        self.v = self.b2 * self.v + (1 - self.b2) * grad ** 2
        mh = self.m / (1 - self.b1 ** self.t)
        vh = self.v / (1 - self.b2 ** self.t)
        self.mean = self.mean + self.lr * mh / (np.sqrt(vh) + self.eps)  # ascent


class BestSinceCheckpoint:
    """Random sampling's candidate: the best item offered since the last `take` (ties to the earliest)."""

    def __init__(self):
        self.best, self.item = -np.inf, None

    def offer(self, scores: np.ndarray, items) -> None:
        for s, it in zip(np.asarray(scores, dtype=np.float64), items):
            if s > self.best:
                self.best, self.item = float(s), it

    def take(self):
        item = self.item
        self.best, self.item = -np.inf, None
        return item
