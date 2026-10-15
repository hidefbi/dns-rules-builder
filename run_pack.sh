#!/bin/bash
# Download all lists and build the trie for one configuration.
# Usage: HEAP=12288 ./run_pack.sh <name> <config.json>
#   Reads  files_<name>/ (written by download.py)
#   Writes out_<name>/   (td.txt, rd.txt, basicconfig.json, filetag.json)
set -euo pipefail
cd "$(dirname "$0")"

N="${1:?usage: run_pack.sh <name> <config.json>}"
CONFIG="${2:?usage: run_pack.sh <name> <config.json>}"
INDIR="files_${N}"
OUTDIR="out_${N}"
mkdir -p logs

export BLCONFIG="$CONFIG" INDIR OUTDIR CODEC=b8 UNIX_EPOCH_SEC="$(date +%s)"
rm -rf "$INDIR" "$OUTDIR"

echo "[$(date +%T)] download start"
START=$(date +%s)
nice -n 10 python3 download.py > "logs/${N}_download.log" 2>&1
echo "[$(date +%T)] download done in $(( $(date +%s) - START ))s; files: $(find "$INDIR" -type f | wc -l)"

echo "[$(date +%T)] build start (heap ${HEAP:-4096} MB)"
START=$(date +%s)
nice -n 10 /usr/bin/time -l node --max-old-space-size="${HEAP:-4096}" --expose-gc src/build.js > "logs/${N}_build.log" 2>&1
echo "[$(date +%T)] build done in $(( $(date +%s) - START ))s"
grep -E "maximum resident" "logs/${N}_build.log" || true
ls -l "$OUTDIR"
