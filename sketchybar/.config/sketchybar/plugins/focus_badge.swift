// Render a native SF Symbol inside the Focus picker's 24-point circular badge.
import AppKit

guard CommandLine.arguments.count == 3 else { exit(2) }
let parts = CommandLine.arguments[1].split(separator: "\t")
guard parts.count == 2, let rgba = UInt64(parts[1], radix: 16),
      let original = NSImage(systemSymbolName: String(parts[0]), accessibilityDescription: nil),
      let symbol = original.withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 28, weight: .medium)),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 48, pixelsHigh: 48,
                                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                    isPlanar: false, colorSpaceName: .deviceRGB,
                                    bytesPerRow: 0, bitsPerPixel: 0),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else { exit(1) }
let hasAlpha = parts[1].count == 8
let rgb = hasAlpha ? rgba >> 8 : rgba
let alpha = hasAlpha ? CGFloat(rgba & 255) / 255 : 1
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.cgContext.clear(CGRect(x: 0, y: 0, width: 48, height: 48))
// Tint the symbol before painting the badge, preserving its native antialiasing.
let scale = min(34 / symbol.size.width, 34 / symbol.size.height)
let size = NSSize(width: symbol.size.width * scale, height: symbol.size.height * scale)
symbol.draw(in: NSRect(x: (48 - size.width) / 2, y: (48 - size.height) / 2,
                      width: size.width, height: size.height))
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: 48, height: 48).fill(using: .sourceIn)
NSColor(srgbRed: CGFloat((rgb >> 16) & 255) / 255,
        green: CGFloat((rgb >> 8) & 255) / 255,
        blue: CGFloat(rgb & 255) / 255, alpha: alpha).setFill()
context.compositingOperation = .destinationOver
NSBezierPath(ovalIn: NSRect(x: 0, y: 0, width: 48, height: 48)).fill()
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(1) }
do {
    try png.write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .atomic)
} catch { exit(1) }
