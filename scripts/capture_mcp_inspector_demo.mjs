/**
 * Screenshot MCP Inspector while connected to local Embabel SSE server.
 *
 *   npx @modelcontextprotocol/inspector   # in another terminal, or auto-started
 *   node scripts/capture_mcp_inspector_demo.mjs
 */
import { createRequire } from "module";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";
import fs from "fs";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "demo-recordings");
const mcpSse = process.env.MCP_SSE_URL ?? "http://127.0.0.1:1337/sse";
const inspectorPort = Number(process.env.MCP_INSPECTOR_PORT ?? "6274");

function wait(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitForUrl(url, timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return true;
    } catch {
      /* retry */
    }
    await wait(1500);
  }
  return false;
}

await mkdir(outDir, { recursive: true });

const inspector = spawn("npx", ["-y", "@modelcontextprotocol/inspector"], {
  shell: true,
  stdio: "ignore",
  detached: false,
  env: { ...process.env, CLIENT_PORT: String(inspectorPort) },
});

let inspectorReady = false;
try {
  inspectorReady = await waitForUrl(`http://127.0.0.1:${inspectorPort}`);
} catch {
  inspectorReady = false;
}

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1400, height: 900 } },
});
const page = await context.newPage();

try {
  const base = inspectorReady
    ? `http://127.0.0.1:${inspectorPort}`
    : `http://127.0.0.1:${inspectorPort}`;
  await page.goto(base, { waitUntil: "domcontentloaded", timeout: 60000 });
  await wait(2500);

  const sseField = page.locator('input[type="url"], input[placeholder*="SSE" i], input[name="url"]').first();
  if (await sseField.count()) {
    await sseField.fill(mcpSse);
    const connectBtn = page.getByRole("button", { name: /connect/i }).first();
    if (await connectBtn.count()) {
      await connectBtn.click();
      await wait(4000);
    }
  }

  await page.screenshot({
    path: path.join(outDir, "screenshot-mcp-inspector-connected.png"),
    fullPage: true,
  });
  console.log("Saved screenshot-mcp-inspector-connected.png");

  const toolBtn = page.getByText(/bioinsight_health|build_program_dossier|Tools/i).first();
  if (await toolBtn.count()) {
    await toolBtn.click().catch(() => {});
    await wait(1500);
  }

  await page.screenshot({
    path: path.join(outDir, "screenshot-mcp-inspector-tools.png"),
    fullPage: true,
  });
  console.log("Saved screenshot-mcp-inspector-tools.png");
} catch (e) {
  console.warn("Inspector capture warning:", e.message);
  await page.screenshot({
    path: path.join(outDir, "screenshot-mcp-inspector-connected.png"),
    fullPage: true,
  });
}

const video = page.video();
await context.close();
await browser.close();

if (video) {
  const src = await video.path();
  const dest = path.join(outDir, "demo-mcp-inspector.webm");
  if (src && fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log("Saved demo-mcp-inspector.webm");
  }
}

inspector.kill();
console.log(`MCP inspector assets in ${outDir}`);
