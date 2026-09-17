"""Environment check.

`torch.cuda.is_available()` is not enough: a PyTorch build can report a usable CUDA runtime and
still have no kernels compiled for this GPU's compute capability, which shows up only when a kernel
actually runs. So this script runs real kernels and compares them against CPU.

Exit code 0 = usable, 1 = not usable (with a message saying what to install).
"""

from __future__ import annotations

import platform
import sys


def main() -> int:
    print(f"os        : {platform.platform()}")
    print(f"python    : {sys.version.split()[0]}")

    try:
        import torch
    except ImportError:
        print("torch     : NOT INSTALLED")
        print("\nInstall: pip install torch --index-url https://download.pytorch.org/whl/cu130")
        return 1

    print(f"torch     : {torch.__version__} (cuda {torch.version.cuda})")

    if not torch.cuda.is_available():
        print("cuda      : NOT AVAILABLE")
        print("\nThis is a CPU-only torch build. Install the CUDA build:")
        print("  pip uninstall torch")
        print("  pip install torch --index-url https://download.pytorch.org/whl/cu130")
        return 1

    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    arch_list = torch.cuda.get_arch_list()
    props = torch.cuda.get_device_properties(0)
    print(f"gpu       : {name}  sm_{cap[0]}{cap[1]}  {props.total_memory / 1e9:.2f} GB")
    print(f"arch_list : {arch_list}")

    want = f"sm_{cap[0]}{cap[1]}"
    if want not in arch_list:
        print(f"\nThis torch build has no kernels for {want}.")
        print("For Blackwell (sm_120, e.g. RTX 5080) you need a CUDA 12.8+ or 13.x build:")
        print("  pip install torch --index-url https://download.pytorch.org/whl/cu130")
        return 1

    dev = torch.device("cuda")
    torch.manual_seed(0)

    # 1. dense matmul + nonlinearity + reduction, the brain's hot path in miniature
    a, b = torch.randn(512, 512), torch.randn(512, 512)
    gpu = torch.tanh(a.to(dev) @ b.to(dev)).sum().item()
    cpu = torch.tanh(a @ b).sum().item()
    rel = abs(gpu - cpu) / max(abs(cpu), 1.0)
    print(f"matmul    : gpu={gpu:.6f} cpu={cpu:.6f} rel_err={rel:.2e}")
    if rel > 1e-4:
        print("\nGPU and CPU disagree; the build is not trustworthy here.")
        return 1

    # 2. index_add_ scatter, which every field splat depends on
    idx = torch.randint(0, 100, (10_000,), device=dev)
    out = torch.zeros(100, device=dev).index_add_(0, idx, torch.ones(10_000, device=dev))
    total = out.sum().item()
    print(f"index_add : total={total:.0f} (expected 10000)")
    if abs(total - 10_000) > 0.5:
        print("\nScatter kernel is wrong.")
        return 1

    print("\nOK: this build runs real kernels on this GPU.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
