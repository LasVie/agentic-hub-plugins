import CoreGraphics
import CryptoKit
import Foundation
import ImageIO
import UniformTypeIdentifiers
import Vision

let version = "1.0.0"
let fileLimit = 32 * 1024 * 1024
let countLimit = 12

struct Failure: Error {
    let message: String
    init(_ message: String) { self.message = message }
}

func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw Failure(message) }
}

struct Box: Codable, Equatable {
    let x: Int
    let y: Int
    let w: Int
    let h: Int

    func valid(_ width: Int, _ height: Int) -> Bool {
        x >= 0 && y >= 0 && x < width && y < height && w > 0 && h > 0 && w <= width - x && h <= height - y
    }
    func contains(_ b: Box) -> Bool {
        x <= b.x && y <= b.y && x + w >= b.x + b.w && y + h >= b.y + b.h
    }
    func intersects(_ b: Box) -> Bool {
        x < b.x + b.w && b.x < x + w && y < b.y + b.h && b.y < y + h
    }
}

struct Suggestion: Codable, Equatable {
    let kind: String
    let box: Box
}
struct ScanImage: Codable {
    let id: String
    let sha256: String
    let width: Int
    let height: Int
    let suggestions: [Suggestion]
}
struct Scan: Codable {
    let version: String
    let images: [ScanImage]
}
struct PlanImage: Codable {
    let id: String
    let disposition: String
    let masks: [Box]
    let keep: [Box]
    let dismissed: [Int]
}
struct Plan: Codable {
    let version: String
    let scanSHA256: String
    let images: [PlanImage]
}
struct Audit: Codable, Equatable {
    let version: String
    let scanSHA256: String
    let planSHA256: String
    let filesSHA256: [String: String]
    let held: [String]
}

func sha(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

func bounded(_ url: URL, limit: Int = fileLimit) throws -> Data {
    let props = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
    try expect(props.isRegularFile == true && props.isSymbolicLink != true, "输入必须是普通文件")
    let handle = try FileHandle(forReadingFrom: url)
    defer { try? handle.close() }
    let data = try handle.read(upToCount: limit + 1) ?? Data()
    try expect(!data.isEmpty && data.count <= limit, "文件为空或超过体积限制")
    return data
}

func json<T: Encodable>(_ value: T) throws -> Data {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys, .prettyPrinted, .withoutEscapingSlashes]
    return try encoder.encode(value) + Data([10])
}
func save(_ data: Data, _ url: URL) throws {
    try data.write(to: url, options: [.withoutOverwriting])
}
func freshDirectory(_ url: URL) throws {
    try FileManager.default.createDirectory(at: url, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
}

let pngSignature: [UInt8] = [137, 80, 78, 71, 13, 10, 26, 10]

func image(_ data: Data) throws -> CGImage {
    try expect(data.starts(with: pngSignature), "只支持静态 PNG")
    guard let source = CGImageSourceCreateWithData(data as CFData, nil),
          CGImageSourceGetType(source) as String? == UTType.png.identifier,
          CGImageSourceGetCount(source) == 1,
          let props = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
          let w = props[kCGImagePropertyPixelWidth] as? Int,
          let h = props[kCGImagePropertyPixelHeight] as? Int else {
        throw Failure("无法读取 PNG")
    }
    try expect(w > 0 && h > 0 && w <= 6000 && h <= 6000 && w * h <= 16_000_000, "截图尺寸超过限制")
    try expect(props[kCGImagePropertyOrientation] as? Int ?? 1 == 1, "截图方向必须是正常方向，请先在本机另存")
    guard let decoded = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw Failure("无法解码 PNG")
    }
    return decoded
}

