import AppKit
import EventKit
import Combine
import Foundation

// These values contain only data needed by the local interface. They are never logged.
struct CalendarEvent: Identifiable {
    let id: String
    let externalID: String?
    let start: Date
    let end: Date
    let allDay: Bool
    let title: String
    let calendarID: String
    let calendarName: String
    let accountName: String
    let color: CGColor
    let location: String?
    let notes: String?
    let url: URL?
    let attendees: [String]
    let organizer: String?
    let event: EKEvent?
}

struct EventGroup: Identifiable {
    let copies: [CalendarEvent]
    var id: String { copies[0].id }
    var event: CalendarEvent { copies[0] }
}

// Only the server's external identifier plus the occurrence's start time can
// establish a match. Missing identifiers never coalesce unrelated events.
func groupEvents(_ events: [CalendarEvent]) -> [EventGroup] {
    var groups: [EventGroup] = []
    var positions: [String: Int] = [:]
    for event in events.sorted(by: { ($0.start, $0.title, $0.id) < ($1.start, $1.title, $1.id) }) {
        guard let external = event.externalID, !external.isEmpty else {
            groups.append(EventGroup(copies: [event]))
            continue
        }
        let key = "\(external)\u{1f}\(event.start.timeIntervalSinceReferenceDate)"
        if let index = positions[key], !groups[index].copies.contains(where: { $0.calendarID == event.calendarID }) {
            groups[index] = EventGroup(copies: groups[index].copies + [event])
        } else {
            // Do not merge two distinct records within the same calendar.
            if positions[key] == nil { positions[key] = groups.count }
            groups.append(EventGroup(copies: [event]))
        }
    }
    return groups
}

func eventOverlapsDay(_ event: CalendarEvent, _ day: Date, calendar: Calendar = .current) -> Bool {
    let start = calendar.startOfDay(for: day)
    guard let end = calendar.date(byAdding: .day, value: 1, to: start) else { return false }
    // Zero-duration events still belong to their start day.
    return event.start < end && (event.end > start || (event.end == event.start && event.start >= start))
}

final class CalendarStore: ObservableObject {
    @Published var calendars: [EKCalendar] = []
    @Published var events: [CalendarEvent] = []
    @Published var status = "Loading calendars…"
    @Published var hiddenIDs: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "hiddenCalendarIDs") ?? [])
    private let store = EKEventStore()
    private var month = Date()

    init() {
        NotificationCenter.default.addObserver(forName: .EKEventStoreChanged, object: store, queue: .main) { [weak self] _ in
            self?.refresh()
        }
    }

    func usePreviewEvents() {
        let start = Calendar.current.startOfDay(for: Date()).addingTimeInterval(9.5 * 3600)
        events = (0..<8).map { index in
            let time = start.addingTimeInterval(Double(index) * 3600)
            return CalendarEvent(id: "sample-\(index)", externalID: nil, start: time, end: time.addingTimeInterval(2700), allDay: false, title: ["Research meeting", "Project work", "Study group"][index % 3], calendarID: "sample", calendarName: "Example calendar", accountName: "Example", color: NSColor.systemPurple.cgColor, location: "North Campus", notes: "Sample notes for testing.", url: nil, attendees: ["Alex Example"], organizer: nil, event: nil)
        }
        status = ""
    }

    func authorize() {
        switch EKEventStore.authorizationStatus(for: .event) {
        case .fullAccess:
            refresh()
        case .notDetermined:
            status = "Waiting for Calendar access…"
            store.requestFullAccessToEvents { [weak self] granted, _ in
                DispatchQueue.main.async {
                    if granted { self?.refresh() }
                    else { self?.status = "Calendar access is off. Enable it in System Settings → Privacy & Security → Calendars." }
                }
            }
        default:
            status = "Calendar access is off. Enable it in System Settings → Privacy & Security → Calendars."
        }
    }

    func show(month: Date) {
        self.month = month
        if EKEventStore.authorizationStatus(for: .event) == .fullAccess { refresh() }
    }

    func toggle(_ calendar: EKCalendar) {
        if hiddenIDs.contains(calendar.calendarIdentifier) { hiddenIDs.remove(calendar.calendarIdentifier) }
        else { hiddenIDs.insert(calendar.calendarIdentifier) }
        UserDefaults.standard.set(Array(hiddenIDs), forKey: "hiddenCalendarIDs")
    }

    func refresh() {
        guard EKEventStore.authorizationStatus(for: .event) == .fullAccess else { return }
        let systemCalendar = Calendar.current
        guard let interval = systemCalendar.dateInterval(of: .month, for: month),
              let start = systemCalendar.date(byAdding: .day, value: -7, to: interval.start),
              let end = systemCalendar.date(byAdding: .day, value: 7, to: interval.end) else { return }
        calendars = store.calendars(for: .event).sorted {
            ($0.source.title, $0.title, $0.calendarIdentifier) < ($1.source.title, $1.title, $1.calendarIdentifier)
        }
        let predicate = store.predicateForEvents(withStart: start, end: end, calendars: nil)
        events = store.events(matching: predicate).compactMap { event in
            guard let start = event.startDate, let end = event.endDate, let cal = event.calendar else { return nil }
            return CalendarEvent(id: "\(event.eventIdentifier ?? UUID().uuidString)|\(start.timeIntervalSinceReferenceDate)",
                                 externalID: event.calendarItemExternalIdentifier, start: start, end: end,
                                 allDay: event.isAllDay, title: event.title ?? "Untitled event",
                                 calendarID: cal.calendarIdentifier, calendarName: cal.title,
                                 accountName: cal.source.title, color: cal.cgColor,
                                 location: event.location, notes: event.notes, url: event.url,
                                 attendees: (event.attendees ?? []).map { $0.name ?? $0.url.absoluteString },
                                 organizer: event.organizer?.name, event: event)
        }
        status = calendars.isEmpty ? "No calendars found in Apple Calendar." : ""
    }

    func events(on day: Date) -> [EventGroup] {
        groupEvents(events.filter { !hiddenIDs.contains($0.calendarID) && eventOverlapsDay($0, day) })
    }
}
