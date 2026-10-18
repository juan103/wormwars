"""03h's statistics (experiments/03h-history-use/DESIGN.md §6): the partial Spearman correlation as registered
(residuals of ranks, average ties, intercept), and its degenerate cases."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata, spearmanr

from wormwars.e03h.stats import partial_spearman


def test_it_is_the_correlation_of_rank_residuals_given_s():
    rng = np.random.default_rng(0)
    s = rng.normal(size=400)
    h = s + rng.normal(size=400)
    f = s + rng.normal(size=400)
    rho, flag = partial_spearman(h, f, s)
    assert not flag
    rh, rf, rs = rankdata(h), rankdata(f), rankdata(s)
    X = np.column_stack([np.ones_like(rs), rs])
    eh = rh - X @ np.linalg.lstsq(X, rh, rcond=None)[0]
    ef = rf - X @ np.linalg.lstsq(X, rf, rcond=None)[0]
    assert abs(rho - np.corrcoef(eh, ef)[0, 1]) < 1e-12
    assert spearmanr(h, f).statistic > 0.3 and abs(rho) < 0.12  # the shared cause s is removed


def test_a_direct_link_survives_the_covariate():
    rng = np.random.default_rng(1)
    s = rng.normal(size=400)
    h = rng.normal(size=400)
    f = h + 0.5 * s + 0.5 * rng.normal(size=400)
    assert partial_spearman(h, f, s)[0] > 0.6


def test_it_depends_only_on_ranks():
    rng = np.random.default_rng(2)
    s, h, f = rng.normal(size=(3, 200))
    a = partial_spearman(h, f, s)[0]
    b = partial_spearman(np.exp(h), f ** 3, 2 * s + 1)[0]
    assert abs(a - b) < 1e-12


def test_degenerate_inputs_give_zero_and_a_flag():
    rng = np.random.default_rng(3)
    s, h = rng.normal(size=(2, 50))
    for f in (np.ones(50), np.r_[np.zeros(49), 1.0] * 0 + 2.0):
        assert partial_spearman(h, f, s) == (0.0, True)
    assert partial_spearman(s.copy(), h, s) == (0.0, True)  # h is fully explained by s: zero residual variance
