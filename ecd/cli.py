import argparse
import json
import sys
from importlib.metadata import version

import ecd


def main() -> None:
    """Main CLI entrypoint (for "ecd" command)"""
    v = version("everybody-codes-data")
    parser = argparse.ArgumentParser(description=f"Everybody Codes Data v{v}")
    parser.add_argument(
        "quest",
        type=int,
        help="puzzle quest, e.g. 1-20",
    )
    parser.add_argument(
        "event",
        type=int,
        help="puzzle event, e.g. 2024 or 2025",
    )
    parser.add_argument(
        "--seed",
        type=int,
        metavar="<1-100>",
        help="optional seed for API (1-100)",
    )
    parser.add_argument(
        "--part",
        type=int,
        choices=[1, 2, 3],
        help="print only the specific part (1, 2 or 3)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"everybody-codes-data v{v}",
    )
    args = parser.parse_args()
    quest = args.quest
    event = args.event
    if event in range(1, 21) and quest >= 2024:
        # be forgiving if user does "ecd 2024 1" instead of "ecd 1 2024"
        quest, event = event, quest
    seed = args.seed
    inputs = ecd.get_inputs(quest=quest, event=event, seed=seed)
    if args.part is not None:
        part = str(args.part)
        if part not in inputs:
            sys.exit(f"ERROR: part {part} is not available yet.")
        print(inputs[part])
    else:
        print(json.dumps(inputs, indent=2))
