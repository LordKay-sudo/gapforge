# Demo media capture

Automated capture (Playwright + optional ffmpeg):

```bash
docker compose up --build -d
# wait until http://localhost:8080 loads
node scripts/capture_media.mjs
```

Outputs:

| File | Description |
|------|-------------|
| `screenshot-search.png` | Search results for BRCA1 |
| `screenshot-graph.png` | Force-directed subgraph |
| `screenshot-gene-detail.png` | Full gene detail page |
| `demo-walkthrough.gif` | Short search → gene → graph animation (requires ffmpeg on PATH) |

Environment:

- `WEB_URL` — default `http://127.0.0.1:8080`
- `GENE_PATH` — default `/gene/ENSG00000012048`

Manual recording is still fine via [ScreenToGif](https://www.screentogif.com/) if ffmpeg is not installed.
