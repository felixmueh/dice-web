#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/dice"
RUNTIME_DIR="$ROOT_DIR/runtime"
BRIDGE_SOURCE="$ROOT_DIR/webbridge.py"
VIEWER_SOURCE="$ROOT_DIR/viewer.py"

# The dice runtime is the `dice` package inside the submodule (dice/dice/).
# The browser gets a copy of that package at runtime/dice/, so webbridge.py
# (runtime/webbridge.py) imports it as `dice.*` exactly as in a checkout.
PACKAGE_SOURCE_DIR="$SOURCE_DIR/dice"
PACKAGE_RUNTIME_DIR="$RUNTIME_DIR/dice"

# Modules the browser needs. Deliberately left out: viewer.py (matplotlib,
# replaced by the repo-local shim below), directdiceengine.py (sampling
# reference engine used only by dice's tests) and __main__.py (CLI entry).
PACKAGE_FILES=(
  __init__.py
  cli.py
  diagnostics.py
  diceengine.py
  diceparser.py
  executor.py
  hostfunctions.py
  interpreter.py
  jsonrenderer.py
  lexer.py
  purity.py
  renderplan.py
  resultjson.py
  syntaxtree.py
)

rm -rf "$RUNTIME_DIR"
mkdir -p "$PACKAGE_RUNTIME_DIR/stdlib" "$RUNTIME_DIR/examples"

for relative_path in "${PACKAGE_FILES[@]}"; do
  cp "$PACKAGE_SOURCE_DIR/$relative_path" "$PACKAGE_RUNTIME_DIR/$relative_path"
done

cp "$BRIDGE_SOURCE" "$RUNTIME_DIR/webbridge.py"
# The shim takes the place of dice/viewer.py, the module the matplotlib render
# backend imports, so no browser path can reach matplotlib.
cp "$VIEWER_SOURCE" "$PACKAGE_RUNTIME_DIR/viewer.py"

# `import "std:..."` resolves against stdlib/ next to interpreter.py.
cp -R "$PACKAGE_SOURCE_DIR/stdlib/." "$PACKAGE_RUNTIME_DIR/stdlib/"
cp -R "$SOURCE_DIR/examples/." "$RUNTIME_DIR/examples/"

cd "$RUNTIME_DIR"
python - <<'PY'
import json
from pathlib import Path

root = Path(".")
files = sorted(
    str(path.relative_to(root)).replace("\\", "/")
    for path in root.rglob("*")
    if path.is_file() and path.name != "manifest.json"
)
(root / "manifest.json").write_text(
    json.dumps({"files": files}, indent=2) + "\n",
    encoding="utf-8",
)
PY

echo "Runtime synced into $RUNTIME_DIR"
