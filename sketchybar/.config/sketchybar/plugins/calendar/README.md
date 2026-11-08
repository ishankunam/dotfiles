# SketchyBar calendar

The clock opens a local calendar panel. It reads calendars already synced to the
macOS Calendar database with EventKit. macOS requires full Calendar permission
to read events. The helper only reads calendar data and does not log events.

- Hover over the clock to open the current month and today's agenda.
- Click the clock to pin the panel. Click again or press Escape to close it.
- Choose a day to see its events. Scroll the agenda if it reaches 500 points.
- Choose an event to open its details on the left. The calendar filter in the
  header stores hidden calendar IDs in the helper's macOS preferences.
- Open in Apple Calendar requests macOS Automation permission. If Calendar
  cannot locate that event, the helper opens the event's date instead.

The first launch builds an ad hoc-signed app under `calendar/build/`. A source
change rebuilds the app when the helper is not running. macOS may ask for
Calendar or Automation access again after a rebuild. If access is denied,
change it in System Settings > Privacy & Security > Calendars or Automation.
The helper exits after two minutes with no panel open.

Run the data checks without accessing real calendars:

```sh
swiftc EventStore.swift tests/EventStoreTests.swift -o /tmp/sketchybar-event-tests
/tmp/sketchybar-event-tests
```

Run those commands from this directory. Build with `./build.sh`; the app accepts
`--preview` to show synthetic events without requesting Calendar access.
