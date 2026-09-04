#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Build research t2-sep-lab CLI. Does not alter stock install.sh.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:-$root/t2-sep-lab}"
dest_dir="$(dirname "$out")"
mkdir -p "$dest_dir"
cc -O2 -Wall -I "$root/src" -o "$out" "$root/tools/t2-sep-lab.c"
echo "built $out"
# Optional research install path used on MBA91:
#   tools/build-t2-sep-lab.sh /home/tim/Private/t2-touchid/t2-sep-lab
