#!/usr/bin/env bash
# 在 macOS 上通过 GitHub Actions 拉取 Windows 安装包（含 ARM 设备可用的 x64 兼容包）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="${1:-squeeze-pdf-Windows-Setup.exe}"

echo "==> 触发 GitHub Actions Build 工作流"
gh workflow run Build --ref "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"

echo "==> 等待最新运行完成"
run_id="$(gh run list -w Build -L 1 | awk -F'\t' '{print $7}')"
if [[ -z "$run_id" || ! "$run_id" =~ ^[0-9]+$ ]]; then
  echo "无法解析 Build 工作流 run id，请检查 gh 版本或手动执行: gh run watch <run-id>" >&2
  exit 1
fi
gh run watch "$run_id" --exit-status

echo "==> 下载 Windows 安装包"
tmpdir="$(mktemp -d)"
gh run download "$run_id" -n squeeze-pdf-Windows-Setup.exe -D "$tmpdir"
src="$tmpdir/squeeze-pdf-Windows-Setup.exe/squeeze-pdf-Windows-Setup.exe"
if [[ ! -f "$src" ]]; then
  src="$tmpdir/squeeze-pdf-Windows-Setup.exe"
fi
cp "$src" "$ROOT/$OUT"
rm -rf "$tmpdir"
ls -lh "$ROOT/$OUT"
echo "==> 完成: $ROOT/$OUT"
