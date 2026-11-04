import AppKit

if CommandLine.arguments.count == 2 && CommandLine.arguments[1] == "pointer" {
    let point = CGEvent(source: nil)!.location
    print("\(point.x) \(point.y)")
    exit(0)
}
if CommandLine.arguments.count == 2 && CommandLine.arguments[1] == "track" {
    while let point = CGEvent(source: nil)?.location {
        let pressed = CGEventSource.buttonState(.combinedSessionState, button: .left)
        print("\(point.x) \(point.y) \(pressed ? 1 : 0)")
        fflush(stdout)
        Thread.sleep(forTimeInterval: 0.035)
    }
    exit(0)
}
let data = Data(CommandLine.arguments[1].utf8)
let model = try JSONSerialization.jsonObject(with: data) as! [String: Any]
let weeks = model["weeks"] as! [[Int]]
let numbers = model["numbers"] as! [Int]
let today = model["today"] as! Int
let height = 246
let hover = model["hover"] as? Int ?? 0
let pressed = model["pressed"] as? Bool ?? false
let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 560, pixelsHigh: height * 2,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
let context = NSGraphicsContext.current!.cgContext
context.scaleBy(x: 2, y: 2)
func color(_ hex: Int) -> NSColor {
    NSColor(srgbRed: CGFloat((hex >> 16) & 255) / 255,
            green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255, alpha: 1)
}
func text(_ value: String, _ x: CGFloat, _ top: CGFloat, _ width: CGFloat,
          _ size: CGFloat = 11, _ tint: Int = 0xf8f8f2) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .center
    let attributes: [NSAttributedString.Key: Any] = [
        .font: NSFont(name: "IBMPlexMono-Medium", size: size) ?? NSFont.monospacedSystemFont(ofSize: size, weight: .medium),
        .foregroundColor: color(tint), .paragraphStyle: paragraph]
    (value as NSString).draw(in: NSRect(x: x, y: CGFloat(height) - top - 19, width: width, height: 19), withAttributes: attributes)
}
color(0x282a36).setFill()
NSBezierPath(roundedRect: NSRect(x: 0, y: 0, width: 280, height: height), xRadius: 12, yRadius: 12).fill()
for (index, button) in [(12, 26, "‹", 18), (42, 196, model["title"] as! String, 12), (242, 26, "›", 18)].enumerated() {
    let (x, width, label, size) = button
    let active = hover == index + 1
    let inset = active && pressed
    color(active ? (inset ? 0x20222d : 0x444655) : 0x30323f).setFill()
    NSBezierPath(roundedRect: NSRect(x: x, y: height - 39 - (inset ? 1 : 0), width: width, height: 28),
                 xRadius: 5, yRadius: 5).fill()
    text(label, CGFloat(x), CGFloat((index == 1 ? 17 : 13) + (inset ? 1 : 0)), CGFloat(width), CGFloat(size))
}
text("W", 12, 49, 28, 10, 0xa0a3b7)
let weekdays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
for column in 0..<7 { text(weekdays[column], CGFloat(44 + column * 32), 49, 28, 11, 0xb1b4c6) }
color(0x626579).setFill()
NSRect(x: 40, y: 12, width: 1, height: height - 58).fill()
for (row, days) in weeks.enumerated() {
    let top = CGFloat(77 + row * 28)
    text(String(format: "%02d", numbers[row]), 12, top, 28, 10, 0xa0a3b7)
    for (column, day) in days.enumerated() where day != 0 {
        let x = CGFloat(44 + column * 32)
        if hover == day + 3 {
            color(day == today ? 0x463950 : 0x3a3c4b).setFill()
            NSBezierPath(roundedRect: NSRect(x: x + 1, y: CGFloat(height) - top - 20, width: 26, height: 25),
                         xRadius: 5, yRadius: 5).fill()
        }
        if day == today {
            color(0xbd93f9).setStroke()
            let outline = NSBezierPath(roundedRect: NSRect(x: x + 1, y: CGFloat(height) - top - 20, width: 26, height: 25), xRadius: 5, yRadius: 5)
            outline.lineWidth = 1
            outline.stroke()
        }
        text(String(day), x, top, 28, 11, day == today ? 0xbd93f9 : 0xf8f8f2)
    }
}
NSGraphicsContext.restoreGraphicsState()
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .atomic)
