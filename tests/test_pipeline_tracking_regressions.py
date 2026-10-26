import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from unittest import mock

import pytest

from tests.test_progress_v1 import _ProgressBridge
from yomu.runtime.job_store import JobStatus
import yomu.ui.ui_bridge as ui_bridge

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_navigation_preserves_job_and_canonical_stage_names():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node unavailable")
    source = (ROOT / "static/tradutor_ui.js").read_text(encoding="utf-8")
    activation = source[source.index("function activateTab("):source.index("\n  $$('.rail-tab').forEach(tab => tab.addEventListener")]
    aliases = source[source.index("const stageAliases ="):source.index("  function terminalIdentity(")]
    build = source[source.index("function canonicalProgressStage("):source.index("  function canonicalStageMetric(")]
    script = r"""
const assert = require('node:assert/strict');
let cleared = 0;
const appState = {status:'queued',currentJobId:'new-job', reviewMode:null};
const node = {classList:{add(){},remove(){}},style:{},getBoundingClientRect(){return {right:0,top:0,height:0}}};
const $ = s => s === '.panel-view.active' ? null : node;
const $$ = () => [];
const views = {nova:'view-nova'};
const window = {setTimeout(){},dispatchEvent(){}};
const CustomEvent = function(){};
const document = {documentElement:{style:{setProperty(){}}}};
const railIndicator=node, ambientGlow=null, tabTheme={inicio:{hex:'#000',rgb:'0,0,0'}};
function moveIndicator(){} function staggerReveal(){} function ambientSweep(){} function burstAt(){}
function clearNewTranslationDraftPanels(){cleared++;}
function clearBootstrapSurfaceForFreshTranslation(){}
const terminalRunStatuses = new Set(['failed','finished','cancelled']);
const stageMessages = {};
""" + activation + aliases + build + r"""
activateTab('nova', {preservePipeline:true});
assert.equal(cleared,0);
assert.equal(appState.currentJobId,'new-job');
assert.notEqual(appState.suppressHistoricalResult,true);
activateTab('nova');
assert.equal(cleared,1); // explicit fresh drafts still work
assert.equal(buildPipelineState({status:'running'},{stage_key:'translation',current:2,total:10}).visualStage,'translate');
assert.equal(buildPipelineState({status:'running'},{stage_key:'rendering',current:2,total:10}).visualStage,'render');
assert.equal(buildPipelineState({status:'staging'},{fraction:null}).progressPercent,null);
assert.equal(buildPipelineState({status:'running'},{fraction:null,current:2,total:10}).progressPercent,20);
"""
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("stale", [False, True])
def test_eta_uses_canonical_counter_and_real_progress_timestamp(stale):
    with tempfile.TemporaryDirectory() as folder:
        bridge = _ProgressBridge(Path(folder) / "jobs.sqlite3")
        try:
            job_id = bridge.store.create_job(source_url="synthetic", output_dir="", command=[],
                configuration={"job_type": "translation"})
            bridge.store.claim_next_job("worker", 1)
            bridge.store.transition(job_id, JobStatus.STARTING, expected_worker="worker")
            bridge.store.transition(job_id, JobStatus.RUNNING, expected_worker="worker")
            now = time.time()
            bridge.store.update_fields(job_id, stage="rendering", stage_started_at=now-100,
                progress_current=99, progress_total=100, progress_counter_stage="ocr", progress_version=1,
                progress_stage_counters_json=json.dumps({"rendering": {
                    "current": 2, "total": 10, "updated_at": now-150 if stale else now,
                }}))
            with mock.patch.object(bridge, "reconcile_orphans"), \
                    mock.patch.object(ui_bridge, "_runner_still_alive", return_value=True), \
                    mock.patch.object(ui_bridge.time, "time", return_value=now):
                progress = bridge.runtime_state()["progress"]
            assert (progress["current"], progress["total"]) == (2, 10)
            assert progress["stale"] == stale
            if stale:
                assert progress["eta_seconds"] is None
            else:
                assert progress["eta_seconds"] == pytest.approx(400)
        finally:
            bridge.store.close()
