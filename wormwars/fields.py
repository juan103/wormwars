"""Grid fields and the only two ways anything touches them: sample and splat.

Everything in the simulation that involves one wey noticing another goes through a field. There are
no pairwise wey-to-wey terms anywhere, so cost is O(N) in weys and O(H*W) in cells.

Coordinates. Positions are continuous in cell units: `x` in [0, W), `y` in [0, H), stored as
`(x, y)`. Cell `(row, col)` is `(floor(y), floor(x))`. Heading `theta` points along
`(cos theta, sin theta)`; the left-hand normal is `(-sin theta, cos theta)`.

Two sampling modes, on purpose:

- **bilinear** for senses, so gradients are smooth and a wey can climb them.
- **nearest** for combat, because the bite-credit rule needs the splat to be the exact adjoint of
  the sample. Nearest-cell splat and nearest-cell sample are exactly adjoint; bilinear pairs are
  too, but only if both ends use identical weights, which is easy to get subtly wrong.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import Tensor


def sample_bilinear(fields: Tensor, points: Tensor) -> Tensor:
    """Sample every channel at every point.

    fields: [Wd, C, H, W]; points: [Wd, P, 2] in (x, y) cell units. Returns [Wd, C, P].
    Out-of-range points read zero (border padding), which is what "outside the arena" should mean.
    """
    wd, c, h, w = fields.shape
    gx = 2.0 * points[..., 0] / w - 1.0
    gy = 2.0 * points[..., 1] / h - 1.0
    grid = torch.stack((gx, gy), dim=-1).unsqueeze(2)  # [Wd, P, 1, 2]
    out = F.grid_sample(fields, grid, mode="bilinear", padding_mode="zeros", align_corners=False)
    return out[..., 0]  # [Wd, C, P]


def cell_index(points: Tensor, h: int, w: int) -> tuple[Tensor, Tensor]:
    """Nearest-cell index of each point, plus a mask of which points are inside the grid."""
    ix = points[..., 0].floor().long()
    iy = points[..., 1].floor().long()
    inside = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    return (iy.clamp(0, h - 1) * w + ix.clamp(0, w - 1)), inside


def splat(
    out: Tensor, points: Tensor, values: Tensor, mask: Tensor | None = None
) -> Tensor:
    """Add `values` into `out [Wd, H, W]` at the nearest cell of each point.

    points: [Wd, P, 2]; values: [Wd, P]; mask: [Wd, P] of what to deposit at all.
    In-place on `out`, returned for chaining. Uses index_add_, which is nondeterministic on CUDA
    unless deterministic algorithms are enabled -- see the replay notes in the docs.
    """
    wd, h, w = out.shape
    flat_cell, inside = cell_index(points, h, w)
    keep = inside if mask is None else (inside & mask)
    world_offset = torch.arange(wd, device=out.device).view(wd, 1) * (h * w)
    idx = (flat_cell + world_offset).reshape(-1)
    val = (values * keep).reshape(-1)
    out.view(-1).index_add_(0, idx, val)
    return out


def splat_into(
    fields: Tensor, channel: int, points: Tensor, values: Tensor, mask: Tensor | None = None
) -> Tensor:
    """Add `values` into one channel of `fields [Wd, C, H, W]` at the nearest cell of each point.

    `fields[:, c]` is a strided slice and cannot be flattened in place, so the channel offset is
    folded into the global index instead and the whole (contiguous) field tensor is scattered into.
    """
    wd, c, h, w = fields.shape
    flat_cell, inside = cell_index(points, h, w)
    keep = inside if mask is None else (inside & mask)
    plane = (torch.arange(wd, device=fields.device) * c + channel).view(wd, 1) * (h * w)
    idx = (flat_cell + plane).reshape(-1)
    fields.view(-1).index_add_(0, idx, (values * keep).reshape(-1))
    return fields


def sample_nearest(fields: Tensor, points: Tensor) -> Tensor:
    """Nearest-cell read of every channel at every point. The exact adjoint of `splat`.

    fields: [Wd, C, H, W]; points: [Wd, P, 2]. Returns [Wd, C, P], zero outside the grid.
    """
    wd, c, h, w = fields.shape
    flat_cell, inside = cell_index(points, h, w)  # [Wd, P]
    flat = fields.reshape(wd, c, h * w)
    out = torch.gather(flat, 2, flat_cell.unsqueeze(1).expand(wd, c, flat_cell.shape[1]))
    return out * inside.unsqueeze(1)


_BLUR_KERNELS: dict[tuple, Tensor] = {}


def blur_kernel(radius: int, device, dtype) -> Tensor:
    """A separable, symmetric, sum-to-one box-ish kernel. Symmetric so it is its own adjoint."""
    key = (radius, str(device), str(dtype))
    k = _BLUR_KERNELS.get(key)
    if k is None:
        size = 2 * radius + 1
        line = torch.ones(size, device=device, dtype=dtype)
        k2 = torch.outer(line, line)
        k2 = k2 / k2.sum()
        k = k2.view(1, 1, size, size)
        _BLUR_KERNELS[key] = k
    return k


def blur(field: Tensor, radius: int) -> Tensor:
    """Symmetric normalised blur of `[Wd, H, W]` (or `[Wd, C, H, W]`), zero-padded at the border.

    Symmetric and normalised means blur(x) . y == x . blur(y), which is what the bite-credit
    adjoint relies on.
    """
    if radius <= 0:
        return field
    squeeze = field.dim() == 3
    x = field.unsqueeze(1) if squeeze else field
    wd, c, h, w = x.shape
    k = blur_kernel(radius, x.device, x.dtype).expand(c, 1, -1, -1)
    y = F.conv2d(x, k, padding=radius, groups=c)
    return y[:, 0] if squeeze else y


def diffuse_decay(field: Tensor, diffusion: float, decay: float) -> Tensor:
    """One tick of pheromone dynamics: a small 3x3 diffusion then a multiplicative decay.

    `diffusion` is the fraction of each cell handed to its 8 neighbours (uniformly), so
    `diffusion = 0` is pure decay and `diffusion = 1` keeps nothing in place.
    """
    squeeze = field.dim() == 3
    x = field.unsqueeze(1) if squeeze else field
    wd, c, h, w = x.shape
    if diffusion > 0:
        k = torch.full((3, 3), diffusion / 8.0, device=x.device, dtype=x.dtype)
        k[1, 1] = 1.0 - diffusion
        k = k.view(1, 1, 3, 3).expand(c, 1, -1, -1)
        x = F.conv2d(x, k, padding=1, groups=c)
    x = x * decay
    return x[:, 0] if squeeze else x


def gradient(field: Tensor) -> Tensor:
    """Central-difference spatial gradient of `[Wd, H, W]`, returned as `[Wd, 2, H, W]` = (dx, dy)."""
    pad = F.pad(field.unsqueeze(1), (1, 1, 1, 1), mode="replicate")
    dx = 0.5 * (pad[:, :, 1:-1, 2:] - pad[:, :, 1:-1, :-2])
    dy = 0.5 * (pad[:, :, 2:, 1:-1] - pad[:, :, :-2, 1:-1])
    return torch.cat((dx, dy), dim=1)


def scale_to_cap(field: Tensor, demand: Tensor) -> Tensor:
    """Per-cell scaling factor so that total take never exceeds what is there.

    Returns `min(1, field / demand)` with 0/0 defined as 0. This is the shared-food rule and the
    same shape of rule is reused wherever several weys draw on one cell.
    """
    return torch.where(demand > 0, torch.clamp(field / demand.clamp_min(1e-12), max=1.0), torch.zeros_like(demand))
