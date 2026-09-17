"""Grid primitives. The adjoint properties here are what the bite-credit rule stands on."""

from __future__ import annotations

import torch

from wormwars.fields import (
    blur,
    diffuse_decay,
    gradient,
    sample_bilinear,
    sample_nearest,
    scale_to_cap,
    splat,
    splat_into,
)

torch.manual_seed(0)


def test_splat_and_sample_nearest_are_adjoint():
    """<splat(p, a), f> == <a, sample(f, p)> -- exactly what bite credit needs."""
    wd, h, w, n = 3, 9, 11, 40
    pts = torch.rand(wd, n, 2) * torch.tensor([w, h])
    a = torch.randn(wd, n)
    f = torch.randn(wd, 1, h, w)
    lhs = (splat(torch.zeros(wd, h, w), pts, a) * f[:, 0]).sum()
    rhs = (a * sample_nearest(f, pts)[:, 0]).sum()
    torch.testing.assert_close(lhs, rhs, rtol=1e-5, atol=1e-5)


def test_splat_conserves_what_it_deposits():
    wd, h, w, n = 2, 7, 7, 50
    pts = torch.rand(wd, n, 2) * torch.tensor([w, h])
    a = torch.rand(wd, n)
    out = splat(torch.zeros(wd, h, w), pts, a)
    torch.testing.assert_close(out.sum(dim=(1, 2)), a.sum(dim=1), rtol=1e-5, atol=1e-5)


def test_splat_drops_points_outside_the_grid():
    pts = torch.tensor([[[-1.0, 3.0], [3.0, 3.0], [99.0, 3.0]]])
    out = splat(torch.zeros(1, 8, 8), pts, torch.ones(1, 3))
    assert out.sum().item() == 1.0


def test_splat_into_writes_only_the_named_channel():
    fields = torch.zeros(2, 4, 6, 6)
    pts = torch.rand(2, 5, 2) * 6
    splat_into(fields, 2, pts, torch.ones(2, 5))
    assert fields[:, 2].sum().item() == 10.0
    assert fields[:, [0, 1, 3]].sum().item() == 0.0


def test_blur_is_symmetric_so_it_is_its_own_adjoint():
    x = torch.randn(2, 5, 7)
    y = torch.randn(2, 5, 7)
    lhs = (blur(x, 1) * y).sum()
    rhs = (x * blur(y, 1)).sum()
    torch.testing.assert_close(lhs, rhs, rtol=1e-5, atol=1e-5)


def test_blur_preserves_mass_away_from_the_border():
    x = torch.zeros(1, 9, 9)
    x[0, 4, 4] = 1.0
    torch.testing.assert_close(blur(x, 1).sum(), torch.tensor(1.0), rtol=1e-6, atol=1e-6)


def test_bilinear_sampling_reads_back_a_constant_field():
    f = torch.full((2, 3, 8, 8), 2.5)
    pts = torch.rand(2, 20, 2) * 6 + 1.0
    out = sample_bilinear(f, pts)
    torch.testing.assert_close(out, torch.full_like(out, 2.5), rtol=1e-5, atol=1e-5)


def test_bilinear_sampling_is_zero_outside():
    f = torch.ones(1, 1, 6, 6)
    pts = torch.tensor([[[-5.0, -5.0], [20.0, 20.0]]])
    assert sample_bilinear(f, pts).abs().sum().item() == 0.0


def test_gradient_points_uphill():
    f = torch.zeros(1, 9, 9)
    f[0] = torch.arange(9, dtype=torch.float32).view(1, 9)  # increases with x
    g = gradient(f)
    assert (g[0, 0, 1:-1, 1:-1] > 0).all(), "dx must be positive where the field rises with x"
    assert g[0, 1].abs().max().item() < 1e-6


def test_diffuse_decay_conserves_then_decays():
    x = torch.zeros(1, 9, 9)
    x[0, 4, 4] = 1.0
    out = diffuse_decay(x, diffusion=0.5, decay=1.0)
    torch.testing.assert_close(out.sum(), torch.tensor(1.0), rtol=1e-6, atol=1e-6)
    assert out[0, 4, 4] < 1.0 and out[0, 3, 4] > 0
    out2 = diffuse_decay(x, diffusion=0.0, decay=0.5)
    torch.testing.assert_close(out2.sum(), torch.tensor(0.5), rtol=1e-6, atol=1e-6)


def test_scale_to_cap_never_lets_more_out_than_is_there():
    avail = torch.tensor([[0.0, 1.0, 5.0]])
    demand = torch.tensor([[3.0, 4.0, 1.0]])
    s = scale_to_cap(avail, demand)
    taken = demand * s
    assert (taken <= avail + 1e-6).all()
    torch.testing.assert_close(taken, torch.tensor([[0.0, 1.0, 1.0]]), rtol=1e-6, atol=1e-6)
