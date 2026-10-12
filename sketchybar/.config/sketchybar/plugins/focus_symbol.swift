// Render an actual macOS SF Symbol as a transparent PNG for SketchyBar.
// NSImage(systemSymbolName:) is available on macOS 11 and later.
import AppKit

guard CommandLine.arguments.count == 3 else {
    fputs("Usage: focus_symbol.swift SYMBOL OUTPUT.png\n", stderr)
    exit(2)
}
let symbolName = CommandLine.arguments[1]
let destination = URL(fileURLWithPath: CommandLine.arguments[2])
guard let original = NSImage(systemSymbolName: symbolName, accessibilityDescription: nil),
      let symbol = original.withSymbolConfiguration(NSImage.SymbolConfiguration(pointSize: 28, weight: .medium)),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 36, pixelsHigh: 36,
                                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                    isPlanar: false, colorSpaceName: .deviceRGB,
                                    bytesPerRow: 0, bitsPerPixel: 0),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fputs("Cannot render the requested SF Symbol.\n", stderr)
    exit(1)
}
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.cgContext.clear(CGRect(x: 0, y: 0, width: 36, height: 36))
let scale = min(30 / symbol.size.width, 30 / symbol.size.height)
let size = NSSize(width: symbol.size.width * scale, height: symbol.size.height * scale)
symbol.draw(in: NSRect(x: (36 - size.width) / 2, y: (36 - size.height) / 2,
                      width: size.width, height: size.height))
// Keep the rendered alpha channel and use a fixed white foreground.
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: 36, height: 36).fill(using: .sourceIn)
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(1) }
do {
    try png.write(to: destination, options: .atomic)
} catch {
    fputs("Cannot save the SF Symbol image.\n", stderr)
    exit(1)
}
