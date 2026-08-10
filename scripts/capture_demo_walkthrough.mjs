/**
 * Record a short WebM walkthrough of GapForge review + OntoHarness Swagger.
 * Convert to GIF locally: ffmpeg -i demo-walkthrough.webm -vf "fps=10,scale=1280:-1" demo-walkthrough.gif
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
const ontoUrl = process.env.ONTO_URL ?? "http://127.0.0.1:8010/docs";

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1400, height: 900 } },
});
const page = await context.newPage();

try {
  await page.goto(ontoUrl, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1200);
  await page.screenshot({
    path: path.join(outDir, "screenshot-ontoharness-api-v0.5.png"),
    fullPage: true,
  });
  console.log("Saved screenshot-ontoharness-api-v0.5.png");

  await page.goto(`${webUrl}/gaps/review`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.getByText("gap-flurizan-efficacy").first().click();
  await page.waitForTimeout(2000);
  await page.evaluate(() => window.scrollBy(0, 420));
  await page.waitForTimeout(1500);
  await page.getByText("gap-flurizan-endpoint").first().click();
  await page.waitForTimeout(2000);
} catch (e) {
  console.warn("Walkthrough capture warning:", e.message);
}

const video = page.video();
await context.close();
await browser.close();

if (video) {
  const src = await video.path();
  const dest = path.join(outDir, "demo-walkthrough.webm");
  if (src && fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log("Saved demo-walkthrough.webm");
  }
}

console.log(`Assets in ${outDir}`);
