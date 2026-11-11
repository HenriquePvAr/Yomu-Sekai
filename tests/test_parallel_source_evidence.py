"""Parallel layout must see the same physical source inventory as serial layout."""
import test_support._test_bootstrap as _bootstrap  # noqa: F401
import threading
import numpy as np
from yomu.ocr import ocr_line_provenance as provenance, source_completeness
from yomu.ocr.ocr_engine import OCRLine
from yomu.ocr.ocr_balloon import TextGroup
from yomu.pipeline import benchmark_pipeline as pipeline


def test_parallel_preflight_keeps_page_owned_ocr_evidence(monkeypatch):
    previous = provenance.active()
    parent = provenance.activate()
    states = []
    for number in (1,2):
        member = OCRLine(text="SOURCE WORDS", raw_text="SOURCE WORDS", confidence=.99,
            box=(10,10,90,20), polygon=np.array([[10,10],[100,10],[100,30],[10,30]]), page=number)
        group = TextGroup("g", lines=[member], text=member.text, translation="PALAVRAS FONTE")
        with provenance.page(number):
            provenance.record_input_lines([member])
            provenance.record_group(group)
        states.append({"index":number,"image_path":"frozen.png","original_bgr":np.full((60,120,3),255,np.uint8),
                       "raw_lines":[member],"candidates":[],"groups":[group]})
    raw_before = sum(len(p["raw_lines"]) for p in parent.pages.values())
    barrier = threading.Barrier(2)
    observed = []
    def render(image, raw, candidates, groups, *, page_index, **kwargs):
        with provenance.page(page_index):
            barrier.wait(timeout=3)
            proof = source_completeness.check_live_group(groups[0], render_lines=raw)
            observed.append((page_index, proof["status"], set(provenance.active().pages)))
            provenance.record_render_input(groups[0], lines=raw)
        return image.copy(), {}
    monkeypatch.setattr(pipeline,"_pipeline_page_workers",lambda:2)
    monkeypatch.setattr(pipeline,"render_analyzed_image",render)
    try:
        assert pipeline._resolve_layout_overflow_before_settlement(states,None,[]) == 0
        assert sorted(observed) == [(1,"pass",{1}),(2,"pass",{2})]
        assert sum(len(p["raw_lines"]) for p in parent.pages.values()) == raw_before
        assert sum(len(p["render_inputs"]) for p in parent.pages.values()) == 2
    finally:
        if previous is None: provenance.deactivate()
        else: provenance.activate(previous)
