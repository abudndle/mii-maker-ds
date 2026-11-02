#!/usr/bin/env bash
# Trusted private third melonDS process: open Edit, cancel, preserve EEPROM.
set -euo pipefail
test -s mii-ds.nds
test "$(stat -c %s mii-ds.sav)" -eq 8192
bin_dir="$RUNNER_TEMP/melonds-1.1"
appimage="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$appimage"
export MELONDS_APP="$appimage"
export MELONDS_ROM="$PWD/mii-ds.nds"
export MELONDS_EDIT_IMAGE="$RUNNER_TEMP/melonds-edit.png"
export MELONDS_EDIT_LOG="$RUNNER_TEMP/melonds-edit.log"
export MELONDS_EDIT_HOME="$RUNNER_TEMP/melonds-edit-home.png"
export MELONDS_EDIT_GALLERY="$RUNNER_TEMP/melonds-edit-gallery.png"
export MELONDS_EDIT_RETURN="$RUNNER_TEMP/melonds-edit-return.png"
export HOME="$RUNNER_TEMP/melonds-home-edit"
# melonDS 1.1 reads its keymap from the Qt/XDG config directory. An
# unconfigured clean HOME has no reliable B binding: xdotool z alone was
# ignored by the real emulator. Explicitly map Qt::Key_Z (90) to DS B.
export XDG_CONFIG_HOME="$HOME/.config"
mkdir -p "$XDG_CONFIG_HOME/melonDS"
cat >"$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<'TOML'
[Instance0.Keyboard]
B = 90
TOML
cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-edit-before.sav"
export QT_QPA_PLATFORM=xcb SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM" >"$MELONDS_EDIT_LOG" 2>&1 &
  emu_pid=$!
  trap "kill $emu_pid 2>/dev/null || true" EXIT
  win=""
  for attempt in $(seq 1 25); do
    if ! kill -0 "$emu_pid" 2>/dev/null; then
      echo "FAIL: third melonDS process exited before Edit acceptance"
      exit 1
    fi
    win="$(xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$win" ]; then break; fi
    sleep 1
  done
  test -n "$win"
  sleep 12
  import -window "$win" -depth 8 "$MELONDS_EDIT_HOME"
  timeout 5s xdotool windowfocus --sync "$win" || true
  xdotool mousemove --window "$win" 120 232
  xdotool mousedown 1
  sleep 0.45
  xdotool mouseup 1
  sleep 15
  import -window "$win" -depth 8 "$MELONDS_EDIT_GALLERY"
  python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_GALLERY"
  capture_height="$(identify -format "%h" "$MELONDS_EDIT_GALLERY")"
  touch_origin=$((capture_height-192))
  # Select an ordinary, non-Personal saved Mii.
  xdotool mousemove --window "$win" 82 "$((touch_origin+71))"
  xdotool mousedown 1
  sleep 0.25
  xdotool mouseup 1
  sleep 4
  # Refresh the baseline AFTER selecting slot 1. Otherwise a selection-only
  # repaint could masquerade as a successful Edit transition.
  import -window "$win" -depth 8 "$MELONDS_EDIT_GALLERY"
  # Actual touchscreen Edit strip (172..247,168..190).
  xdotool mousemove --window "$win" 210 "$((touch_origin+179))"
  xdotool mousedown 1
  sleep 0.35
  xdotool mouseup 1
  sleep 6
  kill -0 "$emu_pid"
  import -window "$win" -depth 8 "$MELONDS_EDIT_IMAGE"
  python3 tools/check_melonds_edit_transition.py "$MELONDS_EDIT_GALLERY" "$MELONDS_EDIT_IMAGE"
  # No draft changes: B must leave Edit without a cartridge mutation.
  timeout 5s xdotool windowfocus --sync "$win" || true
  # A one-shot xdotool key can last less than a DS VBlank and be missed.
  # Hold the explicitly mapped B key across multiple 60 Hz samples.
  xdotool keydown --clearmodifiers z
  sleep 0.35
  xdotool keyup --clearmodifiers z
  sleep 6
  kill -0 "$emu_pid"
  import -window "$win" -depth 8 "$MELONDS_EDIT_RETURN"
  python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_RETURN"
  python3 tools/check_melonds_edit_transition.py "$MELONDS_EDIT_RETURN" "$MELONDS_EDIT_IMAGE"
'
python3 tools/melonds_screen_probe.py "$MELONDS_EDIT_IMAGE"
cmp -s "$RUNNER_TEMP/melonds-edit-before.sav" "$PWD/mii-ds.sav" || {
  echo "FAIL: Edit entry/cancellation unexpectedly changed EEPROM bytes"
  exit 1
}
if grep -Eiq 'segmentation fault|fatal error|failed to open rom|failed to load rom' "$MELONDS_EDIT_LOG"; then
  echo "FAIL: third melonDS process reported fatal/ROM error"
  exit 1
fi
echo "PASS: fresh melonDS opened touchscreen Edit, returned to gallery, and preserved EEPROM byte-for-byte"
