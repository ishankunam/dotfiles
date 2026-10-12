// Normalize the configured Focus icon supplied by Apple's Shortcuts action.
import AppKit

guard CommandLine.arguments.count == 3,
      let data = try? Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])),
      let original = NSBitmapImageRep(data: data),
      let cgImage = original.cgImage else { exit(1) }
var minX = original.pixelsWide, minY = original.pixelsHigh, maxX = -1, maxY = -1
for y in 0..<original.pixelsHigh {
    for x in 0..<original.pixelsWide {
        if (original.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0 {
            minX = min(minX, x); minY = min(minY, y)
            maxX = max(maxX, x); maxY = max(maxY, y)
        }
    }
}
guard maxX >= minX, maxY >= minY,
      let cropped = cgImage.cropping(to: CGRect(x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1)),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 36, pixelsHigh: 36,
                                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                    isPlanar: false, colorSpaceName: .deviceRGB,
                                    bytesPerRow: 0, bitsPerPixel: 0),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else { exit(1) }
let symbol = NSImage(cgImage: cropped, size: NSSize(width: cropped.width, height: cropped.height))
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.cgContext.clear(CGRect(x: 0, y: 0, width: 36, height: 36))
let scale = min(30 / symbol.size.width, 30 / symbol.size.height)
let size = NSSize(width: symbol.size.width * scale, height: symbol.size.height * scale)
symbol.draw(in: NSRect(x: (36 - size.width) / 2, y: (36 - size.height) / 2,
                      width: size.width, height: size.height))
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: 36, height: 36).fill(using: .sourceIn)
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(1) }
do {
    try png.write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .atomic)
} catch { exit(1) }
