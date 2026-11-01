#!/usr/bin/env bash
# Owner-private melonDS 1.1 boot + framebuffer test. Images are never uploaded raw.
set -euo pipefail
test -s mii-ds.nds
bin_dir="$RUNNER_TEMP/melonds-1.1"
mkdir -p "$bin_dir"
archive="$bin_dir/melonDS-1.1-appimage-x86_64.zip"
curl --fail --location --silent --show-error --retry 2 \
  'https://github.com/melonDS-emu/melonDS/releases/download/1.1/melonDS-1.1-appimage-x86_64.zip' \
  --output "$archive"
echo "bf377420a2e95f2cd2cdda17d5372b51c2534f858b038db9ec6d129554875124  $archive" | sha256sum --check
unzip -q "$archive" -d "$bin_dir"
appimage="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$appimage"
chmod +x "$appimage"
export MELONDS_APP="$appimage"
export MELONDS_ROM="$PWD/mii-ds.nds"
export MELONDS_IMAGE="$RUNNER_TEMP/melonds-boot.png"
export MELONDS_LOG="$RUNNER_TEMP/melonds-boot.log"
export HOME="$RUNNER_TEMP/melonds-home"
mkdir -p "$HOME"
export QT_QPA_PLATFORM=xcb SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM" >"$MELONDS_LOG" 2>&1 &
  emu_pid=$!
  trap "kill $emu_pid 2>/dev/null || true" EXIT
  win=""
  for attempt in $(seq 1 25); do
    if ! kill -0 "$emu_pid" 2>/dev/null; then
      echo "FAIL: melonDS exited before displaying the ROM"
      tail -c 1500 "$MELONDS_LOG" || true
      exit 1
    fi
    win="$(xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$win" ]; then break; fi
    sleep 1
  done
  if [ -z "$win" ]; then
    echo "FAIL: no visible melonDS window"
    tail -c 1500 "$MELONDS_LOG" || true
    exit 1
  fi
  sleep 12
  if ! kill -0 "$emu_pid" 2>/dev/null; then
    echo "FAIL: melonDS crashed during ROM boot"
    tail -c 1500 "$MELONDS_LOG" || true
    exit 1
  fi
  import -window "$win" -depth 8 "$MELONDS_IMAGE"
  test -s "$MELONDS_IMAGE"
  echo "PASS: melonDS remained running and a framebuffer was captured"
'
python3 tools/melonds_screen_probe.py "$MELONDS_IMAGE" --report "$RUNNER_TEMP/melonds-boot-metadata.json"
# Suppress potentially sensitive file paths in emulator logs.
if grep -Eiq 'segmentation fault|fatal error|failed to open rom|failed to load rom' "$MELONDS_LOG"; then
  echo 'FAIL: melonDS emitted a fatal/ROM load error'
  exit 1
fi
echo "PASS: original-resource ROM ran in melonDS 1.1 long enough for a nonuniform frame"
