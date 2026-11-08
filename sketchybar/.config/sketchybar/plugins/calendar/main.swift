import AppKit
import EventKit
import SwiftUI

private let calendarBackground = Color(red: 40/255, green: 42/255, blue: 54/255)
private let panelFill = Color(red: 54/255, green: 56/255, blue: 71/255)
private let foreground = Color(red: 248/255, green: 248/255, blue: 242/255)
private let subdued = Color(red: 177/255, green: 180/255, blue: 198/255)
private let purple = Color(red: 189/255, green: 147/255, blue: 249/255)
private let calendarFont = Font.custom("IBMPlexMono-Medium", size: 11)

final class CalendarPanel: NSPanel {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

final class CalendarController: NSObject, ObservableObject, NSApplicationDelegate, NSWindowDelegate {
    @Published var selectedDay = Calendar.current.startOfDay(for: Date())
    @Published var month = Calendar.current.dateInterval(of: .month, for: Date())!.start
    @Published var selectedEvent: EventGroup?
    @Published var pinned = false
    @Published var openMessage: String?
    let store = CalendarStore()
    private var panel: NSPanel!
    private var detail: NSPanel!
    private var clockRects: [CGRect] = []
    private var timer: Timer?
    private var outsideSince: Date?
    private var lastVisible = Date()
    private let directory = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Caches/sketchybar-calendar/native")

    func applicationDidFinishLaunching(_ notification: Notification) {
        try? FileManager.default.createDirectory(at: directory.appendingPathComponent("commands"), withIntermediateDirectories: true)
        if !CommandLine.arguments.contains("--preview") { try? String(ProcessInfo.processInfo.processIdentifier).write(to: directory.appendingPathComponent("pid"), atomically: true, encoding: .utf8) }
        panel = makePanel(width: 280, height: 350)
        panel.contentView = NSHostingView(rootView: CalendarView(controller: self, store: store))
        detail = makePanel(width: 270, height: 360)
        detail.contentView = NSHostingView(rootView: DetailView(controller: self))
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.keyCode == 53 { self?.hide(); return nil }
            return event
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.12, repeats: true) { [weak self] _ in self?.tick() }
        if CommandLine.arguments.contains("--preview") {
            store.usePreviewEvents()
            pinned = true
            if let screen = NSScreen.main {
                panel.setFrame(NSRect(x: screen.visibleFrame.maxX - 300, y: screen.visibleFrame.maxY - 520, width: 280, height: 500), display: true)
            }
            panel.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
        } else { tick() }
    }

    func applicationWillTerminate(_ notification: Notification) {
        if !CommandLine.arguments.contains("--preview") { try? FileManager.default.removeItem(at: directory.appendingPathComponent("pid")) }
    }