func sourceFiles(_ dir: URL) throws -> [URL] {
    let props = try dir.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
    try expect(props.isDirectory == true && props.isSymbolicLink != true, "需要一个普通截图目录")
    let items = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil, options: [.skipsHiddenFiles])
        .filter { $0.pathExtension.lowercased() == "png" }
        .sorted { Array($0.lastPathComponent.utf8).lexicographicallyPrecedes(Array($1.lastPathComponent.utf8)) }
    try expect(!items.isEmpty && items.count <= countLimit, "请输入 1 至 12 张 PNG")
    return items
}
func imageID(_ index: Int) -> String { String(format: "image-%02d", index + 1) }

let patterns: [String: String] = [
    "email": #"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}"#,
    "phone": #"(?<![0-9])(?:\+?[0-9][0-9() .\-]{5,20}[0-9])(?![0-9])"#,
    "url": #"https?://[^\s<>]+"#,
    "account": #"(?:账号|帐户|账户|用户\s*ID|账户\s*ID|account\s*ID|user\s*ID)\s*[:：#]?\s*[A-Z0-9][A-Z0-9_\-]{2,}"#,
]

func pixelBox(_ r: CGRect, _ w: Int, _ h: Int) -> Box? {
    guard !r.isNull, !r.isInfinite, [r.minX,r.maxX,r.minY,r.maxY].allSatisfy({ $0.isFinite }) else { return nil }
    func unit(_ v: CGFloat) -> Double { max(0.0, min(1.0, Double(v))) }
    let leftPixel = unit(r.minX) * Double(w)
    let topPixel = (1.0 - unit(r.maxY)) * Double(h)
    let rightPixel = unit(r.maxX) * Double(w)
    let bottomPixel = (1.0 - unit(r.minY)) * Double(h)
    let x = max(0, Int(floor(leftPixel)) - 3)
    let y = max(0, Int(floor(topPixel)) - 3)
    let right = min(w, Int(ceil(rightPixel)) + 3)
    let bottom = min(h, Int(ceil(bottomPixel)) + 3)
    return right > x && bottom > y ? Box(x:x,y:y,w:right-x,h:bottom-y) : nil
}

func suggest(_ decoded: CGImage, _ categories: [String]) throws -> [Suggestion] {
    if categories.isEmpty { return [] }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    let available = try request.supportedRecognitionLanguages()
    request.recognitionLanguages = ["zh-Hans", "en-US"].filter(available.contains)
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: decoded, options: [:]).perform([request])
    let rules = try categories.map { kind in
        (kind, try NSRegularExpression(pattern: patterns[kind]!, options: .caseInsensitive))
    }
    var result: [Suggestion] = []
    for observation in request.results ?? [] {
        guard let text = observation.topCandidates(1).first else { continue }
        let line = text.string
        for (kind, rule) in rules {
            for match in rule.matches(in: line, range: NSRange(line.startIndex..., in: line)) {
                guard let range = Range(match.range, in: line) else { continue }
                let area = (try? text.boundingBox(for: range))?.boundingBox ?? observation.boundingBox
                if let box = pixelBox(area, decoded.width, decoded.height) {
                    result.append(Suggestion(kind: kind, box: box))
                }
            }
        }
    }
    try expect(result.count <= 200, "单张建议框过多，请缩小截图范围")
    return result.sorted { ($0.box.y, $0.box.x, $0.kind) < ($1.box.y, $1.box.x, $1.kind) }
}

struct Raster {
    let width: Int
    let height: Int
    var bytes: [UInt8]

