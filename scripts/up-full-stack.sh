#!/usr/bin/env sh
# Start GapForge + OntoHarness + Embabel MCP (full agent/HITL stack).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "Copy .env.example to .env and set OPENAI_API_KEY first."
  exit 1
fi

for dir in ../ontoharness ../embabel-mcp; do
  if [ ! -d "$dir" ]; then
    echo "Missing $dir — clone sibling repos next to gapforge."
    exit 1
  fi
done

exec docker compose -f docker-compose.full.yml up --build "$@"
