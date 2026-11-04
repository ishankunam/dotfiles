import AppKit
import ApplicationServices

func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return nil }
    return value
}

func children(_ element: AXUIElement) -> [AXUIElement] {
    attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? []
}

final class MenuController: NSObject, NSApplicationDelegate, NSMenuDelegate {
    var target: NSRunningApplication?
    var sources: [ObjectIdentifier: AXUIElement] = [:]
    var selected: AXUIElement?

    func applicationDidFinishLaunching(_ notification: Notification) {
        target = NSWorkspace.shared.frontmostApplication
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
        guard AXIsProcessTrustedWithOptions(options) else {
            let alert = NSAlert()
            alert.messageText = "Allow App Menu to access application menus"
            alert.informativeText = "Enable SketchyBar App Menu in System Settings → Privacy & Security → Accessibility, then click the app pill again."
            alert.addButton(withTitle: "Open Accessibility Settings")
            alert.addButton(withTitle: "Later")
            NSApp.activate(ignoringOtherApps: true)
            if alert.runModal() == .alertFirstButtonReturn {
                NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!)
            }
            NSApp.terminate(nil)
            return
        }
        guard let target,
              let value = attribute(AXUIElementCreateApplication(target.processIdentifier), kAXMenuBarAttribute),
              CFGetTypeID(value) == AXUIElementGetTypeID() else {
            showError("This application does not expose its menu bar.")
            return
        }
        let menuBar = unsafeBitCast(value, to: AXUIElement.self)
        let menu = NSMenu()
        menu.autoenablesItems = false
        menu.appearance = NSAppearance(named: .darkAqua)
        menu.font = NSFont.systemFont(ofSize: 14)
        // macOS puts the system Apple menu before the app's own menu.
        populate(menu, from: children(menuBar).dropFirst())
        guard !menu.items.isEmpty else {
            showError("No application menus are available.")
            return
        }
        let location = anchor()
        NSApp.activate(ignoringOtherApps: true)
        menu.popUp(positioning: nil, at: location, in: nil)
        if let selected {
            target.activate(options: [])
            let result = AXUIElementPerformAction(selected, kAXPressAction as CFString)
            if result != .success {
                showError("The application could not perform this command. Open its menu and try again.")
                return
            }
        }
        NSApp.terminate(nil)
    }

    func showError(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "App menu unavailable"
        alert.informativeText = message
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
        NSApp.terminate(nil)
    }

    func populate(_ menu: NSMenu, from elements: ArraySlice<AXUIElement>) {
        menu.removeAllItems()
        for element in elements {
            let title = attribute(element, kAXTitleAttribute) as? String ?? ""
            if title.isEmpty {
                menu.addItem(.separator())
                continue
            }
            let item = NSMenuItem(title: title, action: #selector(invoke(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = element
            item.isEnabled = attribute(element, kAXEnabledAttribute) as? Bool ?? true
            if let mark = attribute(element, kAXMenuItemMarkCharAttribute) as? String, !mark.isEmpty {
                item.state = .on
            }
            if let child = children(element).first(where: { attribute($0, kAXRoleAttribute) as? String == kAXMenuRole }) {
                let submenu = NSMenu(title: title)
                submenu.autoenablesItems = false
                submenu.delegate = self
                sources[ObjectIdentifier(submenu)] = child
                // A placeholder makes the cascade available before its lazy update.
                submenu.addItem(NSMenuItem(title: "Loading…", action: nil, keyEquivalent: ""))
                item.submenu = submenu
            } else if let key = attribute(element, kAXMenuItemCmdCharAttribute) as? String, !key.isEmpty {
                item.keyEquivalent = key.lowercased()
                let modifiers = attribute(element, kAXMenuItemCmdModifiersAttribute) as? Int ?? 0
                var flags: NSEvent.ModifierFlags = []
                if modifiers & 8 == 0 { flags.insert(.command) }
                if modifiers & 1 != 0 { flags.insert(.shift) }
                if modifiers & 2 != 0 { flags.insert(.option) }
                if modifiers & 4 != 0 { flags.insert(.control) }
                item.keyEquivalentModifierMask = flags
            }
            menu.addItem(item)
        }
    }

    func menuNeedsUpdate(_ menu: NSMenu) {
        guard let source = sources[ObjectIdentifier(menu)] else { return }
        populate(menu, from: children(source)[...])
        if menu.items.isEmpty {
            let unavailable = NSMenuItem(title: "No commands available", action: nil, keyEquivalent: "")
            unavailable.isEnabled = false
            menu.addItem(unavailable)
        }
    }

    @objc func invoke(_ sender: NSMenuItem) {
        selected = sender.representedObject as! AXUIElement?
    }

    func anchor() -> NSPoint {
        let mouse = NSEvent.mouseLocation
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/homebrew/bin/sketchybar")
        process.arguments = ["--query", "front_app"]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        guard (try? process.run()) != nil else { return mouse }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let rects = json["bounding_rects"] as? [String: [String: Any]],
              let primary = NSScreen.screens.first else { return mouse }
        for rect in rects.values {
            guard let origin = rect["origin"] as? [Double], origin.count == 2,
                  let size = rect["size"] as? [Double], size.count == 2 else { continue }
            let bounds = NSRect(x: origin[0], y: primary.frame.maxY - origin[1] - size[1], width: size[0], height: size[1])
            if bounds.insetBy(dx: -12, dy: -8).contains(mouse) {
                return NSPoint(x: bounds.minX, y: bounds.minY - 4)
            }
        }
        return mouse
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let controller = MenuController()
app.delegate = controller
app.run()
