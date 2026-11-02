#!/usr/bin/env bash
# Trusted owner-only acceptance: received source -> cancel -> confirm copy -> Edit.
# Never upload raw cartridge saves, private ROMs or unencrypted screenshots.
set -euo pipefail
test -s mii-ds.nds
test -x "$RUNNER_TEMP/make_gallery_fixture"
# The previous Favorite/Copy acceptance has completed; this stage uses a
# NEW synthetic received-source cartridge, not the owner's actual save.
"$RUNNER_TEMP/make_gallery_fixture" mii-ds.sav --received
test "$(stat -c %s mii-ds.sav)" -eq 8192
cp mii-ds.sav "$RUNNER_TEMP/melonds-received-before.sav"
python3 tools/check_gallery_received_copy_save.py \
  "$RUNNER_TEMP/melonds-received-before.sav" mii-ds.sav --mode cancel

bin_dir="$RUNNER_TEMP/melonds-1.1"
appimage="$(find "$bin_dir" -maxdepth 3 -type f -name '*.AppImage' -print -quit)"
test -n "$appimage"
# Earlier private acceptance can leave an AppImage child. Only terminate the
# exact melonDS executable on this dedicated trusted runner.
if pgrep -x melonDS >/dev/null 2>&1; then
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
    echo "FAIL: stale melonDS survived cleanup"
    exit 1
  fi
