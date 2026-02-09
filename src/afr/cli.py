import argparse
import sys

import afr.state as state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="afr", add_help=True)
    parser.add_argument(
        "--defer",
        action="store_true",
        help="Defer plotting into a pixel queue and blit it out gradually.",
    )
    parser.add_argument(
        "--blit-rate",
        type=int,
        default=state.BLIT_PPS,
        help="Pixels per second blitted when --defer is enabled.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frame cap (use 0 for uncapped).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print FPS and effective blit throughput once per second.",
    )
    parser.add_argument(
        "--bench-blit",
        action="store_true",
        help="Benchmark blitting throughput by draining a pre-filled pixel queue (implies --defer).",
    )
    parser.add_argument(
        "--bench-pixels",
        type=int,
        default=200_000,
        help="How many pixels to enqueue for --bench-blit.",
    )
    return parser


def parse_args(argv: list[str] | None = None):
    parser = build_parser()
    return parser.parse_args(sys.argv[1:] if argv is None else argv)