    private func makePanel(width: CGFloat, height: CGFloat) -> NSPanel {
        let window = CalendarPanel(contentRect: NSRect(x: 0, y: 0, width: width, height: height),
                             styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = true
        window.level = .popUpMenu
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window.hidesOnDeactivate = false
        window.delegate = self
        return window
    }

    private func updateClockRects() {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        task.arguments = [ProcessInfo.processInfo.environment["BAR_NAME"] ?? "sketchybar", "--query", "clock"]
        var environment = ProcessInfo.processInfo.environment
        environment["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + (environment["PATH"] ?? "/usr/bin:/bin")
        task.environment = environment
        let output = Pipe(); task.standardOutput = output; task.standardError = FileHandle.nullDevice
        do {
            try task.run()
            let data = output.fileHandleForReading.readDataToEndOfFile()
            task.waitUntilExit()
            guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let rectangles = json["bounding_rects"] as? [String: [String: [Double]]],
                  let mainHeight = NSScreen.screens.first?.frame.maxY else { return }
            clockRects = rectangles.values.compactMap { item in
                guard let o = item["origin"], let s = item["size"], o.count == 2, s.count == 2 else { return nil }
                return CGRect(x: o[0], y: mainHeight - o[1] - s[1], width: s[0], height: s[1])
            }
        } catch { clockRects = [] }
    }

    private func tick() {
        if CommandLine.arguments.contains("--preview") { return }
        let queue = directory.appendingPathComponent("commands")
        if let files = try? FileManager.default.contentsOfDirectory(at: queue, includingPropertiesForKeys: nil).sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
            for file in files where file.pathExtension == "cmd" {
                if let command = try? String(contentsOf: file, encoding: .utf8) { handle(command.trimmingCharacters(in: .whitespacesAndNewlines)) }
                try? FileManager.default.removeItem(at: file)
            }
        }
        guard panel.isVisible else {
            if Date().timeIntervalSince(lastVisible) > 120 { NSApp.terminate(nil) }
            return
        }
        lastVisible = Date()
        guard !pinned else { outsideSince = nil; return }
        let point = NSEvent.mouseLocation
        let inClock = clockRects.contains { $0.insetBy(dx: -3, dy: -3).contains(point) }
        let inside = inClock || panel.frame.insetBy(dx: -5, dy: -5).contains(point) || (detail.isVisible && detail.frame.insetBy(dx: -5, dy: -5).contains(point))
        if inside { outsideSince = nil }
        else if outsideSince == nil { outsideSince = Date() }
        else if Date().timeIntervalSince(outsideSince!) > 0.4 { hide() }
    }

    private func handle(_ action: String) {
        if action == "open" {
            guard !panel.isVisible else { return }
            updateClockRects()
            guard clockRects.contains(where: { $0.insetBy(dx: -3, dy: -3).contains(NSEvent.mouseLocation) }) else { return }
            pinned = false
            selectedEvent = nil
            selectedDay = Calendar.current.startOfDay(for: Date())
            month = Calendar.current.dateInterval(of: .month, for: selectedDay)!.start
            store.show(month: month)
            store.authorize()
            position()
            panel.orderFrontRegardless()
        } else if action == "toggle" {
            if panel.isVisible && pinned { hide(); return }
            if !panel.isVisible {
                updateClockRects()
                selectedDay = Calendar.current.startOfDay(for: Date())
                month = Calendar.current.dateInterval(of: .month, for: selectedDay)!.start
                store.show(month: month); store.authorize(); position(); panel.orderFrontRegardless()
            }
            pinned = true
            NSApp.activate(ignoringOtherApps: true)
            panel.makeKey()
        }
    }

    func hide() {
        pinned = false; selectedEvent = nil; outsideSince = nil
        panel.orderOut(nil); detail.orderOut(nil)
    }

    func changeMonth(_ offset: Int) {
        guard let date = Calendar.current.date(byAdding: .month, value: offset, to: month) else { return }
        month = date
        selectedDay = date
        selectedEvent = nil; detail.orderOut(nil); store.show(month: date); resize()
    }

    func today() {
        selectedDay = Calendar.current.startOfDay(for: Date())
        month = Calendar.current.dateInterval(of: .month, for: selectedDay)!.start
        selectedEvent = nil; detail.orderOut(nil); store.show(month: month); resize()
    }

    func choose(_ date: Date) {
        selectedDay = date; selectedEvent = nil; detail.orderOut(nil); resize()
    }

    func show(_ group: EventGroup) {
        selectedEvent = group
        openMessage = nil
        positionDetail()
        NSApp.activate(ignoringOtherApps: true)
        detail.makeKeyAndOrderFront(nil)
        detail.orderFrontRegardless()
    }

    func closeDetail() { selectedEvent = nil; detail.orderOut(nil) }

    func resize() {
        guard panel != nil, panel.isVisible else { return }
        let count = store.events(on: selectedDay).count
        let wanted = min(500, max(306, 294 + CGFloat(max(1, count)) * 43))
        let screen = NSScreen.screens.first(where: { $0.frame.contains(NSPoint(x: panel.frame.midX, y: panel.frame.midY)) }) ?? NSScreen.main
        let available = max(180, (screen?.visibleFrame.height ?? wanted) - 12)
        let height = min(wanted, available)
        var frame = panel.frame
        frame.origin.y += frame.height - height; frame.size.height = height
        panel.setFrame(frame, display: true)
        if detail.isVisible { positionDetail() }
    }

    private func position() {
        let pointer = NSEvent.mouseLocation
        let anchor = clockRects.first(where: { $0.insetBy(dx: -3, dy: -3).contains(pointer) }) ?? clockRects.first
        guard let rect = anchor else { return }
        let screen = NSScreen.screens.first(where: { $0.frame.contains(NSPoint(x: rect.midX, y: rect.midY)) }) ?? NSScreen.main
        let visible = screen?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
        let count = store.events(on: selectedDay).count
        let height = min(500, max(306, 294 + CGFloat(max(1, count)) * 43), visible.height - 12)
        let x = min(max(rect.maxX - 280, visible.minX), visible.maxX - 280)
        panel.setFrame(NSRect(x: x, y: max(visible.minY, rect.minY - height - 3), width: 280, height: height), display: true)
    }

    private func positionDetail() {
        let screen = NSScreen.screens.first(where: { $0.frame.contains(NSPoint(x: panel.frame.midX, y: panel.frame.midY)) }) ?? NSScreen.main
        let visible = screen?.visibleFrame ?? panel.frame
        let height = min(500, visible.height - 12)
        let preferred = panel.frame.minX - 276
        let x = preferred >= visible.minX ? preferred : min(panel.frame.maxX + 6, visible.maxX - 270)
        let y = max(visible.minY, min(panel.frame.maxY - height, visible.maxY - height))
        detail.setFrame(NSRect(x: x, y: y, width: 270, height: height), display: true)
    }

    func openInCalendar(_ event: CalendarEvent) {
        func quote(_ value: String) -> String {
            "\"" + value.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"").replacingOccurrences(of: "\n", with: " ").replacingOccurrences(of: "\r", with: " ") + "\""
        }
        if let uid = event.externalID, !uid.isEmpty {
            let source = "tell application \"Calendar\" to show (event id \(quote(uid)) of calendar id \(quote(event.calendarID)))"
            if let script = NSAppleScript(source: source) {
                var error: NSDictionary?
                script.executeAndReturnError(&error)
                if error == nil { return }
            }
        }
        let seconds = Int(event.start.timeIntervalSinceReferenceDate)
        if let url = URL(string: "calshow:\(seconds)") { NSWorkspace.shared.open(url) }
        openMessage = "Opened the date. Calendar could not open this event directly."
    }
}

