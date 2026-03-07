#!/usr/bin/env python3
"""CLI tool to parse AEP/AEPX files and output JSON.

Usage:
    aep-parser input.aep                 -> prints JSON to stdout
    aep-parser input.aep -o output.json  -> writes JSON to file
    aep-parser input.aepx                -> auto-detects format by extension
    aep-parser input.aep --compact       -> compact JSON output
    aep-parser input.aep --version       -> print AE version info only
    python -m aep_parser input.aep       -> same as above
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from . import parse_aep, parse_aepx

_OS_NAMES: dict[int, str] = {12: "Windows", 13: "macOS", 14: "macOS ARM"}


def _get_version_from_bytes(data: bytes) -> dict | None:
    """Quickly extract AE version info from raw .aep bytes without full parse."""
    # Find 'head' chunk — it's near the start of the RIFX container
    pos = data.find(b"head")
    if pos < 0 or pos + 12 > len(data):
        return None
    # head chunk: 4-byte tag + 4-byte size + payload
    size = struct.unpack(">I", data[pos + 4:pos + 8])[0]
    if size < 8:
        return None
    payload = data[pos + 8:pos + 8 + size]
    vid = struct.unpack(">I", payload[4:8])[0]
    maj_a = (vid >> 26) & 0x1F
    os_code = (vid >> 22) & 0x0F
    maj_b = (vid >> 19) & 0x07
    minor = (vid >> 15) & 0x0F
    patch = (vid >> 11) & 0x0F
    beta_flag = (vid >> 9) & 0x01
    build = vid & 0xFF
    major = maj_a * 8 + maj_b
    ver = f"{major}.{minor}.{patch}" if patch else f"{major}.{minor}"
    return {
        "version": ver,
        "major": major,
        "minor": minor,
        "patch": patch,
        "build": build,
        "os": _OS_NAMES.get(os_code, f"Unknown({os_code})"),
        "os_code": os_code,
        "beta": not beta_flag,
    }


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
    parser.add_argument("-V", "--version", action="store_true", dest="show_version",
                        help="Print AE version info only (fast, no full parse)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Fast version-only mode
    if args.show_version:
        if input_path.suffix.lower() == ".aepx":
            print("Version detection not supported for .aepx files", file=sys.stderr)
            sys.exit(1)
        data = input_path.read_bytes()
        info = _get_version_from_bytes(data)
        if not info:
            print("Could not detect AE version", file=sys.stderr)
            sys.exit(1)
        label = f"AE {info['version']}x{info['build']}" if info["build"] else f"AE {info['version']}"
        label += f"  ({info['os']})"
        if info["beta"]:
            label += "  [Beta]"
        print(label)
        print(json.dumps(info, indent=2))
        sys.exit(0)

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

    # Inject version info for binary .aep files
    if ext != ".aepx" and 'data' in dir():
        ver_info = _get_version_from_bytes(data)
        if ver_info:
            output["aeVersion"] = ver_info

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
