"""Command line entrypoint."""

import argparse
import json
import sys

from .contracts import GateError
from .episode import create_episode
from .romance.workflow import create_chapter, create_series


def main() -> None:
    parser = argparse.ArgumentParser(prog="anime-video")
    command = parser.add_subparsers(dest="command", required=True)
    episode = command.add_parser("episode", help="create a cited episode planning pack")
    episode.add_argument("topic")
    episode.add_argument("--series", default="cosmos")
    episode.add_argument("--quality", choices=["draft", "final"], default="draft")
    episode.add_argument("--research-pack")
    episode.add_argument("--output-root")
    series = command.add_parser("romance-series")
    series.add_argument("--series-id", default="after-the-rain-route")
    series.add_argument("--output-root")
    chapter = command.add_parser("romance-chapter")
    chapter.add_argument("chapter_number", type=int)
    chapter.add_argument("--series-id", default="after-the-rain-route")
    chapter.add_argument("--quality", choices=["draft", "final"], default="draft")
    chapter.add_argument("--output-root")
    args = parser.parse_args()
    try:
        if args.command == "episode":
            result = create_episode(args.topic, series=args.series, quality=args.quality,
                                    research_pack=args.research_pack, output_root=args.output_root)
        elif args.command == "romance-series":
            result = create_series(args.series_id, args.output_root)
        else:
            result = create_chapter(args.series_id, args.chapter_number,
                                    quality=args.quality, output_root=args.output_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except GateError as exc:
        print(f"GATE: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()

