#!/usr/bin/env bash
# Owner-private second melonDS process: load persisted Favorite, then Copy.
set -euo pipefail
test -s mii-ds.nds
test "$(stat -c %s mii-ds.sav)" -eq 8192
bin_dir="$RUNNER_TEMP/melonds-1.1"
appimage="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$appimage"
export MELONDS_APP="$appimage"
export MELONDS_ROM="$PWD/mii-ds.nds"
export MELONDS_COPY_IMAGE="$RUNNER_TEMP/melonds-copy.png"
export MELONDS_COPY_LOG="$RUNNER_TEMP/melonds-copy.log"
export MELONDS_COPY_HOME="$RUNNER_TEMP/melonds-copy-home.png"
export MELONDS_COPY_GALLERY="$RUNNER_TEMP/melonds-copy-gallery.png"
export HOME="$RUNNER_TEMP/melonds-home-restart"
mkdir -p "$HOME"
# Never upload or log the pre-copy save image.
cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-before.sav"
export QT_QPA_PLATFORM=xcb SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  # Give the AppImage and its extracted melonDS child a dedicated process
  # group. Killing only the AppImage wrapper can orphan the actual Qt
  # emulator, leaving a stale window or forwarding a later ROM launch to it.
  setsid -w "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM" >"$MELONDS_COPY_LOG" 2>&1 &
  emu_pid=$!
  cleanup_emulator() {
    kill -- "-$emu_pid" 2>/dev/null || true
    kill "$emu_pid" 2>/dev/null || true
    wait "$emu_pid" 2>/dev/null || true
  }
  trap cleanup_emulator EXIT
  win=""
  for attempt in $(seq 1 25); do
    if ! kill -0 "$emu_pid" 2>/dev/null; then
      echo "FAIL: restarted melonDS exited before showing saved gallery"
      exit 1
    fi
    win="$(xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$win" ]; then break; fi
    sleep 1
  done
  test -n "$win"
  sleep 12
  import -window "$win" -depth 8 "$MELONDS_COPY_HOME"
  xdotool windowfocus --sync "$win" || true
  xdotool mousemove --window "$win" 120 232
  xdotool mousedown 1
  sleep 0.45
  xdotool mouseup 1
  sleep 15
  import -window "$win" -depth 8 "$MELONDS_COPY_GALLERY"
  # A second process must actually load the previous 10-Mii save.
  python3 tools/melonds_gallery_probe.py "$MELONDS_COPY_HOME" "$MELONDS_COPY_GALLERY"
  capture_height="$(identify -format "%h" "$MELONDS_COPY_GALLERY")"
  touch_origin=$((capture_height-192))
  xdotool mousemove --window "$win" 82 "$((touch_origin+71))"
  xdotool mousedown 1
  sleep 0.25
  xdotool mouseup 1
  sleep 4
  # Actual Copy strip (90..165,168..190), not a physical shortcut.
  xdotool mousemove --window "$win" 128 "$((touch_origin+179))"
  xdotool mousedown 1
  sleep 0.35
  xdotool mouseup 1
  sleep 5
  kill -0 "$emu_pid"
  import -window "$win" -depth 8 "$MELONDS_COPY_IMAGE"
  test -s "$MELONDS_COPY_IMAGE"
'
python3 tools/melonds_screen_probe.py "$MELONDS_COPY_IMAGE" --report "$RUNNER_TEMP/melonds-copy-metadata.json"
python3 tools/check_gallery_copy_save.py "$RUNNER_TEMP/melonds-copy-before.sav" "$PWD/mii-ds.sav" \
  --report "$RUNNER_TEMP/melonds-copy-save.json"
if grep -Eiq 'segmentation fault|fatal error|failed to open rom|failed to load rom' "$MELONDS_COPY_LOG"; then
  echo "FAIL: restarted melonDS emitted a fatal/ROM load error"
  exit 1
fi
echo "PASS: restarted melonDS loaded persisted gallery and copied a non-Personal Mii"
