# ocr_screen.py - OCR a screenshot using the Windows built-in OCR engine
# Usage:
#   python ocr_screen.py <image.png> [lang]
#   lang: en  (default, English only)  |  zh  (loads en-US + zh-Hans-CN)
# Output: lines of "text<TAB>x,y,w,h" (recognised text + bounding box in image pixels)

import sys
import asyncio

try:
    import winsdk.windows.media.ocr as ocr
    import winsdk.windows.globalization as globalization
    import winsdk.windows.graphics.imaging as imaging
    import winsdk.windows.storage as storage
    import winsdk.windows.storage.streams as streams
except ImportError:
    print("ERROR: winsdk is not installed", file=sys.stderr)
    sys.exit(2)


async def run(path, lang_pref):
    f = await storage.StorageFile.get_file_from_path_async(path)
    stream = await f.open_async(storage.FileAccessMode.READ)
    decoder = await imaging.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    if lang_pref == "zh":
        tags = ["zh-Hans-CN", "en-US"]
    else:
        tags = ["en-US"]

    engine = None
    for tag in tags:
        try:
            language = globalization.Language(tag)
            if ocr.OcrEngine.is_language_supported(language):
                engine = ocr.OcrEngine.try_create_from_language(language)
                if engine:
                    print(f"# engine language: {tag}", file=sys.stderr)
                    break
        except Exception as exc:  # noqa: BLE001
            print(f"# language {tag} failed: {exc}", file=sys.stderr)

    if engine is None:
        engine = ocr.OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        print("ERROR: no OCR engine available", file=sys.stderr)
        sys.exit(3)

    result = await engine.recognize_async(bitmap)
    for line in result.lines:
        words = list(line.words)
        if not words:
            continue
        x0 = min(w.bounding_rect.x for w in words)
        y0 = min(w.bounding_rect.y for w in words)
        x1 = max(w.bounding_rect.x + w.bounding_rect.width for w in words)
        y1 = max(w.bounding_rect.y + w.bounding_rect.height for w in words)
        print(f"{line.text}\t{int(x0)},{int(y0)},{int(x1 - x0)},{int(y1 - y0)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    sys.exit(asyncio.run(run(sys.argv[1], lang)))
