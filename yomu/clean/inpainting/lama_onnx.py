"""LaMa on the GPU: the verified TorchScript exported once to ONNX, run with DirectML.

The exporter has no ONNX form for the 2-D real FFTs inside LaMa's Fourier units,
so they are written as DFT matrix products (cos/sin built in the graph for the
actual size). Same math, float rounding only: on six page crops (200x360 to
888x800) the ONNX output differs from the TorchScript by at most 0.002 of 255
levels, and runs 6x faster on an RX 6600.

The export is derived from the verified .pt and cached next to it with a sidecar
naming the source SHA-256 and its own SHA-256; a mismatch on either re-exports.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

EXPORT_FORMAT = "lama-dft-matmul-v1"


def onnx_path_for(model_path: Path) -> Path:
    return Path(model_path).with_suffix(".dml.onnx")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sidecar(onnx_path: Path) -> Path:
    return onnx_path.with_suffix(onnx_path.suffix + ".json")


def _cached_export(onnx_path: Path, source_sha256: str) -> bool:
    try:
        meta = json.loads(_sidecar(onnx_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (meta.get("format") == EXPORT_FORMAT and meta.get("source_sha256") == source_sha256
            and onnx_path.exists() and meta.get("onnx_sha256") == _sha256(onnx_path))


def _register_fft_symbolics():
    import torch
    from torch.onnx import register_custom_op_symbolic
    from torch.onnx import symbolic_helper

    float_type = torch.onnx.TensorProtoDataType.FLOAT

    def i64(g, value):
        return g.op("Constant", value_t=torch.tensor(value, dtype=torch.int64))

    def f32(g, value):
        return g.op("Constant", value_t=torch.tensor(value, dtype=torch.float32))

    def size(g, x, axis):
        return g.op("Gather", g.op("Shape", x), i64(g, axis), axis_i=0)

    def angles(g, rows, cols, period):
        # 2*pi*r*c/period, rows x cols
        r = g.op("Cast", g.op("Range", i64(g, 0), rows, i64(g, 1)), to_i=float_type)
        c = g.op("Cast", g.op("Range", i64(g, 0), cols, i64(g, 1)), to_i=float_type)
        outer = g.op("Mul", g.op("Unsqueeze", r, i64(g, [1])), g.op("Unsqueeze", c, i64(g, [0])))
        return g.op("Div", g.op("Mul", outer, f32(g, 2 * math.pi)), g.op("Cast", period, to_i=float_type))

    # A complex tensor travels as a real one with a trailing (re, im) axis.
    def split(g, z):
        return (g.op("Gather", z, i64(g, 0), axis_i=-1), g.op("Gather", z, i64(g, 1), axis_i=-1))

    def pack(g, re, im):
        return g.op("Concat", g.op("Unsqueeze", re, i64(g, [-1])), g.op("Unsqueeze", im, i64(g, [-1])), axis_i=-1)

    def ortho(g, h, w):
        return g.op("Div", f32(g, 1.0), g.op("Sqrt", g.op("Cast", g.op("Mul", h, w), to_i=float_type)))

    def rfftn(g, x, s, dims, norm):
        h, w = size(g, x, 2), size(g, x, 3)
        half = g.op("Add", g.op("Div", w, i64(g, 2)), i64(g, 1))
        aw = angles(g, w, half, w)
        a_re = g.op("MatMul", x, g.op("Cos", aw))
        a_im = g.op("Neg", g.op("MatMul", x, g.op("Sin", aw)))
        ah = angles(g, h, h, h)
        ch, sh = g.op("Cos", ah), g.op("Sin", ah)
        re = g.op("Add", g.op("MatMul", ch, a_re), g.op("MatMul", sh, a_im))
        im = g.op("Sub", g.op("MatMul", ch, a_im), g.op("MatMul", sh, a_re))
        k = ortho(g, h, w)
        return pack(g, g.op("Mul", re, k), g.op("Mul", im, k))

    def irfftn(g, z, s, dims, norm):
        sizes = symbolic_helper._unpack_list(s)
        h, w = g.op("Reshape", sizes[0], i64(g, [])), g.op("Reshape", sizes[1], i64(g, []))
        z_re, z_im = split(g, z)
        half = size(g, z_re, 3)
        ah = angles(g, h, h, h)
        ch, sh = g.op("Cos", ah), g.op("Sin", ah)
        b_re = g.op("Sub", g.op("MatMul", ch, z_re), g.op("MatMul", sh, z_im))
        b_im = g.op("Add", g.op("MatMul", ch, z_im), g.op("MatMul", sh, z_re))
        # Hermitian weights: 1 for DC and (even width) Nyquist, 2 for the rest.
        k = g.op("Cast", g.op("Range", i64(g, 0), half, i64(g, 1)), to_i=float_type)
        weight = g.op("Sub", g.op("Sub", f32(g, 2.0), g.op("Cast", g.op("Equal", k, f32(g, 0.0)), to_i=float_type)),
                      g.op("Cast", g.op("Equal", g.op("Mul", k, f32(g, 2.0)), g.op("Cast", w, to_i=float_type)),
                           to_i=float_type))
        weight = g.op("Unsqueeze", weight, i64(g, [1]))
        aw = angles(g, half, w, w)
        out = g.op("Sub", g.op("MatMul", b_re, g.op("Mul", g.op("Cos", aw), weight)),
                   g.op("MatMul", b_im, g.op("Mul", g.op("Sin", aw), weight)))
        return g.op("Mul", out, ortho(g, h, w))

    symbolics = {
        "aten::fft_rfftn": rfftn,
        "aten::fft_irfftn": irfftn,
        "aten::real": lambda g, z: split(g, z)[0],
        "aten::imag": lambda g, z: split(g, z)[1],
        "aten::complex": lambda g, a, b: pack(g, a, b),
    }
    for name, fn in symbolics.items():
        register_custom_op_symbolic(name, fn, 17)
    return list(symbolics)


def ensure_onnx(model_path: Path, source_sha256: str) -> Path:
    """The cached ONNX export of the verified ``model_path``, exporting it if needed."""
    import torch

    onnx_path = onnx_path_for(model_path)
    if _cached_export(onnx_path, source_sha256):
        return onnx_path
    names = _register_fft_symbolics()
    tmp = onnx_path.with_suffix(".tmp")
    try:
        model = torch.jit.load(str(model_path), map_location="cpu").eval()
        image = torch.rand(1, 3, 256, 384)
        mask = (torch.rand(1, 1, 256, 384) > 0.9).float()
        torch.onnx.export(
            model, (image, mask), str(tmp), opset_version=17, dynamo=False,
            input_names=["image", "mask"], output_names=["out"],
            dynamic_axes={name: {2: "h", 3: "w"} for name in ("image", "mask", "out")})
    finally:
        for name in names:
            torch.onnx.unregister_custom_op_symbolic(name, 17)
    os.replace(tmp, onnx_path)
    _sidecar(onnx_path).write_text(json.dumps({
        "format": EXPORT_FORMAT, "source_sha256": source_sha256, "onnx_sha256": _sha256(onnx_path),
    }), encoding="utf-8")
    return onnx_path


class DirectMLSession:
    """One DirectML session, run under the one GPU lock shared with RapidOCR."""

    def __init__(self, onnx_path: Path):
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.log_severity_level = 3
        from yomu.core.gpu import DIRECTML_LOCK

        with DIRECTML_LOCK:
            self._session = ort.InferenceSession(
                str(onnx_path), sess_options=options,
                providers=["DmlExecutionProvider", "CPUExecutionProvider"])

    def __call__(self, image, mask):
        from yomu.core.gpu import DIRECTML_LOCK

        with DIRECTML_LOCK:
            return self._session.run(None, {"image": image, "mask": mask})[0]
