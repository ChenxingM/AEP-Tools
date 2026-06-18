from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python"))

from aep_parser import parse_aep_settings  # noqa: E402

FOLDER = r"X:\GS1MND\MND_01\600_Comp"
RECURSIVE = True
CSV_OUT = "MND_01_working_colorspace.csv"

FIELDS = ["file", "path", "color_space", "ocio_config",
          "bits_per_channel", "working_gamma", "modified", "error"]


def probe(path: Path) -> dict:
    proj = parse_aep_settings(path.read_bytes())
    return {
        "working_color_space_name": proj.working_color_space_name,  # "sRGB IEC61966-2.1" / "" (OCIO/none)
        "cms": proj.color_management_settings,
        "bpc": proj.bits_per_channel,
        "gamma": proj.working_gamma,
    }


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(FOLDER)
    csv_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(CSV_OUT)
    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        sys.exit(1)

    pattern = "**/*.aep" if RECURSIVE else "*.aep"
    files = sorted(f for f in folder.glob(pattern) if "自動保存" not in f.name)
    if not files:
        print(f"No .aep files found in {folder}")
        return

    print(f"Scanning {len(files)} file(s) in {folder}\n")
    header = f"{'File':<40} {'Color Space':<22} {'BPC':>3} {'Gamma':>15} {'Modified':>20}"
    print(header)
    print("-" * len(header))

    n_ok = n_err = 0
    # Write incrementally + flush so partial results survive a hard OOM/kill.
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()

        for f in files:
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                mtime = ""
            try:
                r = probe(f)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:  # noqa: BLE001  (also catch Rust PanicException / MemoryError)
                n_err += 1
                print(f"{f.name[:40]:<40} ERROR: {type(e).__name__}: {e}")
                writer.writerow({
                    "file": f.name, "path": str(f), "color_space": "",
                    "ocio_config": "", "bits_per_channel": "", "working_gamma": "",
                    "modified": mtime, "error": f"{type(e).__name__}: {e}",
                })
                fh.flush()
                continue

            n_ok += 1
            wcs = r["working_color_space_name"] or "None"
            print(f"{f.name[:40]:<40} {wcs[:22]:<22} {r['bpc']:>3} "
                  f"{r['gamma']:>15} {mtime:>20}")
            writer.writerow({
                "file": f.name,
                "path": str(f),
                "color_space": wcs,
                "ocio_config": r["cms"].get("ocioConfigurationFile", ""),
                "bits_per_channel": r["bpc"],
                "working_gamma": r["gamma"],
                "modified": mtime,
                "error": "",
            })
            fh.flush()

    print(f"\nSaved CSV: {csv_path.resolve()}  ({n_ok} ok, {n_err} errors)")


if __name__ == "__main__":
    main()
