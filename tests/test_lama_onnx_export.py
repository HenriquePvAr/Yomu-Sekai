"""The LaMa ONNX export writes the 2-D real FFTs as DFT matmuls; same numbers as torch."""
import numpy as np
import pytest

torch = pytest.importorskip("torch")
ort = pytest.importorskip("onnxruntime")

from yomu.clean.inpainting import lama_onnx  # noqa: E402


class _FourierUnit(torch.nn.Module):
    """The FFT round trip of LaMa's FourierUnit, with a mixing step in between."""

    def forward(self, image, mask):
        x = image * (1 - mask)
        ffted = torch.fft.rfftn(x, dim=(-2, -1), norm="ortho")
        ffted = torch.stack((ffted.real, ffted.imag), dim=-1) * 0.7 + 0.01
        ffted = torch.complex(ffted[..., 0], ffted[..., 1])
        return torch.fft.irfftn(ffted, s=x.shape[-2:], dim=(-2, -1), norm="ortho")


def test_export_matches_torch_for_even_and_odd_sizes(tmp_path):
    traced = torch.jit.trace(_FourierUnit(), (torch.rand(1, 3, 32, 48), torch.zeros(1, 1, 32, 48)))
    model_path = tmp_path / "unit.pt"
    traced.save(str(model_path))

    onnx_path = lama_onnx.ensure_onnx(model_path, "source-sha")
    assert lama_onnx._cached_export(onnx_path, "source-sha")
    assert not lama_onnx._cached_export(onnx_path, "other-sha")

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(0)
    for h, w in ((40, 64), (24, 37), (17, 30)):
        image = rng.random((1, 3, h, w), dtype=np.float32)
        mask = (rng.random((1, 1, h, w)) > 0.8).astype(np.float32)
        expected = traced(torch.from_numpy(image), torch.from_numpy(mask)).numpy()
        got = session.run(None, {"image": image, "mask": mask})[0]
        assert got.shape == expected.shape
        assert np.abs(got - expected).max() < 1e-4