    init(_ decoded: CGImage) throws {
        width = decoded.width
        height = decoded.height
        let w = width, h = height
        bytes = [UInt8](repeating: 255, count: w * h * 4)
        try bytes.withUnsafeMutableBytes { storage in
            guard let ctx = CGContext(data: storage.baseAddress, width: w, height: h, bitsPerComponent: 8,
                                      bytesPerRow: w * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                      bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue) else {
                throw Failure("无法初始化像素缓冲区")
            }
            ctx.setFillColor(red: 1, green: 1, blue: 1, alpha: 1)
            ctx.fill(CGRect(x:0,y:0,width:w,height:h))
            ctx.draw(decoded, in: CGRect(x:0,y:0,width:w,height:h))
        }
    }
    mutating func cover(_ boxes: [Box]) {
        for b in boxes {
            for row in b.y ..< b.y + b.h {
                for column in b.x ..< b.x + b.w {
                    let pixel = (row * width + column) * 4
                    bytes[pixel] = 0
                    bytes[pixel + 1] = 0
                    bytes[pixel + 2] = 0
                }
            }
        }
    }
    func png() throws -> Data {
        let format = CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue)
        guard let provider = CGDataProvider(data: Data(bytes) as CFData),
              let pic = CGImage(width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 32,
                                bytesPerRow: width * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                bitmapInfo: format, provider: provider, decode: nil,
                                shouldInterpolate: false, intent: .defaultIntent) else {
            throw Failure("无法生成扁平图像")
        }
        let out = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(out, UTType.png.identifier as CFString, 1, nil) else {
            throw Failure("无法创建 PNG")
        }
        CGImageDestinationAddImage(destination, pic, nil)
        try expect(CGImageDestinationFinalize(destination), "无法写出 PNG")
        return try pngChunks(out as Data, strip: true)
    }
}

func pngChunks(_ data: Data, strip: Bool) throws -> Data {
    try expect(data.starts(with: pngSignature), "候选不是 PNG")
    let bytes = [UInt8](data)
    var offset = 8
    var result = Data(pngSignature)
    var hasHeader = false, hasPixels = false, ended = false
    while offset + 12 <= bytes.count {
        let size = bytes[offset..<offset+4].reduce(0) { ($0 << 8) | Int($1) }
        let end = offset + 12 + size
        try expect(end <= bytes.count, "候选 PNG 数据块损坏")
        let kind = String(decoding: bytes[offset+4..<offset+8], as: UTF8.self)
        if !hasHeader {
            try expect(kind == "IHDR" && size == 13 && bytes[offset+16] == 8 && bytes[offset+17] == 2,
                       "候选必须为不透明的 8 位 RGB PNG")
            hasHeader = true
        } else if kind == "IHDR" {
            throw Failure("候选 PNG 表头重复")
        }
        if kind == "IDAT" { hasPixels = true }
        if ["IHDR","IDAT","IEND"].contains(kind) {
            result.append(contentsOf: bytes[offset..<end])
        } else if !strip || bytes[offset+4] & 32 == 0 {
            throw Failure("候选 PNG 包含额外数据块")
        }
        offset = end
        if kind == "IEND" {
            try expect(size == 0 && hasPixels && offset == bytes.count, "候选 PNG 结尾无效")
            ended = true
            break
        }
    }
    try expect(ended, "候选 PNG 不完整")
    return result
}

func checkPixels(_ source: Raster, _ output: Raster, _ boxes: [Box]) throws {
    try expect(source.width == output.width && source.height == output.height, "候选尺寸变化")
    for y in 0..<source.height {
        let intervals = boxes.filter { $0.y <= y && y < $0.y + $0.h }
            .map { ($0.x, $0.x + $0.w) }.sorted { $0.0 < $1.0 }
        var interval = 0
        var coveredUntil = 0
        for x in 0..<source.width {
            while interval < intervals.count && intervals[interval].0 <= x {
                coveredUntil = max(coveredUntil, intervals[interval].1)
                interval += 1
            }
            let i = (y * source.width + x) * 4
            let a = output.bytes[i], b = output.bytes[i + 1], c = output.bytes[i + 2]
            if x < coveredUntil {
                if a != 0 || b != 0 || c != 0 { throw Failure("候选有未完整覆盖的像素") }
            } else if a != source.bytes[i] || b != source.bytes[i + 1] || c != source.bytes[i + 2] {
                throw Failure("候选改变了确认框之外的像素")
            }
        }
    }
}

