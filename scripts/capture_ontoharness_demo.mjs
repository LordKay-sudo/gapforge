/**
 * Capture OntoHarness demo screenshots for docs/demo-recordings/.
 *
 * Prerequisites (full stack):
 *   docker compose -f docker-compose.full.yml up --build
 *
 * Usage:
 *   node scripts/capture_ontoharness_demo.mjs
 *
 * Env:
 *   WEB_URL     — GapForge UI (default http://127.0.0.1:8080)
 *   ONTO_URL    — OntoHarness docs (default http://127.0.0.1:8010/docs)
 */
import { createRequire } from "module";
import { mkdir } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "demo-recordings");
const webUrl = process.env.WEB_URL ?? "http://127.0.0.1:8080";
const ontoUrl = process.env.ONTO_URL ?? "http://127.0.0.1:8010/docs";

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

try {
  await page.goto(ontoUrl, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.screenshot({
    path: path.join(outDir, "screenshot-ontoharness-docs.png"),
    fullPage: true,
  });
  console.log("Saved screenshot-ontoharness-docs.png");
} catch (e) {
  console.warn("OntoHarness docs capture skipped:", e.message);
}

try {
  await page.goto(`${webUrl}/gaps/review`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2000);

  const efficacy = page.getByText(/gap-flurizan-efficacy|efficacy/i).first();
  if (await efficacy.count()) {
    await efficacy.click();
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: path.join(outDir, "screenshot-review-ontology-fail.png"),
      fullPage: true,
    });
    console.log("Saved screenshot-review-ontology-fail.png");
  }

  const endpoint = page.getByText(/gap-flurizan-endpoint|endpoint/i).first();
  if (await endpoint.count()) {
    await endpoint.click();
    await page.waitForTimeout(1500);
    const revalidate = page.getByRole("button", { name: /re-validate|ontology/i }).first();
    if (await revalidate.count()) {
      await revalidate.click().catch(() => {});
      await page.waitForTimeout(2000);
    }
    await page.screenshot({
      path: path.join(outDir, "screenshot-review-ontology-pass.png"),
      fullPage: true,
    });
    console.log("Saved screenshot-review-ontology-pass.png");
  }
} catch (e) {
  console.warn("GapForge review UI capture skipped:", e.message);
  console.warn("Start full stack: docker compose -f docker-compose.full.yml up --build");
}

await browser.close();
console.log(`Screenshots in ${outDir}`);
