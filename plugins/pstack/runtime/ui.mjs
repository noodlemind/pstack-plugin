import { chromium } from 'playwright';
import { createInterface } from 'node:readline';
import { createHash } from 'node:crypto';
import { appendFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

let browser, context, page, artifacts, snapshot, cdp;
let counter = 0;
let attached = false;
async function observe() {
  const tree = await page.locator('body').ariaSnapshot();
  snapshot = createHash('sha256').update(page.url() + tree).digest('hex');
  const screenshot = join(artifacts, `snapshot-${++counter}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  return { url: page.url(), title: await page.title(), tree, digest: snapshot, screenshot };
}
for await (const line of createInterface({ input: process.stdin })) {
  try {
    const a = JSON.parse(line);
    let result;
    if (a.action === 'start') {
      artifacts = a.artifact_dir;
      if (a.cdp_url) {
        attached = true;
        browser = await chromium.connectOverCDP(a.cdp_url);
        const pages = browser.contexts().flatMap(c => c.pages());
        const matches = [];
        for (const p of pages) if (a.marker && await p.locator(a.marker).count()) matches.push(p);
        if (matches.length !== 1) throw new Error('CDP attachment requires one positive marker match');
        page = matches[0];
        context = page.context();
      } else {
        browser = await chromium.launch({ channel: 'chrome', headless: a.headless ?? true });
        context = await browser.newContext(a.record_video ? { recordVideo: { dir: artifacts } } : {});
        page = await context.newPage();
        await page.goto(a.url);
      }
      cdp = await context.newCDPSession(page);
      await context.tracing.start({ screenshots: true, snapshots: true });
      result = await observe();
    } else if (a.action === 'snapshot') result = await observe();
    else if (['click', 'fill', 'press', 'navigate', 'resize'].includes(a.action)) {
      if (!a.after_snapshot || a.after_snapshot !== snapshot) throw new Error('Fresh snapshot digest required before a structural action');
      const currentTree = await page.locator('body').ariaSnapshot();
      const currentDigest = createHash('sha256').update(page.url() + currentTree).digest('hex');
      if (currentDigest !== snapshot) throw new Error('Page changed since snapshot; observe again before acting');
      if (a.action === 'navigate') await page.goto(a.url);
      if (a.action === 'resize') await page.setViewportSize({ width: a.width, height: a.height });
      if (a.action === 'click') await page.locator(a.selector).click();
      if (a.action === 'fill') await page.locator(a.selector).fill(a.text);
      if (a.action === 'press') await page.locator(a.selector).press(a.key);
      result = await observe();
    } else if (a.action === 'inspect') {
      const values = await page.locator(a.selector).evaluateAll(nodes => nodes.map(n => ({ text: n.textContent, value: n.value, checked: n.checked, visible: !!(n.offsetWidth || n.offsetHeight) })));
      result = { values };
    } else if (a.action === 'profile-start') {
      await cdp.send('Profiler.enable'); await cdp.send('Profiler.start'); result = { state: 'profiling' };
    } else if (a.action === 'profile-stop') {
      const profile = await cdp.send('Profiler.stop'); const path = join(artifacts, 'cpu.cpuprofile'); writeFileSync(path, JSON.stringify(profile.profile)); result = { path };
    } else if (a.action === 'heap') {
      const path = join(artifacts, 'heap.heapsnapshot'); writeFileSync(path, '');
      const listener = e => appendFileSync(path, e.chunk);
      cdp.on('HeapProfiler.addHeapSnapshotChunk', listener);
      await cdp.send('HeapProfiler.takeHeapSnapshot'); cdp.off('HeapProfiler.addHeapSnapshotChunk', listener); result = { path };
    } else if (a.action === 'stop') {
      const trace = join(artifacts, 'trace.zip'); await context.tracing.stop({ path: trace });
      const video = attached ? null : await page.video()?.path();
      if (!attached) await context.close();
      await browser.close(); result = { state: 'stopped', trace, video };
    } else throw new Error('Unknown browser action');
    appendFileSync(join(artifacts, 'actions.jsonl'), JSON.stringify({ time: new Date().toISOString(), action: a.action, result }) + '\n');
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch (e) { process.stdout.write(JSON.stringify({ error: String(e.message) }) + '\n'); }
}
if (browser?.isConnected()) await browser.close();
