// Render the vendored Raycast SVG at 2× for SketchyBar's 18-point image box.
import AppKit

let folder = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
guard let image = NSImage(contentsOf: folder.appendingPathComponent("mug.svg")),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 36, pixelsHigh: 36,
                                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                    isPlanar: false, colorSpaceName: .deviceRGB,
                                    bytesPerRow: 0, bitsPerPixel: 0),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fputs("Cannot load the Raycast mug SVG.\n", stderr)
    exit(1)
}
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.cgContext.clear(CGRect(x: 0, y: 0, width: 36, height: 36))
image.draw(in: NSRect(x: 0, y: 0, width: 36, height: 36))
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: 36, height: 36).fill(using: .sourceIn)
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(1) }
do {
    try png.write(to: folder.appendingPathComponent("mug.png"), options: .atomic)
} catch {
    fputs("Cannot save the Raycast mug PNG.\n", stderr)
    exit(1)
}
