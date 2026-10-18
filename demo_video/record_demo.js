/**
 * GraphSRE: Automated Demo Video Recorder & Audio-Visual Synchronizer
 * File: demo_video/record_demo.js
 * 
 * Records a 1080p demonstration video of GraphSRE with Playwright,
 * dynamically pausing each visual act to align with the Kokoro TTS AI voiceover tracks,
 * and automatically merging the master audio track into a submission-ready MP4.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn, execSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const OUTPUT_DIR = path.join(__dirname, 'output');
const AUDIO_DIR = path.join(__dirname, 'audio');
const MASTER_AUDIO_PATH = path.join(AUDIO_DIR, 'graphsre_master_voiceover.wav');
const FINAL_MP4_PATH = path.join(__dirname, 'graphsre_demo_submission.mp4');
const FINAL_WEBM_PATH = path.join(__dirname, 'graphsre_demo_submission.webm');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// 7 Act Timeline aligned with Kokoro TTS audio durations (NARRATION_GUIDE.md)
const ACT_SCHEDULE = [
  {
    act: 0,
    id: '01_hook_and_problem',
    title: 'Act 0: The 3:00 AM Outage & Why Vector RAG Fails',
    subtitle: 'Cascading HTTP 504 Alert Storm • Why Vector RAG and Agent chat loops fail in distributed systems',
    audioDurationMs: 38950,
    audioFile: '01_hook_and_problem.wav'
  },
  {
    act: 1,
    id: '02_blackboard_architecture',
    title: 'Act 1: FalkorDB Central ACID Blackboard',
    subtitle: 'Sub-millisecond GraphBLAS queries • Unified Code AST, Dependency Topology & Telemetry',
    audioDurationMs: 35830,
    audioFile: '02_blackboard_architecture.wav'
  },
  {
    act: 2,
    id: '03_act2_chaos_and_rca',
    title: 'Act 2: Chaos Fault Injection & 5-Layer Causal Walk',
    subtitle: 'Label Propagation Clustering • Telemetry -> Service -> Endpoint -> AST Function -> Culprit Commit c3d9a107',
    audioDurationMs: 48770,
    audioFile: '03_act2_chaos_and_rca.wav'
  },
  {
    act: 3,
    id: '04_act3_quorum_and_sandbox',
    title: 'Act 3: Multi-Agent Quorum & Sub-15ms GRAPH.COPY Sandboxing',
    subtitle: 'Memory Agent HNSW vector recall (0.941) • Quorum WCS = 0.88 >= 0.75 • Counterfactual blast simulation (<8ms)',
    audioDurationMs: 47670,
    audioFile: '04_act3_quorum_and_sandbox.wav'
  },
  {
    act: 4,
    id: '05_act4_shortcut_net',
    title: 'Act 4: Closed-Loop O(1) Shortcut Net with Bayesian Dynamics',
    subtitle: 'Direct Shortcut Edge (:Service)-[:SHORTCUT_TO]->(:Function) • Repeat Outage Resolved in 0.18s (MTTR 78s -> 0.18s)',
    audioDurationMs: 43980,
    audioFile: '05_act4_shortcut_net.wav'
  },
  {
    act: 5,
    id: '06_act5_cicd_blast_gate',
    title: 'Act 5: Shift-Left CI/CD Blast Gate',
    subtitle: 'AST Call Graph Traversal & Structural Risk Index (SRI) • Blocking Regressive PRs Before Merge',
    audioDurationMs: 36200,
    audioFile: '06_act5_cicd_blast_gate.wav'
  },
  {
    act: 6,
    id: '07_conclusion_and_vision',
    title: 'Act 6: The Unfair Advantage of FalkorDB',
    subtitle: 'Sub-millisecond GraphBLAS Sparse Matrix Algebra • Zero Hallucinations • Autonomous SRE Intelligence',
    audioDurationMs: 24770,
    audioFile: '07_conclusion_and_vision.wav'
  }
];

// Helper: Locate full FFmpeg binary
function findFfmpegPath() {
  if (process.env.FFMPEG_PATH && fs.existsSync(process.env.FFMPEG_PATH)) {
    return process.env.FFMPEG_PATH;
  }

  // Look in imageio_ffmpeg folder
  const candidateDirs = [
    'C:\\Users\\acer\\miniconda3\\Lib\\site-packages\\imageio_ffmpeg\\binaries',
    path.join(process.env.USERPROFILE || '', 'miniconda3', 'Lib', 'site-packages', 'imageio_ffmpeg', 'binaries'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python310', 'Lib', 'site-packages', 'imageio_ffmpeg', 'binaries')
  ];

  for (const cDir of candidateDirs) {
    if (fs.existsSync(cDir)) {
      const files = fs.readdirSync(cDir).filter(f => f.startsWith('ffmpeg-') && f.endsWith('.exe'));
      if (files.length > 0) {
        return path.join(cDir, files[0]);
      }
    }
  }

  return 'ffmpeg';
}

// Helper: Locate Python executable
function findPythonPath() {
  if (process.env.PYTHON_PATH && fs.existsSync(process.env.PYTHON_PATH)) {
    return process.env.PYTHON_PATH;
  }
  const minicondaPy = 'C:\\Users\\acer\\miniconda3\\python.exe';
  if (fs.existsSync(minicondaPy)) {
    return minicondaPy;
  }
  return 'python';
}

// Helper: check if a port is responding with HTTP
function checkPort(port, checkPath = '/') {
  return new Promise((resolve) => {
    const req = http.get({ host: 'localhost', port, path: checkPath, timeout: 2000 }, (res) => {
      resolve(res.statusCode < 500);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Helper: wait for a port to be ready
async function waitForPort(port, name, timeoutMs = 35000) {
  const start = Date.now();
  process.stdout.write(`Waiting for ${name} on port ${port}...`);
  while (Date.now() - start < timeoutMs) {
    const ready = await checkPort(port);
    if (ready) {
      console.log(` Ready!`);
      return true;
    }
    process.stdout.write('.');
    await new Promise((r) => setTimeout(r, 1000));
  }
  console.log(` Timeout!`);
  return false;
}

// Helper: smoothly move mouse between two points
async function smoothMouseMove(page, targetX, targetY, steps = 25) {
  await page.mouse.move(targetX, targetY, { steps });
  await page.waitForTimeout(200);
}

// Helper: inject presentation overlay banner with glassmorphism and pulsing status
async function showPresenterBanner(page, actTitle, subtitle) {
  await page.evaluate(({ actTitle, subtitle }) => {
    let banner = document.getElementById('graphsre-demo-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'graphsre-demo-banner';
      banner.style.position = 'fixed';
      banner.style.bottom = '24px';
      banner.style.left = '50%';
      banner.style.transform = 'translateX(-50%)';
      banner.style.background = 'rgba(15, 23, 42, 0.94)';
      banner.style.backdropFilter = 'blur(16px)';
      banner.style.border = '1px solid rgba(59, 130, 246, 0.45)';
      banner.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(59, 130, 246, 0.25)';
      banner.style.borderRadius = '14px';
      banner.style.padding = '12px 28px';
      banner.style.zIndex = '999999';
      banner.style.display = 'flex';
      banner.style.alignItems = 'center';
      banner.style.gap = '16px';
      banner.style.fontFamily = 'system-ui, -apple-system, sans-serif';
      banner.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
      document.body.appendChild(banner);
    }
    banner.innerHTML = `
      <div style="width: 12px; height: 12px; border-radius: 50%; background: #10B981; box-shadow: 0 0 14px #10B981; animation: pulse 1.5s infinite;"></div>
      <div>
        <div style="font-size: 13px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.6px; text-transform: uppercase;">${actTitle}</div>
        <div style="font-size: 12px; color: #94A3B8; margin-top: 3px; font-weight: 500;">${subtitle}</div>
      </div>
    `;
  }, { actTitle, subtitle });
}

async function runAutomation() {
  console.log('===============================================================');
  console.log('   GraphSRE: Automated Demo Video Recorder & Audio Synchronizer');
  console.log('===============================================================\n');

  // 1. Check/Start Backend
  let backendReady = await checkPort(8000, '/docs');
  let backendProc = null;
  if (!backendReady) {
    const pyBin = findPythonPath();
    console.log(`Starting FastAPI backend with ${pyBin} on port 8000...`);
    backendProc = spawn(pyBin, ['-m', 'uvicorn', 'backend.main:app', '--port', '8000'], {
      cwd: REPO_ROOT,
      shell: true,
      stdio: 'ignore'
    });
    backendReady = await waitForPort(8000, 'Backend API');
  } else {
    console.log('✓ FastAPI backend active on port 8000.');
  }

  // 2. Check/Start Frontend
  let frontendReady = await checkPort(3001, '/');
  let frontendProc = null;
  if (!frontendReady) {
    console.log('Starting Next.js frontend server on port 3001...');
    const nextBin = path.join(REPO_ROOT, 'frontend', 'node_modules', '.bin', 'next.cmd');
    frontendProc = spawn(nextBin, ['start', '-p', '3001'], {
      cwd: path.join(REPO_ROOT, 'frontend'),
      shell: true
    });
    frontendReady = await waitForPort(3001, 'Next.js Frontend', 35000);
  } else {
    console.log('✓ Next.js frontend active on port 3001.');
  }

  // 3. Launch Playwright Chrome with 1080p Video Recording
  const isHeadless = process.env.HEADLESS !== 'false';
  console.log(`\nLaunching Google Chrome (${isHeadless ? 'Headless' : 'Visible'}) with 1080p video recording...`);
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: isHeadless,
    args: ['--start-maximized', '--no-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  try {
    // =========================================================================
    // ACT 0: The 3:00 AM Outage & Why Vector RAG Fails (Target: 38.95s)
    // =========================================================================
    const act0 = ACT_SCHEDULE[0];
    const act0Start = Date.now();
    console.log(`\n▶ [00:00] ${act0.title} (Duration: ${act0.audioDurationMs / 1000}s)...`);

    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    await showPresenterBanner(page, act0.title, act0.subtitle);

    // Pan across system status indicators & healthy service badges
    await smoothMouseMove(page, 220, 110, 30);
    await page.waitForTimeout(2500);
    await smoothMouseMove(page, 620, 110, 30);
    await page.waitForTimeout(2500);
    await smoothMouseMove(page, 1020, 110, 30);
    await page.waitForTimeout(2500);

    // Pan across healthy microservice nodes in Cytoscape canvas
    await smoothMouseMove(page, 520, 340, 35);
    await page.waitForTimeout(3000);
    await smoothMouseMove(page, 720, 380, 35);
    await page.waitForTimeout(3000);

    // Hover over top metrics
    await smoothMouseMove(page, 1420, 110, 30);
    await page.waitForTimeout(2500);

    // Precise padding to match Act 0 audio duration
    const act0Elapsed = Date.now() - act0Start;
    const act0Remain = act0.audioDurationMs - act0Elapsed;
    if (act0Remain > 0) {
      console.log(`  Act 0 action elapsed: ${(act0Elapsed/1000).toFixed(1)}s, padding ${(act0Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act0Remain);
    }

    // =========================================================================
    // ACT 1: FalkorDB Central ACID Blackboard & Cypher Console (Target: 35.83s)
    // =========================================================================
    const act1 = ACT_SCHEDULE[1];
    const act1Start = Date.now();
    console.log(`\n▶ [${(act0.audioDurationMs/1000).toFixed(0)}s] ${act1.title} (Duration: ${act1.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act1.title, act1.subtitle);

    // Scroll smoothly to Cypher Console at bottom
    await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' }));
    await page.waitForTimeout(2000);

    // Mouse over live OpenCypher & GraphBLAS Execution Stream badges
    await smoothMouseMove(page, 800, 750, 30);
    await page.waitForTimeout(3000);
    await smoothMouseMove(page, 950, 790, 30);
    await page.waitForTimeout(3000);
    await smoothMouseMove(page, 1100, 830, 30);
    await page.waitForTimeout(3000);

    // Scroll back to Cytoscape topology canvas
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(2000);
    await smoothMouseMove(page, 640, 360, 30);
    await page.waitForTimeout(2500);

    // Precise padding to match Act 1 audio duration
    const act1Elapsed = Date.now() - act1Start;
    const act1Remain = act1.audioDurationMs - act1Elapsed;
    if (act1Remain > 0) {
      console.log(`  Act 1 action elapsed: ${(act1Elapsed/1000).toFixed(1)}s, padding ${(act1Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act1Remain);
    }

    // =========================================================================
    // ACT 2: Chaos Fault Injection & 5-Layer Causal Walk (Target: 48.77s)
    // =========================================================================
    const act2 = ACT_SCHEDULE[2];
    const act2Start = Date.now();
    console.log(`\n▶ ${act2.title} (Duration: ${act2.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act2.title, act2.subtitle);

    // Scroll down to Chaos Panel
    await page.evaluate(() => window.scrollBy({ top: 400, behavior: 'smooth' }));
    await page.waitForTimeout(1500);

    const chaosButton = page.locator('button:has-text("Inject Chaos Fault")');
    if (await chaosButton.isVisible()) {
      await smoothMouseMove(page, 950, 680, 25);
      console.log('  Triggering [Inject Chaos Fault] button...');
      await chaosButton.click();
      await page.waitForTimeout(1500);
    }

    // Scroll back to main canvas to observe fault propagation
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(2000);

    // Hover over alerted PaymentService node (turns red)
    await smoothMouseMove(page, 640, 350, 35);
    await page.waitForTimeout(3500);

    // Hover over the Agent Feed on the right panel as RCA Agent performs 5-layer walk
    await smoothMouseMove(page, 1380, 240, 30);
    await page.waitForTimeout(3000);
    await smoothMouseMove(page, 1380, 380, 30);
    await page.waitForTimeout(3000);

    // Click canvas node to inspect culprit commit c3d9a107 metadata
    await page.mouse.click(640, 350);
    await page.waitForTimeout(3500);
    // Dismiss inspector
    await page.mouse.click(200, 250);
    await page.waitForTimeout(1500);

    // Precise padding to match Act 2 audio duration
    const act2Elapsed = Date.now() - act2Start;
    const act2Remain = act2.audioDurationMs - act2Elapsed;
    if (act2Remain > 0) {
      console.log(`  Act 2 action elapsed: ${(act2Elapsed/1000).toFixed(1)}s, padding ${(act2Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act2Remain);
    }

    // =========================================================================
    // ACT 3: Multi-Agent Quorum & Sub-15ms GRAPH.COPY Sandboxing (Target: 47.67s)
    // =========================================================================
    const act3 = ACT_SCHEDULE[3];
    const act3Start = Date.now();
    console.log(`\n▶ ${act3.title} (Duration: ${act3.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act3.title, act3.subtitle);

    // Focus on Quorum Consensus Meter (WCS = 0.88 >= 0.75)
    await smoothMouseMove(page, 1400, 110, 30);
    await page.waitForTimeout(3000);

    // Scroll to Action Card
    await page.evaluate(() => window.scrollBy({ top: 320, behavior: 'smooth' }));
    await page.waitForTimeout(1500);

    // Hover and click Fork Sandbox Sim (GRAPH.COPY)
    const simButton = page.locator('button:has-text("Fork Sandbox Sim")');
    if (await simButton.isVisible()) {
      const box = await simButton.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        console.log('  Clicking [Fork Sandbox Sim] (GRAPH.COPY simulation)...');
        await simButton.click();
        await page.waitForTimeout(3000);
      }
    }

    // Hover and click 1-Click Approve Canary Revert
    const revertButton = page.locator('button:has-text("1-Click Approve Canary Revert")');
    if (await revertButton.isVisible()) {
      const box = await revertButton.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        console.log('  Clicking [1-Click Approve Canary Revert]...');
        await revertButton.click();
        await page.waitForTimeout(3000);
      }
    }

    // Scroll back to canvas to observe healthy emerald green restoration
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(2000);
    await smoothMouseMove(page, 640, 350, 30);
    await page.waitForTimeout(3000);

    // Precise padding to match Act 3 audio duration
    const act3Elapsed = Date.now() - act3Start;
    const act3Remain = act3.audioDurationMs - act3Elapsed;
    if (act3Remain > 0) {
      console.log(`  Act 3 action elapsed: ${(act3Elapsed/1000).toFixed(1)}s, padding ${(act3Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act3Remain);
    }

    // =========================================================================
    // ACT 4: Closed-Loop O(1) Shortcut Net with Bayesian Dynamics (Target: 43.98s)
    // =========================================================================
    const act4 = ACT_SCHEDULE[4];
    const act4Start = Date.now();
    console.log(`\n▶ ${act4.title} (Duration: ${act4.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act4.title, act4.subtitle);

    // Highlight radiant emerald shortcut edge on canvas
    await smoothMouseMove(page, 700, 380, 30);
    await page.waitForTimeout(3000);

    // Scroll to Shortcut Visualizer card
    await page.evaluate(() => window.scrollBy({ top: 350, behavior: 'smooth' }));
    await page.waitForTimeout(1500);

    const repeatShortcutBtn = page.locator('button:has-text("Test Repeat Outage")');
    if (await repeatShortcutBtn.isVisible()) {
      const box = await repeatShortcutBtn.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        console.log('  Triggering [Test Repeat Outage (O(1) Shortcut)] button...');
        await repeatShortcutBtn.click();
        await page.waitForTimeout(3500);
      }
    }

    // Mouse over Bayesian Dynamics indicators (30-day half-life, -70% invalidation)
    await smoothMouseMove(page, 300, 680, 25);
    await page.waitForTimeout(3000);
    await smoothMouseMove(page, 450, 680, 25);
    await page.waitForTimeout(3000);

    // Precise padding to match Act 4 audio duration
    const act4Elapsed = Date.now() - act4Start;
    const act4Remain = act4.audioDurationMs - act4Elapsed;
    if (act4Remain > 0) {
      console.log(`  Act 4 action elapsed: ${(act4Elapsed/1000).toFixed(1)}s, padding ${(act4Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act4Remain);
    }

    // =========================================================================
    // ACT 5: Shift-Left CI/CD Blast Gate (Target: 36.20s)
    // =========================================================================
    const act5 = ACT_SCHEDULE[5];
    const act5Start = Date.now();
    console.log(`\n▶ ${act5.title} (Duration: ${act5.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act5.title, act5.subtitle);

    // Navigate to CI/CD Blast Gate
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(1000);

    const blastGateLink = page.locator('header a[href="/cicd-blast-gate"]');
    if (await blastGateLink.isVisible()) {
      const box = await blastGateLink.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 20);
        await blastGateLink.click();
      }
    } else {
      await page.goto('http://localhost:3001/cicd-blast-gate', { waitUntil: 'networkidle' });
    }
    await page.waitForTimeout(2000);

    // Evaluate Unsafe PR #412 (timeout=None)
    const evalBtn = page.locator('button:has-text("Evaluate PR Blast Gate")');
    if (await evalBtn.isVisible()) {
      const box = await evalBtn.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        console.log('  Evaluating Unsafe PR #412...');
        await evalBtn.click();
        await page.waitForTimeout(2500);
      }
    }

    // Switch tab to Safe PR #413 (circuit breaker)
    const pr413Tab = page.locator('button:has-text("PR #413")');
    if (await pr413Tab.isVisible()) {
      const box = await pr413Tab.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 20);
        console.log('  Switching to Safe PR #413...');
        await pr413Tab.click();
        await page.waitForTimeout(1500);
      }
    }

    // Evaluate Safe PR #413
    if (await evalBtn.isVisible()) {
      const box = await evalBtn.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 20);
        console.log('  Evaluating Safe PR #413...');
        await evalBtn.click();
        await page.waitForTimeout(2500);
      }
    }

    // Scroll through PR Structural Risk Index & Cytoscape blast subgraph
    await page.evaluate(() => window.scrollBy({ top: 280, behavior: 'smooth' }));
    await page.waitForTimeout(2500);

    // Precise padding to match Act 5 audio duration
    const act5Elapsed = Date.now() - act5Start;
    const act5Remain = act5.audioDurationMs - act5Elapsed;
    if (act5Remain > 0) {
      console.log(`  Act 5 action elapsed: ${(act5Elapsed/1000).toFixed(1)}s, padding ${(act5Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act5Remain);
    }

    // =========================================================================
    // ACT 6: The Unfair Advantage of FalkorDB & Conclusion (Target: 24.77s)
    // =========================================================================
    const act6 = ACT_SCHEDULE[6];
    const act6Start = Date.now();
    console.log(`\n▶ ${act6.title} (Duration: ${act6.audioDurationMs / 1000}s)...`);

    await showPresenterBanner(page, act6.title, act6.subtitle);

    // Navigate back to War Room for clean finale
    const warRoomLink = page.locator('header nav a[href="/"]');
    if (await warRoomLink.isVisible()) {
      const box = await warRoomLink.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 20);
        await warRoomLink.click();
      }
    } else {
      await page.goto('http://localhost:3001/', { waitUntil: 'networkidle' });
    }
    await page.waitForTimeout(2000);

    // Smooth final pan over healthy topology and docked Cypher console
    await smoothMouseMove(page, 960, 540, 40);
    await page.waitForTimeout(3000);
    await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' }));
    await page.waitForTimeout(3000);

    // Precise padding to match Act 6 audio duration
    const act6Elapsed = Date.now() - act6Start;
    const act6Remain = act6.audioDurationMs - act6Elapsed;
    if (act6Remain > 0) {
      console.log(`  Act 6 action elapsed: ${(act6Elapsed/1000).toFixed(1)}s, padding ${(act6Remain/1000).toFixed(1)}s to sync`);
      await page.waitForTimeout(act6Remain);
    }

    console.log('\n✓ All 7 visual acts completed with synchronized narration durations!');

  } catch (err) {
    console.error('Error during recording execution:', err);
  } finally {
    // 4. Finalize Video Recording
    console.log('\nFinalizing raw Playwright video recording...');
    const video = page.video();
    await page.close();
    await context.close();
    await browser.close();

    if (backendProc && backendProc.pid) {
      try { process.kill(backendProc.pid); } catch (e) {}
    }
    if (frontendProc && frontendProc.pid) {
      try { process.kill(frontendProc.pid); } catch (e) {}
    }

    if (video) {
      const rawVideoPath = await video.path();
      console.log(`✓ Raw video captured at: ${rawVideoPath}`);

      // Check if master voiceover audio exists
      if (fs.existsSync(MASTER_AUDIO_PATH)) {
        console.log(`✓ Master audio voiceover detected: ${MASTER_AUDIO_PATH}`);
        const ffmpegBin = findFfmpegPath();
        console.log(`Using FFmpeg binary: ${ffmpegBin}`);

        try {
          console.log('\n=== Merging Audio & Video with FFmpeg ===');
          // 1. Generate High-Quality MP4 (H.264 / AAC)
          console.log('Encoding final submission MP4 (H.264 / AAC 1080p)...');
          const mp4Cmd = `"${ffmpegBin}" -y -i "${rawVideoPath}" -i "${MASTER_AUDIO_PATH}" -c:v libx264 -pix_fmt yuv420p -preset fast -crf 20 -c:a aac -b:a 192k -shortest "${FINAL_MP4_PATH}"`;
          execSync(mp4Cmd, { stdio: 'inherit' });
          console.log(`🎉 SUCCESS! Official MP4 Video Created:`);
          console.log(`👉 ${FINAL_MP4_PATH}`);

          // 2. Also Generate WebM (VP9 / Opus)
          console.log('Encoding final submission WebM (VP9 / Opus 1080p)...');
          const webmCmd = `"${ffmpegBin}" -y -i "${rawVideoPath}" -i "${MASTER_AUDIO_PATH}" -c:v libvpx-vp9 -b:v 2500k -c:a libopus -b:a 128k -shortest "${FINAL_WEBM_PATH}"`;
          execSync(webmCmd, { stdio: 'inherit' });
          console.log(`🎉 SUCCESS! Official WebM Video Created:`);
          console.log(`👉 ${FINAL_WEBM_PATH}`);
        } catch (ffmpegErr) {
          console.warn('FFmpeg merge encountered an error:', ffmpegErr.message);
          console.log('Falling back to raw video copy...');
          fs.copyFileSync(rawVideoPath, FINAL_WEBM_PATH);
        }
      } else {
        console.log(`Note: Master voiceover not found at ${MASTER_AUDIO_PATH}. Copying raw video.`);
        fs.copyFileSync(rawVideoPath, FINAL_WEBM_PATH);
      }
    }
  }
}

runAutomation();