func checkPlan(_ item: PlanImage, _ scan: ScanImage) throws {
    try expect(item.id == scan.id && ["approved","held"].contains(item.disposition), "确认清单编号或状态无效")
    try expect(item.masks.count <= 200 && item.keep.count <= 200
               && (item.masks + item.keep).allSatisfy({ $0.valid(scan.width, scan.height) }),
               "区域坐标无效或超出截图边界")
    let ignored = Set(item.dismissed)
    try expect(ignored.count == item.dismissed.count && ignored.allSatisfy(scan.suggestions.indices.contains),
               "忽略的建议编号无效")
    if item.disposition == "approved" {
        try expect(!item.masks.contains(where: { m in item.keep.contains(where: { m.intersects($0) }) }),
                   "脱敏框与必须保留的区域重叠")
        for (i, s) in scan.suggestions.enumerated() {
            try expect(ignored.contains(i) || item.masks.contains(where: { $0.contains(s.box) }),
                       "仍有未覆盖也未确认忽略的建议")
        }
    }
}

func scan(_ src: URL, _ target: URL, _ choice: String) throws -> Scan {
    let names = choice == "manual" ? [] : choice.components(separatedBy: ",")
    try expect(Set(names).count == names.count && names.allSatisfy({ patterns[$0] != nil }),
               "识别类别无效，可选 email,phone,url,account 或 manual")
    let inputs = try sourceFiles(src)
    var images: [ScanImage] = []
    for (i, path) in inputs.enumerated() {
        let raw = try bounded(path)
        let picture = try image(raw)
        images.append(ScanImage(id: imageID(i), sha256: sha(raw), width: picture.width, height: picture.height,
                                suggestions: try suggest(picture, names.sorted())))
    }
    let result = Scan(version: version, images: images)
    try save(json(result), target)
    return result
}

func process(_ input: URL, _ scanURL: URL, _ planURL: URL, _ candidate: URL, render: Bool) throws -> (Audit, [String: Data]) {
    let scanBytes = try bounded(scanURL, limit: 2_000_000)
    let planBytes = try bounded(planURL, limit: 2_000_000)
    let scan = try JSONDecoder().decode(Scan.self, from: scanBytes)
    let plan = try JSONDecoder().decode(Plan.self, from: planBytes)
    let inputs = try sourceFiles(input)
    try expect(scan.version == version && plan.version == version && plan.scanSHA256 == sha(scanBytes),
               "确认清单与扫描版本或摘要不一致")
    try expect(inputs.count == scan.images.count && scan.images.count == plan.images.count,
               "原图、扫描和确认清单数量不符")
    if !render {
        let props = try candidate.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
        try expect(props.isDirectory == true && props.isSymbolicLink != true, "候选必须在普通目录中")
    }
    var exports: [String: Data] = [:]
    var held: [String] = []
    for (i, path) in inputs.enumerated() {
        let s = scan.images[i], p = plan.images[i]
        let raw = try bounded(path)
        try expect(s.id == imageID(i) && sha(raw) == s.sha256, "原图已更换，须重新扫描")
        let decoded = try image(raw)
        try expect(s.width == decoded.width && s.height == decoded.height && s.suggestions.count <= 200
                   && s.suggestions.allSatisfy({ patterns[$0.kind] != nil && $0.box.valid(s.width, s.height) }),
                   "扫描坐标无效或尺寸不符")
        try checkPlan(p, s)
        if p.disposition == "held" {
            held.append(s.id)
            continue
        }
        let filename = s.id + ".png"
        var raster = try Raster(decoded)
        if render {
            raster.cover(p.masks)
            exports[filename] = try raster.png()
        } else {
            let output = try bounded(candidate.appendingPathComponent(filename))
            _ = try pngChunks(output, strip: false)
            let decodedOutput = try Raster(image(output))
            try checkPixels(raster, decodedOutput, p.masks)
            let canonical = try decodedOutput.png()
            try expect(output == canonical, "候选包含编码器未生成的数据")
            exports[filename] = output
        }
    }
    if render {
        try freshDirectory(candidate)
        for (key, value) in exports { try save(value, candidate.appendingPathComponent(key)) }
    } else {
        let filenames = try FileManager.default.contentsOfDirectory(atPath: candidate.path)
        try expect(Set(filenames) == Set(exports.keys), "候选目录含有多余或缺失文件")
    }
    return (Audit(version: version, scanSHA256: sha(scanBytes), planSHA256: sha(planBytes),
                  filesSHA256: exports.mapValues(sha), held: held), exports)
}

