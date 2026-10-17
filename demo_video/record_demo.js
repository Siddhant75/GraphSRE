const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const OUTPUT_DIR = path.join(__dirname, 'output');
const FINAL_VIDEO_PATH = path.join(__dirname, 'graphsre_demo_submission.webm');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Helper: check if a port is responding with HTTP
function checkPort(port, path = '/') {
  return new Promise((resolve) => {
    const req = http.get({ host: 'localhost', port, path, timeout: 2000 }, (res) => {
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
async function waitForPort(port, name, timeoutMs = 30000) {
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
async function smoothMouseMove(page, targetX, targetY, steps = 20) {
  await page.mouse.move(targetX, targetY, { steps });
  await page.waitForTimeout(300);
}

// Helper: inject presentation overlay banner
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
      banner.style.background = 'rgba(15, 23, 42, 0.92)';
      banner.style.backdropFilter = 'blur(12px)';
      banner.style.border = '1px solid rgba(59, 130, 246, 0.4)';
      banner.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(59, 130, 246, 0.2)';
      banner.style.borderRadius = '14px';
      banner.style.padding = '12px 24px';
      banner.style.zIndex = '999999';
      banner.style.display = 'flex';
      banner.style.alignItems = 'center';
      banner.style.gap = '14px';
      banner.style.fontFamily = 'system-ui, -apple-system, sans-serif';
      banner.style.transition = 'all 0.4s ease';
      document.body.appendChild(banner);
    }
    banner.innerHTML = `
      <div style="width: 10px; height: 10px; border-radius: 50%; background: #10B981; box-shadow: 0 0 12px #10B981; animation: pulse 1.5s infinite;"></div>
      <div>
        <div style="font-size: 13px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px; text-transform: uppercase;">${actTitle}</div>
        <div style="font-size: 12px; color: #94A3B8; margin-top: 2px;">${subtitle}</div>
      </div>
    `;
  }, { actTitle, subtitle });
}

async function runAutomation() {
  console.log('=== GraphSRE Automated Demo Video Recorder ===\n');

  // 1. Check/Start Backend
  let backendReady = await checkPort(8000, '/docs');
  let backendProc = null;
  if (!backendReady) {
    console.log('Starting FastAPI backend server...');
    backendProc = spawn('python', ['-m', 'uvicorn', 'backend.main:app', '--port', '8000'], {
      cwd: REPO_ROOT,
      detached: true,
      stdio: 'ignore'
    });
    backendReady = await waitForPort(8000, 'Backend API');
  } else {
    console.log('FastAPI backend already active on port 8000.');
  }

  // 2. Check/Start Frontend
  let frontendReady = await checkPort(3001, '/');
  let frontendProc = null;
  if (!frontendReady) {
    console.log('Starting Next.js frontend server on port 3001...');
    frontendProc = spawn('pnpm', ['dev'], {
      cwd: path.join(REPO_ROOT, 'frontend'),
      detached: true,
      stdio: 'ignore',
      shell: true
    });
    frontendReady = await waitForPort(3001, 'Next.js Frontend');
  } else {
    console.log('Next.js frontend already active on port 3001.');
  }

  // 3. Launch Playwright with Chrome & 1080p Video Recording
  const isHeadless = process.env.HEADLESS === 'true';
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
    // ==========================================
    // ACT 1: The Outage Alert Storm (00:00 - 00:40)
    // ==========================================
    console.log('▶ Starting Act 1: The Outage Alert Storm...');
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    await showPresenterBanner(
      page,
      'Act 1: Outage Ingestion & CDLP Clustering',
      'Cascading HTTP 504 alert storm clustered via FalkorDB Label Propagation into SEV-1'
    );

    // Pan across top status metrics
    await smoothMouseMove(page, 200, 100, 30);
    await page.waitForTimeout(1000);
    await smoothMouseMove(page, 600, 100, 30);
    await page.waitForTimeout(1000);
    await smoothMouseMove(page, 1000, 100, 30);
    await page.waitForTimeout(1500);

    // Inspect Cytoscape Topology Canvas
    await smoothMouseMove(page, 500, 350, 40);
    await page.waitForTimeout(2000);

    // Scroll down to Chaos Panel and trigger fault injection
    await page.evaluate(() => window.scrollBy({ top: 400, behavior: 'smooth' }));
    await page.waitForTimeout(1500);

    const chaosButton = page.locator('button:has-text("Inject Chaos Fault")');
    if (await chaosButton.isVisible()) {
      await smoothMouseMove(page, 950, 680, 25);
      await chaosButton.click();
      await page.waitForTimeout(2500);
    }

    // Scroll back to main canvas
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(2000);

    // ==========================================
    // ACT 2: Multi-Hop RCA & Quorum Consensus (00:40 - 01:25)
    // ==========================================
    console.log('▶ Starting Act 2: Multi-Hop RCA & Quorum Consensus...');
    await showPresenterBanner(
      page,
      'Act 2: Cross-Layer RCA & Quorum Consensus',
      'Traversing Telemetry -> Service -> Endpoint -> Tree-sitter AST -> Culprit Commit c3d9a107'
    );

    // Hover over Agent Feed
    await smoothMouseMove(page, 1350, 250, 30);
    await page.waitForTimeout(2000);
    await smoothMouseMove(page, 1350, 400, 25);
    await page.waitForTimeout(2000);

    // Focus on Quorum Consensus Meter
    await smoothMouseMove(page, 1400, 100, 30);
    await page.waitForTimeout(2500);

    // Click on Cytoscape canvas center to trigger Node Inspector
    await smoothMouseMove(page, 650, 350, 35);
    await page.mouse.click(650, 350);
    await page.waitForTimeout(3000);

    // Dismiss inspector by clicking canvas background
    await page.mouse.click(200, 250);
    await page.waitForTimeout(1500);

    // ==========================================
    // ACT 3: Ephemeral Sandbox & O(1) Shortcut Net (01:25 - 02:10)
    // ==========================================
    console.log('▶ Starting Act 3: Ephemeral Sandbox & O(1) Shortcut Net...');
    await showPresenterBanner(
      page,
      'Act 3: Ephemeral Sandboxing (GRAPH.COPY) & Canary Rollback',
      'Counterfactual blast radius simulation (<10ms) & Synthesizing O(1) Shortcut Edge'
    );

    await page.evaluate(() => window.scrollBy({ top: 320, behavior: 'smooth' }));
    await page.waitForTimeout(1500);

    // Hover and click Fork Sandbox Sim
    const simButton = page.locator('button:has-text("Fork Sandbox Sim")');
    if (await simButton.isVisible()) {
      const box = await simButton.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        await simButton.click();
        await page.waitForTimeout(2000);
      }
    }

    // Click 1-Click Approve Canary Revert
    const revertButton = page.locator('button:has-text("1-Click Approve Canary Revert")');
    if (await revertButton.isVisible()) {
      const box = await revertButton.boundingBox();
      if (box) {
        await smoothMouseMove(page, box.x + box.width / 2, box.y + box.height / 2, 25);
        await revertButton.click();
        await page.waitForTimeout(2500);
      }
    }

    // Hover over Shortcut Visualizer card
    await smoothMouseMove(page, 1350, 600, 30);
    await page.waitForTimeout(3000);

    // ==========================================
    // ACT 4: Shift-Left CI/CD Blast Gate (02:10 - 02:50)
    // ==========================================
    console.log('▶ Starting Act 4: Shift-Left CI/CD Blast Gate...');
    await showPresenterBanner(
      page,
      'Act 4: Shift-Left CI/CD Blast Gate',
      'Tree-sitter PR diff evaluation blocking regressive merge via Structural Risk Index (SRI >= 0.70)'
    );

    // Navigate to CI/CD Blast Gate
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await page.waitForTimeout(1000);

    const blastGateLink = page.locator('a:has-text("CI/CD Blast Gate")');
    await blastGateLink.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Scroll through PR analysis
    await smoothMouseMove(page, 800, 300, 30);
    await page.waitForTimeout(2000);
    await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' }));
    await page.waitForTimeout(2500);

    // Navigate to Vector Memory & Postmortems
    await showPresenterBanner(
      page,
      'Episodic Vector Memory & Knowledge Graph',
      'FalkorDB embedded 384-dim HNSW vector search linking past incident postmortems'
    );

    const postmortemsLink = page.locator('a:has-text("Vector Memory & Postmortems")');
    await postmortemsLink.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Return to War Room for clean finale
    await showPresenterBanner(
      page,
      'GraphSRE: Autonomous SRE & Code Brain',
      'Sub-millisecond GraphBLAS • Zero Hallucinations • Powered by FalkorDB'
    );

    const warRoomLink = page.locator('a:has-text("War Room")');
    await warRoomLink.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3500);

  } catch (err) {
    console.error('Error during recording execution:', err);
  } finally {
    // 4. Finalize Video Recording
    console.log('\nFinalizing video recording...');
    const video = page.video();
    await page.close();
    await context.close();
    await browser.close();

    if (video) {
      const videoPath = await video.path();
      console.log(`Raw video saved at: ${videoPath}`);
      try {
        fs.copyFileSync(videoPath, FINAL_VIDEO_PATH);
        console.log(`\n🎉 SUCCESS! Official demo video created at:\n👉 ${FINAL_VIDEO_PATH}`);
      } catch (e) {
        console.log(`Video available at: ${videoPath}`);
      }
    }
  }
}

runAutomation();
