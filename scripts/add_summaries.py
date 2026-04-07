#!/usr/bin/env python3
"""Add extractive summaries to the articles JSON dataset.

For each article the summary is built from the text blocks:
  1. Collect all text blocks and split them into sentences on Chinese
     sentence-ending punctuation (。！？) as well as newlines.
  2. Take sentences in order until the combined text reaches the target
     length (default 200 chars) or we run out of content.
  3. If the article is shorter than the minimum (default 60 chars) the
     whole content is used as-is.
"""

import argparse
import json
import re
from pathlib import Path

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？])\s*")
TARGET_LENGTH = 200
MIN_LENGTH = 60


def extract_summary(blocks: list[dict], target: int = TARGET_LENGTH, minimum: int = MIN_LENGTH) -> str:
    """Return an extractive summary from a list of content blocks."""
    sentences: list[str] = []
    for block in blocks:
        if block.get("type") != "text":
            continue
        text = block["text"].replace("\r", "").replace("\n", " ").strip()
        if not text:
            continue
        parts = SENTENCE_SPLIT_RE.split(text)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    if not sentences:
        return ""

    full = "".join(sentences)
    if len(full) <= minimum:
        return full

    accumulated: list[str] = []
    total = 0
    for sentence in sentences:
        accumulated.append(sentence)
        total += len(sentence)
        if total >= target:
            break

    summary = "".join(accumulated)
    if len(summary) > target + 50:
        summary = summary[: target + 50].rstrip() + "…"
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add extractive summaries to the Vida articles JSON dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the source articles JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write the updated JSON. Defaults to overwriting the input file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = args.input.resolve()
    dst = args.output.resolve() if args.output else src

    payload = json.loads(src.read_text(encoding="utf-8"))
    updated = 0
    for article in payload["articles"]:
        summary = extract_summary(article.get("blocks", []))
        article["summary"] = summary
        if summary:
            updated += 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"articles updated with summary: {updated} / {len(payload['articles'])}")
    print(f"output: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
