# Caffeine indicator validation

Validated on 2026-10-21 with a separate `coffee-trial` SketchyBar instance.
The installed bar and the existing Raycast caffeinate session remained unchanged.

## Automated checks

`python3 previews/sketchybar/test_plugins.py` passed all 19 checks.
The checks include overlapping sessions, failed process queries, duplicate listeners,
an exit between the snapshot and process-watch registration, recovery during reload,
and actual AppKit rendering and caching of the mug.
Shell syntax checks and `git diff --check` passed.

## Native event trial

The listener used real macOS power events, kqueue process notifications, and a native bar.
The test reader excluded pre-existing caffeinate PIDs from its snapshot.
This allowed independent on/off checks without stopping the user's session.
The production reader has no such filter.

- An independent indefinite session showed the mug. Terminating it hid the mug.
- An independent one-second session showed the mug. Its expiry hid the mug.
- Two overlapping sessions kept the mug visible until both exited.
- A duplicate listener exited without starting another event stream.
- Restarting the listener during a session restored the active state.
- Stopping the trial bar stopped its listener and reaped the pmset child.

Four sampled transitions reached the native `drawing` property in about 22–59 ms.
These samples used a warmed icon cache and a test-only query loop.
They measure command-state observation, not pixels on screen or a latency guarantee.
The production listener has no polling timer.

## Complete configuration trial

The unmodified candidate configuration ran in another named bar instance.
Its production reader showed the mug for the existing caffeinate session.
Native geometry placed the mug before the clock on both attached displays.
The cached image used scale `0.5`, with a 36×36 source and an 18-point displayed symbol.
The image was visually inspected as a white outline mug with a transparent background.

Reloading the config and triggering `system_woke` restored the active item.
The same listener PID survived both actions. Its item had `update_freq=0`.
During reload, the listener tolerated a failed update while the item was absent.
It remained active and recovered after the item returned.

Raycast start/stop commands were not invoked during the trial.
The installed Coffee extension was inspected and uses `/usr/bin/caffeinate`.
No end-to-end screen-pixel latency measurement was made.
