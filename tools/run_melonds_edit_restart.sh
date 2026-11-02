#!/usr/bin/env bash
# Trusted private third melonDS process: open Edit, cancel, preserve EEPROM.
set -euo pipefail
test -s mii-ds.nds
test "$(stat -c %s mii-ds.sav)" -eq 8192
bin_dir="$RUNNER_TEMP/melonds-1.1"
appimage="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$appimage"
# The two preceding isolated Xvfb stages must not leave a real Qt emulator
# behind. AppImage child processes can detach from their launcher's process
# group and redirect later ROM launches to a stale instance. This trusted
# GitHub-hosted runner is dedicated to this job; terminate only the exact
# melonDS executable name, never arbitrary user processes or path matches.
if pgrep -x melonDS >/dev/null 2>&1; then
  echo "Edit acceptance: reaping stale emulator from earlier stage"
  pkill -TERM -x melonDS 2>/dev/null || true
  for attempt in 1 2 3 4 5; do
    if ! pgrep -x melonDS >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if pgrep -x melonDS >/dev/null 2>&1; then
    pkill -KILL -x melonDS 2>/dev/null || true
    sleep 1
  fi
  if pgrep -x melonDS >/dev/null 2>&1; then
    echo "FAIL: previous melonDS process survived cleanup; refusing Edit test"
    exit 1
  fi
fi
# Extract the verified AppImage once and launch AppRun directly for the
# third emulator process. The AppImage --appimage-extract-and-run wrapper
# has intermittently exited with status 127 before the first Edit capture,
# even though the preceding Favorite and Copy processes succeeded. Keep
# this extraction in the trusted runner and never upload extracted files.
edit_appdir="$RUNNER_TEMP/melonds-1.1/edit-apprun"
mkdir -p "$edit_appdir"
(
  cd "$edit_appdir"
  timeout 60s "$appimage" --appimage-extract >/dev/null
)
test -x "$edit_appdir/squashfs-root/AppRun"
export APPDIR="$edit_appdir/squashfs-root"
export MELONDS_APP="$APPDIR/AppRun"
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
echo "Edit acceptance: launching isolated emulator"
timeout 150s xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  # Give the AppImage and its extracted melonDS child a dedicated process
  # group. Killing only the AppImage wrapper can orphan the actual Qt
  # emulator, leaving a stale window or forwarding a later ROM launch to it.
  setsid -w "$MELONDS_APP" "$MELONDS_ROM" >"$MELONDS_EDIT_LOG" 2>&1 &
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
      echo "FAIL: third melonDS process exited before Edit acceptance"
      exit 1
    fi
    win="$(xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$win" ]; then break; fi
    sleep 1
  done
  test -n "$win"
  echo "Edit acceptance: window ready"
  # XGetImage against a Qt window can block, and the initial melonDS
  # window ID may be replaced during ROM startup. Capture only the current
  # visible window rectangle from the isolated Xvfb root. Re-resolve the
  # window for every frame instead of reusing a potentially dead XID.
  capture_edit() {
    local destination="$1" geometry="" candidate="" x y width height attempt status
    for attempt in 1 2 3; do
      if ! kill -0 "$emu_pid" 2>/dev/null; then
        if wait "$emu_pid"; then
          echo "FAIL: Edit emulator launcher exited cleanly before capture"
        else
          status=$?
          echo "FAIL: Edit emulator exited before capture (status $status)"
        fi
        # Print only a fixed failure category, never raw emulator stderr,
        # which can contain the owner-private ROM and runner paths.
        python3 tools/classify_melonds_startup.py "$MELONDS_EDIT_LOG"
        return 1
      fi
      candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
      if [ -n "$candidate" ] &&
         geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate" 2>/dev/null)"; then
        win="$candidate"
        break
      fi
      geometry=""
      sleep 1
    done
    if [ -z "$geometry" ]; then
      echo "FAIL: no stable visible melonDS window for bounded Edit capture"
      return 1
    fi
    x="$(printf '%s\n' "$geometry" | sed -n 's/^X=//p')"
    y="$(printf '%s\n' "$geometry" | sed -n 's/^Y=//p')"
    width="$(printf '%s\n' "$geometry" | sed -n 's/^WIDTH=//p')"
    height="$(printf '%s\n' "$geometry" | sed -n 's/^HEIGHT=//p')"
    if ! [[ "$x" =~ ^[0-9]+$ && "$y" =~ ^[0-9]+$ &&
            "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]] ||
       ! (( width >= 256 && height >= 384 &&
             x + width <= 1280 && y + height <= 960 )); then
      echo "FAIL: invalid bounded Edit capture geometry"
      return 1
    fi
    timeout 12s import -window root -depth 8 -crop "${width}x${height}+${x}+${y}" +repage "$destination"
    test -s "$destination"
  }

  sleep 12
  capture_edit "$MELONDS_EDIT_HOME"
  timeout 5s xdotool windowfocus --sync "$win" || true
  timeout 5s xdotool mousemove --window "$win" 120 232
  timeout 5s xdotool mousedown 1
  sleep 0.45
  timeout 5s xdotool mouseup 1
  sleep 15
  capture_edit "$MELONDS_EDIT_GALLERY"
  echo "Edit acceptance: verifying gallery entry"
  timeout 15s python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_GALLERY"
  capture_height="$(timeout 5s identify -format "%h" "$MELONDS_EDIT_GALLERY")"
  touch_origin=$((capture_height-192))
  # Select an ordinary, non-Personal saved Mii.
  timeout 5s xdotool mousemove --window "$win" 82 "$((touch_origin+71))"
  timeout 5s xdotool mousedown 1
  sleep 0.25
  timeout 5s xdotool mouseup 1
  sleep 4
  # Refresh the baseline AFTER selecting slot 1. Otherwise a selection-only
  # repaint could masquerade as a successful Edit transition.
  capture_edit "$MELONDS_EDIT_GALLERY"
  echo "Edit acceptance: selected ordinary Mii"
  # Actual touchscreen Edit strip (172..247,168..190).
  timeout 5s xdotool mousemove --window "$win" 210 "$((touch_origin+179))"
  timeout 5s xdotool mousedown 1
  sleep 0.35
  timeout 5s xdotool mouseup 1
  sleep 6
  kill -0 "$emu_pid"
  capture_edit "$MELONDS_EDIT_IMAGE"
  echo "Edit acceptance: verifying editor transition"
  timeout 15s python3 tools/check_melonds_edit_transition.py "$MELONDS_EDIT_GALLERY" "$MELONDS_EDIT_IMAGE"
  # No draft changes: B must leave Edit without a cartridge mutation.
  timeout 5s xdotool windowfocus --sync "$win" || true
  # A one-shot xdotool key can last less than a DS VBlank and be missed.
  # Hold the explicitly mapped B key across multiple 60 Hz samples.
  timeout 5s xdotool keydown --clearmodifiers z
  sleep 0.35
  timeout 5s xdotool keyup --clearmodifiers z
  sleep 6
  kill -0 "$emu_pid"
  capture_edit "$MELONDS_EDIT_RETURN"
  echo "Edit acceptance: verifying B return"
  timeout 15s python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_RETURN"
  timeout 15s python3 tools/check_melonds_edit_transition.py "$MELONDS_EDIT_RETURN" "$MELONDS_EDIT_IMAGE"
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
