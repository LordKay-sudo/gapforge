/**
 * Invoke Embabel MCP tools over SSE and write demo outputs (live stack + OPENAI_API_KEY).
 *
 * Usage:
 *   npm install --prefix scripts
 *   node scripts/invoke_mcp_tools.mjs
 */
import { writeFile, mkdir } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "docs", "demo-recordings");
const mcpUrl = process.env.MCP_SSE_URL ?? "http://127.0.0.1:1337/sse";
const stamp = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

async function connect() {
  const client = new Client({ name: "gapforge-demo-recorder", version: "1.0.0" });
  const transport = new SSEClientTransport(new URL(mcpUrl));
  await client.connect(transport);
  return client;
}

function extractText(result) {
  if (result?.isError) {
    return `[tool error]\n${JSON.stringify(result.content, null, 2)}`;
  }
  const parts = result?.content ?? [];
  return parts
    .map((p) => (p.type === "text" ? p.text : JSON.stringify(p)))
    .join("\n");
}

async function callTool(client, name, args) {
  const started = Date.now();
  const result = await client.callTool({ name, arguments: args });
  return {
    name,
    arguments: args,
    duration_ms: Date.now() - started,
    isError: Boolean(result.isError),
    text: extractText(result),
  };
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const header = `# MCP tool session — ${stamp} (UTC)\n\nEndpoint: ${mcpUrl}\n\n`;
  const client = await connect();

  const toolList = await client.listTools();
  const names = toolList.tools.map((t) => t.name).sort();
  await writeFile(
    path.join(outDir, "13-mcp-tool-catalog.json"),
    header + JSON.stringify({ tool_count: names.length, tools: names }, null, 2) + "\n",
    "utf8",
  );
  console.log(`Listed ${names.length} MCP tools`);

  const sequence = [
    ["bioinsight_health", { format: "json" }],
    [
      "plan_gap_investigation",
      {
        question: "Why did the Flurizan AD program stall?",
        programId: "prog-flurizan-ad",
        format: "markdown",
      },
    ],
    ["build_program_dossier", { programId: "prog-flurizan-ad", format: "markdown" }],
    ["run_gap_ontology_validate", { gapId: "gap-flurizan-efficacy", format: "markdown" }],
    ["list_ontoharness_domains", { format: "json" }],
  ];

  const results = [];
  for (const [name, args] of sequence) {
    console.log(`Calling ${name}...`);
    try {
      results.push(await callTool(client, name, args));
    } catch (err) {
      results.push({
        name,
        arguments: args,
        isError: true,
        text: String(err),
      });
    }
  }

  await client.close();

  const sessionPath = path.join(outDir, "14-mcp-tool-session.json");
  await writeFile(sessionPath, header + JSON.stringify(results, null, 2) + "\n", "utf8");
  console.log(`Wrote ${sessionPath}`);

  const transcript = results
    .map(
      (r) =>
        `## ${r.name}\n\n\`\`\`json\n${JSON.stringify(r.arguments, null, 2)}\n\`\`\`\n\n${r.text}\n`,
    )
    .join("\n---\n\n");
  await writeFile(path.join(outDir, "14-mcp-tool-session.md"), header + transcript, "utf8");

  for (const r of results) {
    const safe = r.name.replace(/[^a-z0-9_-]+/gi, "-");
    await writeFile(
      path.join(outDir, `15-mcp-${safe}.txt`),
      header + r.text + "\n",
      "utf8",
    );
  }

  const failed = results.filter((r) => r.isError);
  if (failed.length) {
    console.warn(`${failed.length} tool call(s) failed`);
    process.exitCode = 1;
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
