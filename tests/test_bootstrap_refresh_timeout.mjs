import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../static/komyst_ui.js', import.meta.url), 'utf8');
const start = source.indexOf('  async function runBootstrapRefresh() {');
const end = source.indexOf('  async function pollState()', start);
assert.ok(start >= 0 && end > start);
const implementation = source.slice(start, end);

for (const alreadyBooted of [true, false]) {
  const status = {textContent: 'conectado', dataset: {state: 'ok'}};
  const html = {dataset: {shellState: 'authenticated'}};
  const events = [];
  const context = vm.createContext({
    appState: {authGeneration: 3, cursor: 1, active: {id: 'running-job'}},
    bootHasClosed: alreadyBooted, bootTimer: 1,
    api: async () => { throw Object.assign(new Error('serviço demorou'), {code: 'timeout'}); },
    setBootStage: () => {}, window: {clearTimeout: () => {}},
    $: selector => selector === '#appStatus' ? status : null,
    setBootFailed: () => { html.dataset.shellState = 'boot_failed'; events.push('failed'); },
    showToast: () => { events.push('toast'); },
  });
  await vm.runInContext(implementation + '\nrunBootstrapRefresh()', context);
  assert.equal(context.appState.active.id, 'running-job');
  if (alreadyBooted) {
    assert.equal(html.dataset.shellState, 'authenticated');
    assert.equal(status.textContent, 'reconectando');
    assert.equal(status.dataset.state, 'warning');
    assert.deepEqual(events, ['toast']);
  } else {
    assert.equal(html.dataset.shellState, 'boot_failed');
    assert.deepEqual(events, ['failed', 'toast']);
  }
}
console.log('Bootstrap timeout: existing panel preserved; initial startup failure remains visible.');