private struct CalendarView: View {
    @ObservedObject var controller: CalendarController
    @ObservedObject var store: CalendarStore
    let calendar = Calendar.current
    private let columns = [GridItem(.fixed(24), spacing: 0)] + Array(repeating: GridItem(.flexible(), spacing: 0), count: 7)
    private var dates: [Date?] {
        let start = controller.month
        let count = calendar.range(of: .day, in: .month, for: start)?.count ?? 30
        let offset = calendar.component(.weekday, from: start) - 1
        return (0..<42).map { i in
            let day = i - offset
            return (0..<count).contains(day) ? calendar.date(byAdding: .day, value: day, to: start) : nil
        }
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 4) {
                Button("‹") { controller.changeMonth(-1) }.frame(width: 25)
                Button(controller.month.formatted(.dateTime.month(.wide).year())) { controller.today() }.frame(maxWidth: .infinity)
                Button("›") { controller.changeMonth(1) }.frame(width: 25)
                Menu {
                    if store.calendars.isEmpty { Text("No calendars") }
                    ForEach(store.calendars, id: \.calendarIdentifier) { cal in
                        Button { store.toggle(cal); controller.resize() } label: {
                            Label("\(cal.title) · \(cal.source.title)", systemImage: store.hiddenIDs.contains(cal.calendarIdentifier) ? "circle" : "checkmark.circle.fill")
                        }
                    }
                } label: { Image(systemName: "line.3.horizontal.decrease.circle") }.menuStyle(.borderlessButton).frame(width: 25)
                .help("Choose calendars")
            }.buttonStyle(CalendarButton())
            LazyVGrid(columns: columns, spacing: 0) {
                ForEach(["W", "Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"], id: \.self) { Text($0).foregroundColor(subdued).frame(height: 25) }
                ForEach(0..<6, id: \.self) { row in
                    let offset = calendar.component(.weekday, from: controller.month) - 1
                    let thursday = calendar.date(byAdding: .day, value: row * 7 + 4 - offset, to: controller.month)!
                    Text(String(format: "%02d", Calendar(identifier: .iso8601).component(.weekOfYear, from: thursday)))
                        .foregroundColor(subdued).frame(height: 27)
                    ForEach(0..<7, id: \.self) { column in
                        if let day = dates[row * 7 + column] {
                            Button { controller.choose(day) } label: {
                                VStack(spacing: 0) {
                                    Text("\(calendar.component(.day, from: day))")
                                    Circle().fill(store.events(on: day).isEmpty ? .clear : purple).frame(width: 3, height: 3)
                                }.frame(maxWidth: .infinity).frame(height: 27)
                                    .background(calendar.isDate(day, inSameDayAs: controller.selectedDay) ? purple.opacity(0.22) : .clear)
                                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(calendar.isDateInToday(day) ? purple : .clear))
                            }.buttonStyle(.plain)
                        } else { Color.clear.frame(height: 27) }
                    }
                }
            }
            Divider().overlay(subdued.opacity(0.25)).padding(.vertical, 5)
            HStack {
                Text(controller.selectedDay.formatted(.dateTime.weekday(.wide).month(.abbreviated).day())).fontWeight(.semibold)
                Spacer()
                if controller.pinned { Image(systemName: "pin.fill").foregroundColor(subdued).help("Pinned") }
            }.padding(.bottom, 4)
            if !store.status.isEmpty {
                Text(store.status).foregroundColor(subdued).frame(maxWidth: .infinity, alignment: .leading).fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 0)
            } else {
                let events = store.events(on: controller.selectedDay)
                if events.isEmpty { Text("No events").foregroundColor(subdued).frame(maxWidth: .infinity, alignment: .leading); Spacer(minLength: 0) }
                else {
                    ScrollView {
                        LazyVStack(spacing: 2) {
                            ForEach(events) { group in
                                Button { controller.show(group) } label: { EventRow(group: group) }.buttonStyle(.plain)
                            }
                        }
                    }
                }
            }
        }
        .padding(11).font(calendarFont).foregroundColor(foreground)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(calendarBackground).clipShape(RoundedRectangle(cornerRadius: 12))
        .onReceive(store.$events) { _ in DispatchQueue.main.async { controller.resize() } }
    }
}

