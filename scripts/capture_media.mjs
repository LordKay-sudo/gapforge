/**
 * Capture README screenshots and a short walkthrough GIF.
 * Requires BioInsight web on WEB_URL (default http://127.0.0.1:8080).
 *
 * Usage: node scripts/capture_media.mjs
 * Also captures compare + disease pages (roadmap 3.6).
 */
import { createRequire } from "module";
import { mkdir, writeFile } from "fs/promises";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const docsDir = path.join(root, "docs");
const baseUrl = process.env.WEB_URL ?? "http://127.0.0.1:8080";
const genePath = process.env.GENE_PATH ?? "/gene/ENSG00000012048";

await mkdir(docsDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

console.log("Capturing search UI...");
await page.goto(`${baseUrl}/`);
await page.waitForTimeout(800);
const searchInput = page.locator(".search-input");
await searchInput.fill("BRCA1");
await page.waitForTimeout(2000);
await page.screenshot({ path: path.join(docsDir, "screenshot-search.png"), fullPage: true });

const geneLink = page.locator(".result-link").first();
const href = await geneLink.getAttribute("href");
const geneUrl = href?.startsWith("http") ? href : `${baseUrl}${href}`;
console.log("Opening gene detail:", geneUrl);
await page.goto(geneUrl);
await page.waitForTimeout(1500);

const graphBtn = page.getByRole("button", { name: /graph/i });
if (await graphBtn.count()) {
  await graphBtn.click();
}
await page.waitForTimeout(2500);
const graphPanel = page.locator(".graph-panel, .graph-section, canvas").first();
if (await graphPanel.count()) {
  await graphPanel.screenshot({ path: path.join(docsDir, "screenshot-graph.png") });
} else {
  await page.screenshot({ path: path.join(docsDir, "screenshot-graph.png"), fullPage: false });
}

await page.screenshot({ path: path.join(docsDir, "screenshot-gene-detail.png"), fullPage: true });

console.log("Capturing compare page...");
await page.goto(`${baseUrl}/compare`);
await page.waitForTimeout(1200);
await page.screenshot({ path: path.join(docsDir, "screenshot-compare.png"), fullPage: true });

console.log("Capturing disease page...");
await page.goto(`${baseUrl}/`);
await page.waitForTimeout(400);
const diseasesTab = page.getByRole("button", { name: /Diseases/i });
if (await diseasesTab.count()) {
  await diseasesTab.click();
}
const diseaseSearch = page.getByPlaceholder(/breast|disease|search/i).first();
if (await diseaseSearch.count()) {
  await diseaseSearch.fill("breast");
  await page.waitForTimeout(1500);
  const diseaseLink = page.locator(".result-link").first();
  if (await diseaseLink.count()) {
    await diseaseLink.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(docsDir, "screenshot-disease.png"), fullPage: true });
  }
}

console.log("Capturing GIF frames...");
const framesDir = path.join(docsDir, "_gif_frames");
await mkdir(framesDir, { recursive: true });
const frames = [];

await page.goto(`${baseUrl}/`);
await page.waitForTimeout(400);
frames.push(await shot(page, path.join(framesDir, "f01.png")));

await searchInput.fill("");
await page.waitForTimeout(200);
await searchInput.fill("BRCA");
await page.waitForTimeout(300);
frames.push(await shot(page, path.join(framesDir, "f02.png")));

await searchInput.fill("BRCA1");
await page.waitForTimeout(1800);
frames.push(await shot(page, path.join(framesDir, "f03.png")));

await page.goto(geneUrl);
await page.waitForTimeout(2000);
frames.push(await shot(page, path.join(framesDir, "f04.png")));

if (await graphBtn.count()) {
  await graphBtn.click();
  await page.waitForTimeout(2800);
}
frames.push(await shot(page, path.join(framesDir, "f05.png")));

await browser.close();

const gifPath = path.join(docsDir, "demo-walkthrough.gif");
const built = await tryFfmpeg(framesDir, gifPath);
if (built) {
  console.log("GIF:", gifPath);
} else {
  console.log("ffmpeg not available — frames saved in docs/_gif_frames/");
}

console.log("Done. Screenshots in docs/");

async function shot(page, file) {
  await page.screenshot({ path: file });
  return file;
}

function tryFfmpeg(framesDir, out) {
  return new Promise((resolve) => {
    const ff = spawn(
      "ffmpeg",
      ["-y", "-framerate", "2", "-i", path.join(framesDir, "f%02d.png"), "-vf", "scale=960:-1", out],
      { stdio: "ignore" }
    );
    ff.on("error", () => resolve(false));
    ff.on("close", (code) => resolve(code === 0));
  });
}
