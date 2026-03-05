#!/usr/bin/env python3
"""CLI tool to parse AEP/AEPX files and output JSON.

Usage:
    aep-parser input.aep                 -> prints JSON to stdout
    aep-parser input.aep -o output.json  -> writes JSON to file
    aep-parser input.aepx                -> auto-detects format by extension
    aep-parser input.aep --compact       -> compact JSON output
    python -m aep_parser input.aep       -> same as above
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import parse_aep, parse_aepx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse AEP/AEPX files and output structured JSON")
    parser.add_argument("input", help="Path to .aep or .aepx file")
    parser.add_argument("-o", "--output", help="Output JSON file (default: stdout)")
    parser.add_argument("--compact", action="store_true",
                        help="Compact JSON output (no indentation)")
    parser.add_argument("--comp", help="Export only the composition with this name")
    parser.add_argument("--comp-id", type=int,
                        help="Export only the composition with this ID")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()

    try:
        if ext == ".aepx":
            xml_string = input_path.read_text(encoding="utf-8")
            project = parse_aepx(xml_string)
        elif ext == ".aep":
            data = input_path.read_bytes()
            project = parse_aep(data)
        else:
            # Try binary first, fall back to XML
            data = input_path.read_bytes()
            if data[:4] in (b"RIFF", b"RIFX"):
                project = parse_aep(data)
            else:
                xml_string = data.decode("utf-8")
                project = parse_aepx(xml_string)
    except Exception as e:
        print(f"Error parsing {input_path.name}: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter composition if requested
    output = project.to_dict()
    if args.comp:
        output["compositions"] = [
            c for c in output["compositions"] if c.get("name") == args.comp
        ]
    elif args.comp_id is not None:
        output["compositions"] = [
            c for c in output["compositions"] if c.get("id") == args.comp_id
        ]

    indent = None if args.compact else 2
    json_str = json.dumps(output, indent=indent, ensure_ascii=False,
                          default=str)

    if args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"Written to {args.output} ({len(json_str)} bytes)")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
