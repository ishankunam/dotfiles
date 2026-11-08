import AppKit
import Foundation

@main struct EventStoreTests {
    static func main() {
        let start = Date(timeIntervalSince1970: 1_700_000_000)
        func item(_ id: String, _ external: String?, _ calendar: String, _ date: Date = start) -> CalendarEvent {
            CalendarEvent(id: id, externalID: external, start: date, end: date.addingTimeInterval(3600),
                          allDay: false, title: "Event", calendarID: calendar, calendarName: calendar,
                          accountName: calendar, color: NSColor.red.cgColor, location: nil, notes: nil,
                          url: nil, attendees: [], organizer: nil, event: nil)
        }
        let one = item("1", "shared", "a")
        let two = item("2", "shared", "b")
        precondition(groupEvents([one, two]).count == 1)
        precondition(groupEvents([one, two])[0].copies.count == 2)
        precondition(groupEvents([one, item("3", "shared", "b", start.addingTimeInterval(86400))]).count == 2)
        precondition(groupEvents([one, item("4", nil, "b"), item("5", nil, "c")]).count == 3)
        precondition(groupEvents([one, item("6", "shared", "a")]).count == 2)
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(secondsFromGMT: 0)!
        let day = cal.startOfDay(for: start)
        precondition(eventOverlapsDay(one, day, calendar: cal))
        precondition(!eventOverlapsDay(one, day.addingTimeInterval(86400), calendar: cal))
        print("EventStore tests passed")
    }
}
