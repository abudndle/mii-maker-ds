#!/usr/bin/env bash
# Public screenshots are allowed ONLY from the independent, asset-free homebrew ROM.
set -euo pipefail
test "${MDS_PUBLIC_DEMO_ONLY:-}" = yes
test -s public-demo/public-demo.nds
mkdir -p public-screenshots
bin_dir="$RUNNER_TEMP/public-melonds"
mkdir -p "$bin_dir"
archive="$bin_dir/melonds.zip"
curl --fail --location --silent --show-error --retry 2 \
  'https://github.com/melonDS-emu/melonDS/releases/download/1.1/melonDS-1.1-appimage-x86_64.zip' -o "$archive"
echo "bf377420a2e95f2cd2cdda17d5372b51c2534f858b038db9ec6d129554875124  $archive" | sha256sum --check
unzip -q "$archive" -d "$bin_dir"
app="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$app"
chmod +x "$app"
export MELONDS_APP="$app" MELONDS_ROM="$PWD/public-demo/public-demo.nds"
export MELONDS_IMAGE="$PWD/public-screenshots/synthetic-boot.png"
export HOME="$RUNNER_TEMP/public-melonds-home"
mkdir -p "$HOME"
export QT_QPA_PLATFORM=xcb SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  setsid "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM" >"$RUNNER_TEMP/public-melonds.log" 2>&1 &
  pid=$!
  trap '\''kill -- "-$pid" 2>/dev/null || true; kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true'\'' EXIT
  win=""
  for attempt in $(seq 1 25); do
    kill -0 "$pid" 2>/dev/null || { echo "FAIL: emulator exited"; cat "$RUNNER_TEMP/public-melonds.log"; exit 1; }
    win="$(xdotool search --onlyvisible --name melonDS 2>/dev/null | tail -n 1 || true)"
    test -z "$win" || break
    sleep 1
  done
  test -n "$win" || { echo "FAIL: no melonDS window"; cat "$RUNNER_TEMP/public-melonds.log"; exit 1; }
  sleep 12
  kill -0 "$pid"
  import -window "$win" -depth 8 "$MELONDS_IMAGE"
'
python3 tools/melonds_screen_probe.py "$MELONDS_IMAGE"
python3 - <<'PY'
from PIL import Image
from pathlib import Path
p=Path("public-screenshots/synthetic-boot.png")
with Image.open(p) as im:
    assert im.format=="PNG" and im.width>=256 and im.height>=384
    im.verify()
print("PASS: public-safe synthetic-only PNG; no original assets or ROM published")
PY