private struct EventRow: View {
    let group: EventGroup
    var body: some View {
        HStack(alignment: .top, spacing: 7) {
            Text(group.event.allDay ? "All day" : group.event.start.formatted(date: .omitted, time: .shortened))
                .foregroundColor(subdued).frame(width: 64, alignment: .leading)
            RoundedRectangle(cornerRadius: 1).fill(Color(cgColor: group.event.color)).frame(width: 3)
            VStack(alignment: .leading, spacing: 2) {
                Text(group.event.title).lineLimit(2).frame(maxWidth: .infinity, alignment: .leading)
                Text(group.copies.map(\.calendarName).joined(separator: ", ")).foregroundColor(subdued).lineLimit(1)
            }
        }.padding(.vertical, 4).frame(minHeight: 40, alignment: .top).contentShape(Rectangle())
    }
}

private struct CalendarButton: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.padding(.vertical, 5).background(panelFill.opacity(configuration.isPressed ? 0.5 : 1)).cornerRadius(4)
    }
}

private struct DetailView: View {
    @ObservedObject var controller: CalendarController
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                Text(controller.selectedEvent?.event.title ?? "Event").font(.custom("IBMPlexMono-Medium", size: 13)).textSelection(.enabled)
                Spacer()
                Button("×") { controller.closeDetail() }.buttonStyle(.plain).font(.system(size: 18))
            }
            if let group = controller.selectedEvent {
                let event = group.event
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        field("Time", event.allDay ? "All day · \(event.start.formatted(date: .abbreviated, time: .omitted))" : "\(event.start.formatted(date: .abbreviated, time: .shortened)) – \(event.end.formatted(date: .abbreviated, time: .shortened))")
                        field("Calendars", group.copies.map { "\($0.calendarName) · \($0.accountName)" }.joined(separator: "\n"))
                        if let value = event.location, !value.isEmpty { field("Location", value) }
                        if let value = event.organizer, !value.isEmpty { field("Organizer", value) }
                        if !event.attendees.isEmpty { field("Attendees", event.attendees.joined(separator: "\n")) }
                        if let value = event.notes, !value.isEmpty { field("Notes", value) }
                        if let url = event.url { Link(url.absoluteString, destination: url).textSelection(.enabled) }
                        ForEach(eventLinks(event), id: \.absoluteString) { url in
                            Link(url.absoluteString, destination: url).textSelection(.enabled)
                        }
                        if let alarms = event.event?.alarms, !alarms.isEmpty {
                            field("Alerts", alarms.map { alarm in
                                if let date = alarm.absoluteDate { return date.formatted(date: .abbreviated, time: .shortened) }
                                return "\(Int(alarm.relativeOffset / 60)) minutes from start"
                            }.joined(separator: "\n"))
                        }
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }
                if let message = controller.openMessage { Text(message).foregroundColor(subdued).fixedSize(horizontal: false, vertical: true) }
                Button("Open in Apple Calendar ↗") { controller.openInCalendar(event) }.buttonStyle(CalendarButton())
            } else { Spacer() }
        }.padding(12).font(calendarFont).foregroundColor(foreground)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .background(calendarBackground).clipShape(RoundedRectangle(cornerRadius: 12))
    }
    func eventLinks(_ event: CalendarEvent) -> [URL] {
        let text = [event.location, event.notes].compactMap { $0 }.joined(separator: "\n")
        guard let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue) else { return [] }
        let range = NSRange(text.startIndex..., in: text)
        var seen = Set<String>()
        return detector.matches(in: text, range: range).compactMap { $0.url }.filter {
            ["http", "https"].contains($0.scheme?.lowercased() ?? "") && $0 != event.url && seen.insert($0.absoluteString).inserted
        }
    }
    func field(_ name: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(name).foregroundColor(subdued)
            Text(value).textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
        }
    }
}

let application = NSApplication.shared
let controller = CalendarController()
application.delegate = controller
application.setActivationPolicy(.accessory)
application.run()
