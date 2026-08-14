/** Screenshot MCP tool session HTML + optional Inspector UI. */
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "demo-recordings");
const htmlPath = path.join(outDir, "mcp-tool-session-capture.html");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

await page.goto(`file:///${htmlPath.replace(/\\/g, "/")}`, { waitUntil: "load" });
await page.waitForTimeout(800);
await page.screenshot({
  path: path.join(outDir, "screenshot-mcp-tool-session.png"),
  fullPage: true,
});
console.log("Saved screenshot-mcp-tool-session.png");

await browser.close();
