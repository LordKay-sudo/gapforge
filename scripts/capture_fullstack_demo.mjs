/**
 * Capture full-stack demo (GapForge API + MCP + review UI + OntoHarness).
 *
 * Prerequisites:
 *   docker compose -f docker-compose.full.yml up --build
 *
 * Usage:
 *   node scripts/capture_fullstack_demo.mjs
 */
import { createRequire } from "module";
import { mkdir } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");
const fs = require("fs");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "demo-recordings");
const webUrl = process.env.WEB_URL ?? "http://127.0.0.1:8080";
const apiDocs = process.env.API_DOCS_URL ?? "http://127.0.0.1:8000/docs";
const mcpHealth = process.env.MCP_HEALTH_URL ?? "http://127.0.0.1:1337/actuator/health";
const ontoUrl = process.env.ONTO_URL ?? "http://127.0.0.1:8010/docs";
const programUrl = `${webUrl}/program/prog-flurizan-ad`;

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1400, height: 900 } },
});
const page = await context.newPage();

async function shot(name) {
  await page.screenshot({ path: path.join(outDir, name), fullPage: true });
  console.log(`Saved ${name}`);
}

try {
  await page.goto(apiDocs, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shot("screenshot-gapforge-api-docs.png");

  await page.goto(mcpHealth, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1200);
  await shot("screenshot-mcp-health.png");

  await page.goto(ontoUrl, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1200);

  await page.goto(programUrl, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shot("screenshot-program-detail.png");

  await page.goto(`${webUrl}/gaps/review`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
  for (const gapId of ["gap-flurizan-efficacy", "gap-flurizan-cq-demo", "gap-flurizan-endpoint"]) {
    const card = page.locator("article.gap-card").filter({ hasText: gapId });
    if (await card.count()) {
      await card.scrollIntoViewIfNeeded();
      await page.waitForTimeout(1800);
    }
  }
} catch (e) {
  console.warn("Full-stack capture warning:", e.message);
}

const video = page.video();
await context.close();
await browser.close();

if (video) {
  const src = await video.path();
  const dest = path.join(outDir, "demo-fullstack-walkthrough.webm");
  if (src && fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log("Saved demo-fullstack-walkthrough.webm");
  }
}

console.log(`Full-stack assets in ${outDir}`);