fi
export MELONDS_APP="$appimage" MELONDS_ROM="$PWD/mii-ds.nds"
export MELONDS_RECEIVED_LOG="$RUNNER_TEMP/melonds-received.log"
export MELONDS_RECEIVED_HOME="$RUNNER_TEMP/melonds-received-home.png"
export MELONDS_RECEIVED_GALLERY="$RUNNER_TEMP/melonds-received-gallery.png"
export MELONDS_RECEIVED_MODAL="$RUNNER_TEMP/melonds-received-modal.png"
export MELONDS_RECEIVED_CANCEL="$RUNNER_TEMP/melonds-received-cancel.png"
export MELONDS_RECEIVED_EDITOR="$RUNNER_TEMP/melonds-received-editor.png"
export MELONDS_RECEIVED_RETURN="$RUNNER_TEMP/melonds-received-return.png"
export MELONDS_RECEIVED_POSTCOPY="$RUNNER_TEMP/melonds-received-postcopy.sav"
export HOME="$RUNNER_TEMP/melonds-home-received"
# Proven melonDS 1.1 Qt B key mapping; touch handles Yes/No on the source
# CLYT B_BtnCommon_00 / B_BtnCommon_01 panes (28..228, y71..103/111..143).
unset XDG_CONFIG_HOME
mkdir -p "$HOME/.config/melonDS"
cat >"$HOME/.config/melonDS/melonDS.toml" <<'TOML'
[Instance0]
[Instance0.Keyboard]
B = 90
TOML
export MELONDS_B_CONFIG_SHA="$(sha256sum "$HOME/.config/melonDS/melonDS.toml" | cut -d ' ' -f 1)"
export QT_QPA_PLATFORM=xcb SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
echo "Received acceptance: launching isolated synthetic cartridge"
timeout 170s xvfb-run -a -s '-screen 0 1280x960x24' bash -c '
  set -euo pipefail
  setsid -w "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM" >"$MELONDS_RECEIVED_LOG" 2>&1 &
  emu_pid=$!
  cleanup() {
    kill -- "-$emu_pid" 2>/dev/null || true
    kill "$emu_pid" 2>/dev/null || true
    wait "$emu_pid" 2>/dev/null || true
  }
  trap cleanup EXIT
  win=""
  for attempt in $(seq 1 25); do
    kill -0 "$emu_pid" 2>/dev/null || { echo "FAIL: received emulator exited before window"; exit 1; }
    win="$(timeout 5s xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$win" ]; then break; fi
    sleep 1
  done
  test -n "$win" || { echo "FAIL: no received emulator window"; exit 1; }
  qt_pid="$(timeout 5s xdotool getwindowpid "$win" 2>/dev/null || true)"
  if ! [[ "$qt_pid" =~ ^[1-9][0-9]*$ ]] || [ ! -r "/proc/$qt_pid/environ" ]; then
    echo "FAIL: received emulator has no readable window owner"
    exit 1
  fi
  python3 tools/verify_melonds_input_config.py --pid "$qt_pid" --expected-home "$HOME" --expected-sha256 "$MELONDS_B_CONFIG_SHA"
  capture_received() {
    local dest="$1" candidate="$win" geometry="" x y width height
    geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate" 2>/dev/null || true)"
    if [ -z "$geometry" ]; then
      candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
      test -n "$candidate" || { echo "FAIL: received emulator window vanished"; return 1; }
      geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate" 2>/dev/null)"
    fi
    x="$(printf "%s\n" "$geometry" | sed -n "s/^X=//p")"
    y="$(printf "%s\n" "$geometry" | sed -n "s/^Y=//p")"
    width="$(printf "%s\n" "$geometry" | sed -n "s/^WIDTH=//p")"
    height="$(printf "%s\n" "$geometry" | sed -n "s/^HEIGHT=//p")"
    if ! [[ "$x" =~ ^[0-9]+$ && "$y" =~ ^[0-9]+$ &&
            "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]] ||
       ! (( width >= 256 && height >= 384 &&
             x + width <= 1280 && y + height <= 960 )); then
      echo "FAIL: unsafe received capture geometry"
      return 1
    fi
    win="$candidate"
    timeout 12s import -window root -depth 8 -crop "${width}x${height}+${x}+${y}" +repage "$dest"
    test -s "$dest"
  }
  tap() {
    timeout 5s xdotool windowfocus --sync "$win" || true
    timeout 5s xdotool mousemove --window "$win" "$1" "$2"
    timeout 5s xdotool mousedown 1
    sleep 0.35
    timeout 5s xdotool mouseup 1
  }
  sleep 12
  capture_received "$MELONDS_RECEIVED_HOME"
  tap 120 232
  sleep 12
  capture_received "$MELONDS_RECEIVED_GALLERY"
  timeout 15s python3 tools/melonds_gallery_probe.py "$MELONDS_RECEIVED_HOME" "$MELONDS_RECEIVED_GALLERY"
  height="$(timeout 5s identify -format "%h" "$MELONDS_RECEIVED_GALLERY")"
  touch_origin=$((height-192))
  tap 82 "$((touch_origin+71))"  # synthetic received source slot 1
  sleep 3
  capture_received "$MELONDS_RECEIVED_GALLERY"
  tap 210 "$((touch_origin+179))" # Edit -> copy-before-edit modal
  sleep 5
  capture_received "$MELONDS_RECEIVED_MODAL"
  timeout 15s python3 tools/check_melonds_confirm_modal.py "$MELONDS_RECEIVED_GALLERY" "$MELONDS_RECEIVED_MODAL"
  echo "Received acceptance: rejecting copy-to-edit via original No pane"
  tap 128 "$((touch_origin+127))"
  sleep 5
  capture_received "$MELONDS_RECEIVED_CANCEL"
  # Qt may accept focus while dropping the first stylus release after a
  # screenshot/window refresh. Retry ONLY if the modal has not visibly
  # changed and the cartridge is still byte-identical to the pre-copy save.
  # Never mask a real second failure or replay an already accepted choice.
  if ! timeout 15s python3 tools/check_melonds_confirm_modal.py "$MELONDS_RECEIVED_MODAL" "$MELONDS_RECEIVED_CANCEL" >/dev/null 2>&1; then
    echo "Received acceptance: No touch not observed; retrying once with refreshed window"
    cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav" || {
      echo "FAIL: received No retry blocked by unexpected EEPROM mutation"
      exit 1
    }
    kill -0 "$emu_pid"
    candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS" 2>/dev/null | tail -n 1 || true)"
    test -n "$candidate" || { echo "FAIL: no live received window for No retry"; exit 1; }
    win="$candidate"
    tap 128 "$((touch_origin+127))"
    sleep 5
    capture_received "$MELONDS_RECEIVED_CANCEL"
  fi
  timeout 15s python3 tools/check_melonds_confirm_modal.py "$MELONDS_RECEIVED_MODAL" "$MELONDS_RECEIVED_CANCEL"
  timeout 15s python3 tools/melonds_gallery_probe.py "$MELONDS_RECEIVED_HOME" "$MELONDS_RECEIVED_CANCEL"
  cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav" || {
    echo "FAIL: cancelling received copy changed EEPROM"
    exit 1
  }
  echo "Received acceptance: cancellation left cartridge byte-identical"
  tap 210 "$((touch_origin+179))"
  sleep 5
  capture_received "$MELONDS_RECEIVED_MODAL"
  timeout 15s python3 tools/check_melonds_confirm_modal.py "$MELONDS_RECEIVED_CANCEL" "$MELONDS_RECEIVED_MODAL"
  echo "Received acceptance: confirming copy-to-edit via original Yes pane"
  tap 128 "$((touch_origin+87))"
  sleep 7
  kill -0 "$emu_pid"
  capture_received "$MELONDS_RECEIVED_EDITOR"
  timeout 15s python3 tools/check_melonds_edit_transition.py "$MELONDS_RECEIVED_GALLERY" "$MELONDS_RECEIVED_EDITOR"
  echo "Received acceptance: confirmed copy opened editor"
  cp "$PWD/mii-ds.sav" "$MELONDS_RECEIVED_POSTCOPY"
  # Copy is committed; B must leave the newly editable copy without another
  # EEPROM transaction. Keep the synthetic key held across several VBlanks,
  # but below the host auto-repeat delay.
  timeout 5s xdotool windowfocus --sync "$win" || true
  timeout 5s xdotool keydown --clearmodifiers z
  sleep 0.12
  timeout 5s xdotool keyup --clearmodifiers z
  sleep 6
  kill -0 "$emu_pid"
  capture_received "$MELONDS_RECEIVED_RETURN"
  if ! timeout 15s python3 tools/check_melonds_edit_transition.py "$MELONDS_RECEIVED_RETURN" "$MELONDS_RECEIVED_EDITOR"; then
    echo "Received acceptance: B not observed; retrying after focusing game surface"
    timeout 5s xdotool mousemove --window "$win" 128 65
    timeout 5s xdotool mousedown 1
    sleep 0.15
    timeout 5s xdotool mouseup 1
    timeout 5s xdotool windowfocus --sync "$win" || true
    timeout 5s xdotool keydown --clearmodifiers z
    sleep 0.12
    timeout 5s xdotool keyup --clearmodifiers z
    sleep 6
    kill -0 "$emu_pid"
    capture_received "$MELONDS_RECEIVED_RETURN"
    timeout 15s python3 tools/check_melonds_edit_transition.py "$MELONDS_RECEIVED_RETURN" "$MELONDS_RECEIVED_EDITOR"
  fi
  echo "Received acceptance: B returned from editable copy"
'
python3 tools/check_gallery_received_copy_save.py \
  "$RUNNER_TEMP/melonds-received-before.sav" mii-ds.sav --mode copy
cmp -s "$MELONDS_RECEIVED_POSTCOPY" "$PWD/mii-ds.sav" || {
  echo "FAIL: received editable-copy cancellation changed EEPROM"
  exit 1
}
if grep -Eiq 'segmentation fault|fatal error|failed to open rom|failed to load rom' "$MELONDS_RECEIVED_LOG"; then
  echo "FAIL: received emulator reported fatal/ROM error"
  exit 1
fi
echo "PASS: real melonDS received modal cancelled, copied editable Mii, then B returned without EEPROM write"
