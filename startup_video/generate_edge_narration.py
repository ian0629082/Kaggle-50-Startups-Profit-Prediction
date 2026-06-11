import asyncio
import json
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parent
TEXT_PATH = ROOT / "narration.txt"
OUT_DIR = ROOT / "assets" / "edge_yunjhe_segments"
VOICE = "zh-TW-YunJheNeural"
RATE = "+8%"
VOLUME = "+0%"
PITCH = "+0Hz"


def load_paragraphs() -> list[str]:
    text = TEXT_PATH.read_text(encoding="utf-8")
    return [part.strip() for part in text.split("\n\n") if part.strip()]


async def synthesize_segment(index: int, text: str) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    media_path = OUT_DIR / f"segment_{index:02d}.mp3"
    subtitle_path = OUT_DIR / f"segment_{index:02d}.vtt"
    communicator = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        volume=VOLUME,
        pitch=PITCH,
    )
    submaker = edge_tts.SubMaker()
    with media_path.open("wb") as media:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                media.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    subtitle_path.write_text(submaker.get_srt(), encoding="utf-8")
    return {
        "index": index,
        "voice": VOICE,
        "rate": RATE,
        "pitch": PITCH,
        "text": text,
        "media": str(media_path.relative_to(ROOT)).replace("\\", "/"),
        "subtitles": str(subtitle_path.relative_to(ROOT)).replace("\\", "/"),
    }


async def main() -> None:
    paragraphs = load_paragraphs()
    manifest = []
    for index, text in enumerate(paragraphs, start=1):
        print(f"Synthesizing {index:02d}/{len(paragraphs)}")
        manifest.append(await synthesize_segment(index, text))
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"segments": len(manifest), "voice": VOICE, "rate": RATE}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
