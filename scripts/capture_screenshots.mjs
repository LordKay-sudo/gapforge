/**
 * Capture README screenshots. Requires: npm run dev (web) on :5173 or :5174
 * Usage: node scripts/capture_screenshots.mjs
 */
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");
import { mkdir } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const docsDir = path.join(root, "docs");
const baseUrl = process.env.WEB_URL ?? "http://127.0.0.1:5174";

await mkdir(docsDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

await page.goto(`${baseUrl}/`);
await page.waitForTimeout(500);
await page.getByPlaceholder(/BRCA1/i).fill("BRCA1");
await page.waitForTimeout(800);
await page.screenshot({ path: path.join(docsDir, "screenshot-search.png"), fullPage: true });

await page.goto(`${baseUrl}/gene/ENSG00000012048`);
await page.waitForSelector(".graph-panel canvas", { timeout: 10000 }).catch(() => {});
await page.waitForTimeout(1500);
await page.locator(".graph-section").screenshot({
  path: path.join(docsDir, "screenshot-graph.png"),
});
await page.screenshot({
  path: path.join(docsDir, "screenshot-gene-detail.png"),
  fullPage: true,
});

await page.goto(`${baseUrl}/compare`);
await page.waitForTimeout(800);
await page.screenshot({ path: path.join(docsDir, "screenshot-compare.png"), fullPage: true });

await page.goto(`${baseUrl}/`);
await page.getByRole("button", { name: /Diseases/i }).click();
await page.getByPlaceholder(/breast/i).fill("breast");
await page.waitForTimeout(1200);
const diseaseLink = page.locator(".result-link").first();
if (await diseaseLink.count()) {
  await diseaseLink.click();
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(docsDir, "screenshot-disease.png"), fullPage: true });
}

await browser.close();
console.log("Screenshots saved to docs/");