func deliver(_ audit: Audit, _ exports: [String: Data], to target: URL) throws {
    try freshDirectory(target)
    let share = target.appendingPathComponent("share")
    try freshDirectory(share)
    for (name, png) in exports { try save(png, share.appendingPathComponent(name)) }
    let rows = exports.keys.sorted().map { "<li><a href=\"share/\($0)\">\($0)</a></li>" }.joined()
    let held = audit.held.map { "<li>\($0) · 暂缓外发</li>" }.joined()
    let page = """
    <!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>截图脱敏复核清单</title><style>body{background:#eff5f2;color:#142f31;font:16px/1.65 system-ui,sans-serif;margin:0}
    main{max-width:740px;margin:auto;padding:32px}section{background:#fff;border:1px solid #b6cdc7;border-radius:12px;padding:0 20px;margin:20px 0}
    a{color:#155e55}.status{background:#dcece6;padding:12px;border-left:5px solid #23766b}</style>
    <main><h1>截图脱敏复核清单</h1><p class="status">\(exports.count) 张通过像素复核，\(audit.held.count) 张暂缓</p>
    <section><h2>可供最后检查的副本</h2><ul>\(rows.isEmpty ? "<li>本批没有已通过的副本</li>" : rows)</ul></section>
    <section><h2>暂缓外发</h2><ul>\(held.isEmpty ? "<li>无</li>" : held)</ul></section>
    <p>复核覆盖已确认遮盖区域。发送前请再次确认未标记区域。</p><p><a href="manifest.json">文件摘要</a></p></main></html>
    """
    try save(Data(page.utf8), target.appendingPathComponent("checklist.html"))
    try save(json(audit), target.appendingPathComponent("manifest.json"))
}

func run(_ a: [String]) throws {
    if a == ["--help"] || a == ["-h"] {
        print("""
        截图脱敏复核 v\(version) · 本机 PNG
        scan 截图目录 扫描.json 类别（email,phone,url,account 或 manual）
        render 截图目录 扫描.json 确认.json 新候选目录
        verify 截图目录 扫描.json 确认.json 候选目录 新复核.json
        deliver 截图目录 扫描.json 确认.json 候选目录 复核.json 新交付目录
        """)
        return
    }
    guard let cmd = a.first, let expected = ["scan":4,"render":5,"verify":6,"deliver":7][cmd],
          a.count == expected else { throw Failure("参数无效，请查看 --help") }
    func url(_ i: Int) -> URL { URL(fileURLWithPath: a[i]) }
    if cmd == "scan" {
        let info = try scan(url(1), url(2), a[3])
        print("已扫描 \(info.images.count) 张截图。请使用本地确认页检查建议和保留区域。")
        return
    }
    let (audit, exports) = try process(url(1), url(2), url(3), url(4), render: cmd == "render")
    if cmd == "verify" { try save(json(audit), url(5)) }
    if cmd == "deliver" {
        let previous = try bounded(url(5), limit: 100_000)
        let current = try json(audit)
        try expect(previous == current, "正式复核记录与当前候选不同")
        try deliver(audit, exports, to: url(6))
    }
    print("本阶段完成：\(exports.count) 张副本，\(audit.held.count) 张暂缓。")
}

do {
    try run(Array(CommandLine.arguments.dropFirst()))
} catch let failure as Failure {
    FileHandle.standardError.write(Data(("复核中止：" + failure.message + "\n").utf8))
    exit(1)
} catch {
    FileHandle.standardError.write(Data("复核中止：无法读写文件、解析清单或运行本机检查，请核对格式、权限和新输出路径。\n".utf8))
    exit(1)
}
