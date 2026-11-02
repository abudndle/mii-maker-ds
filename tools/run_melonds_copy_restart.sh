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
# Reuse the proven, fresh second emulator for Edit/cancel instead of starting
# a third AppImage instance that has repeatedly aborted before first capture.
export MELONDS_COPY_EDIT_GALLERY="$RUNNER_TEMP/melonds-copy-edit-gallery.png"
export MELONDS_COPY_EDIT_IMAGE="$RUNNER_TEMP/melonds-edit.png"
export MELONDS_COPY_EDIT_RETURN="$RUNNER_TEMP/melonds-copy-edit-return.png"
export HOME="$RUNNER_TEMP/melonds-home-restart"
export XDG_CONFIG_HOME="$HOME/.config"
mkdir -p "$XDG_CONFIG_HOME/melonDS"
# Explicit Qt::Key_Z -> DS B, held across several VBlanks for cancellation.
cat >"$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<'TOML'
[Instance0.Keyboard]
B = 90
TOML
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
  # Qt window XGetImage may hang even for the initial reopened Home.
  # Capture ONLY the validated melonDS window rectangle from isolated Xvfb.
  # The original window ID remains valid when the title changes; re-search
  # only when that ID is gone. Never capture or upload the full desktop.
  capture_copy_edit() {
    local destination="$1" candidate="$win" geometry="" x y width height
    geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate" 2>/dev/null || true)"
    if [ -z "$geometry" ]; then
      candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
      test -n "$candidate" || { echo "FAIL: no live Copy/Edit window"; return 1; }
      geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate" 2>/dev/null)" ||
        { echo "FAIL: no Copy/Edit window geometry"; return 1; }
    fi
    x="$(printf '%s\n' "$geometry" | sed -n 's/^X=//p')"
    y="$(printf '%s\n' "$geometry" | sed -n 's/^Y=//p')"
    width="$(printf '%s\n' "$geometry" | sed -n 's/^WIDTH=//p')"
    height="$(printf '%s\n' "$geometry" | sed -n 's/^HEIGHT=//p')"
    if ! [[ "$x" =~ ^[0-9]+$ && "$y" =~ ^[0-9]+$ &&
            "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]] ||
       ! (( width >= 256 && height >= 384 &&
             x + width <= 1280 && y + height <= 960 )); then
      echo "FAIL: unsafe Copy/Edit capture geometry"
      return 1
    fi
    win="$candidate"
    timeout 12s import -window root -depth 8 -crop "${width}x${height}+${x}+${y}" +repage "$destination"
    test -s "$destination"
    test "$(timeout 5s identify -format "%wx%h" "$destination")" = "${width}x${height}" || {
      echo "FAIL: cropped Copy/Edit capture dimensions changed"
      return 1
    }
  }
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
  echo "Copy acceptance: capturing reopened Home"
  capture_copy_edit "$MELONDS_COPY_HOME"
  timeout 5s xdotool windowfocus --sync "$win" || true
  xdotool mousemove --window "$win" 120 232
  xdotool mousedown 1
  sleep 0.45
  xdotool mouseup 1
  sleep 15
  echo "Copy acceptance: capturing saved gallery"
  capture_copy_edit "$MELONDS_COPY_GALLERY"
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
  echo "Copy acceptance: capturing post-Copy gallery"
  capture_copy_edit "$MELONDS_COPY_IMAGE"
  test -s "$MELONDS_COPY_IMAGE"
  # Prove the Copy transaction completed BEFORE attempting Edit. The
  # subsequent byte-identity check is relative to this post-Copy snapshot,
  # so it cannot hide an Edit write behind the expected Copy generation.
  python3 tools/check_gallery_copy_save.py "$RUNNER_TEMP/melonds-copy-before.sav" "$PWD/mii-ds.sav" --report "$RUNNER_TEMP/melonds-copy-save.json"
  cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-postcopy.sav"
  echo "Edit acceptance: Copy persisted; selecting ordinary Mii"
  timeout 5s xdotool windowfocus --sync "$win" || true
  xdotool mousemove --window "$win" 82 "$((touch_origin+71))"
  xdotool mousedown 1
  sleep 0.25
  xdotool mouseup 1
  sleep 3
  echo "Edit acceptance: capturing selected gallery"
  capture_copy_edit "$MELONDS_COPY_EDIT_GALLERY"
  # Tap actual gallery Edit strip; selection-only changes are excluded from
  # the transition baseline by capturing AFTER selection.
  xdotool mousemove --window "$win" 210 "$((touch_origin+179))"
  xdotool mousedown 1
  sleep 0.35
  xdotool mouseup 1
  sleep 6
  kill -0 "$emu_pid"
  echo "Edit acceptance: capturing editor"
  capture_copy_edit "$MELONDS_COPY_EDIT_IMAGE"
  python3 tools/check_melonds_edit_transition.py "$MELONDS_COPY_EDIT_GALLERY" "$MELONDS_COPY_EDIT_IMAGE"
  echo "Edit acceptance: editor transition confirmed"
  timeout 5s xdotool windowfocus --sync "$win" || true
  xdotool keydown --clearmodifiers z
  sleep 0.35
  xdotool keyup --clearmodifiers z
  sleep 6
  kill -0 "$emu_pid"
  echo "Edit acceptance: capturing B return"
  capture_copy_edit "$MELONDS_COPY_EDIT_RETURN"
  python3 tools/melonds_gallery_probe.py "$MELONDS_COPY_HOME" "$MELONDS_COPY_EDIT_RETURN"
  python3 tools/check_melonds_edit_transition.py "$MELONDS_COPY_EDIT_RETURN" "$MELONDS_COPY_EDIT_IMAGE"
  echo "Edit acceptance: returned to gallery"
'
python3 tools/melonds_screen_probe.py "$MELONDS_COPY_IMAGE" --report "$RUNNER_TEMP/melonds-copy-metadata.json"
python3 tools/check_gallery_copy_save.py "$RUNNER_TEMP/melonds-copy-before.sav" "$PWD/mii-ds.sav" \
  --report "$RUNNER_TEMP/melonds-copy-save.json"
python3 tools/melonds_screen_probe.py "$MELONDS_COPY_EDIT_IMAGE"
cmp -s "$RUNNER_TEMP/melonds-copy-postcopy.sav" "$PWD/mii-ds.sav" || {
  echo "FAIL: Edit cancellation changed EEPROM after verified Copy"
  exit 1
}
if grep -Eiq 'segmentation fault|fatal error|failed to open rom|failed to load rom' "$MELONDS_COPY_LOG"; then
  echo "FAIL: restarted melonDS emitted a fatal/ROM load error"
  exit 1
fi
echo "PASS: restarted melonDS persisted Copy, opened Edit, returned via B and preserved EEPROM"
