"""
Collect Files
"""
from __future__ import annotations

import io
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import Project, FootageItem, CompItem
from aep_tools._project import FolderItem


def collect_items(item, results: list[tuple[list[str], FootageItem]],
                  folder_path: list[str] | None = None):
    """Recursively collect all FootageItem instances with their folder path."""
    if folder_path is None:
        folder_path = []
    if isinstance(item, FolderItem):
        sub_path = folder_path + [item.name] if item.name else folder_path
        for i in range(1, item.num_items + 1):
            collect_items(item.items[i], results, sub_path)
    elif isinstance(item, FootageItem):
        results.append((list(folder_path), item))


def _sanitize_folder_name(name: str) -> str:
    """Remove characters that are invalid in directory names."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip('. ')


def collect_project(aep_path: str, output_dir: str | None = None):
    aep = Path(aep_path)
    if not aep.exists():
        print(f"File not found: {aep}")
        sys.exit(1)

    t0 = time.time()
    proj = Project.open(aep)
    if not proj.writable:
        print("Only .aep files are supported (requires binary chunk tree for path rewriting)")
        sys.exit(1)

    # Output directory
    out_root = Path(output_dir) if output_dir else aep.parent / f"{aep.stem}_collected"
    footage_root = out_root / "(Footage)"
    footage_root.mkdir(parents=True, exist_ok=True)

    # Collect all footage items with their folder paths
    footages: list[tuple[list[str], FootageItem]] = []
    for i in range(1, proj.num_items + 1):
        collect_items(proj.item(i), footages)

    # Count only footage with file paths (exclude solids)
    total = sum(1 for _, it in footages if it.file is not None)
    copied = 0
    missing = 0
    errors = 0
    report_lines: list[dict] = []
    # Track destination paths globally to avoid collisions
    seen_destinations: dict[str, int] = {}

    print(f"Project: {aep.name}")
    print(f"Assets:  {total}")
    print(f"Output:  {out_root}\n")

    for folder_path, item in footages:
        src_path = item.file
        # Build display prefix from folder path
        folder_display = "/".join(folder_path) if folder_path else "(root)"

        entry: dict = {
            "name": item.name,
            "id": item.id,
            "type": item.type_name,
            "folder": folder_display,
            "source": src_path or "",
            "destination": "",
            "status": "",
            "size": 0,
        }

        # Solids have no file path — just ignore them
        if src_path is None:
            continue

        src = Path(src_path)

        # Build target directory preserving project folder structure
        target_dir = footage_root
        for folder_name in folder_path:
            target_dir = target_dir / _sanitize_folder_name(folder_name)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Detect sequence: path is a directory (AE stores folder path for
        # sequences rendered to per-pass folders), or path is a file whose
        # siblings form a numbered sequence.
        if src.is_dir():
            # Path points to a folder containing sequence frames
            seq_files = sorted(f for f in src.iterdir() if f.is_file())
            seq_subdir = target_dir / _sanitize_folder_name(src.name)
            seq_subdir.mkdir(parents=True, exist_ok=True)

            seq_copied, seq_total_size = _copy_files(seq_files, seq_subdir)
            if seq_copied < 0:
                errors += 1
                entry["status"] = "error: copy failed"
            else:
                new_path = str(seq_subdir)
                item.file = new_path
                entry["destination"] = new_path
                entry["status"] = f"copied_seq ({seq_copied} files)"
                entry["size"] = seq_total_size
                copied += 1
                print(f"  [SEQ] {folder_display}/{item.name} ({seq_copied} files)")
            report_lines.append(entry)
            continue

        seq_files = _find_sequence_files(src)
        if seq_files:
            # Path is a file that belongs to a numbered sequence
            seq_subdir = target_dir / _sanitize_folder_name(src.parent.name)
            seq_subdir.mkdir(parents=True, exist_ok=True)

            seq_copied, seq_total_size = _copy_files(seq_files, seq_subdir)
            if seq_copied < 0:
                errors += 1
                entry["status"] = "error: copy failed"
            else:
                new_path = str(seq_subdir / src.name)
                item.file = new_path
                entry["destination"] = new_path
                entry["status"] = f"copied_seq ({seq_copied} files)"
                entry["size"] = seq_total_size
                copied += 1
                print(f"  [SEQ] {folder_display}/{item.name} ({seq_copied} files)")
        elif src.is_file():
            # Single file
            dst_name = src.name
            # Full destination key includes folder path to scope collision detection
            dest_key = str(target_dir / dst_name)
            if dest_key in seen_destinations:
                seen_destinations[dest_key] += 1
                stem = src.stem
                suffix = src.suffix
                dst_name = f"{stem}_{seen_destinations[dest_key]}{suffix}"
            else:
                seen_destinations[dest_key] = 0

            dst = target_dir / dst_name
            try:
                if not dst.exists():
                    shutil.copy2(src, dst)
                file_size = src.stat().st_size
                new_path = str(dst)
                item.file = new_path
                entry["destination"] = new_path
                entry["status"] = "copied"
                entry["size"] = file_size
                copied += 1
                size_mb = file_size / (1024 * 1024)
                print(f"  [OK] {folder_display}/{item.name} ({size_mb:.1f} MB)")
            except OSError as e:
                entry["status"] = f"error: {e}"
                errors += 1
                print(f"  [ERR] {folder_display}/{item.name}: {e}")
        else:
            entry["status"] = "missing"
            missing += 1
            print(f"  [MISS] {folder_display}/{item.name}: {src_path}")

        report_lines.append(entry)

    # Save new .aep
    out_aep = out_root / aep.name
    proj.save(out_aep)
    elapsed = time.time() - t0
    print(f"\nSaved: {out_aep}")

    # Write report
    report_path = out_root / "collect_report.txt"
    total_size = sum(e["size"] for e in report_lines)
    _write_report(report_path, aep, out_root, report_lines,
                  total=total, copied=copied,
                  missing=missing, errors=errors,
                  total_size=total_size, elapsed=elapsed,
                  proj=proj)
    print(f"Report: {report_path}")
    print(f"\nDone: {copied} copied, {missing} missing, {errors} errors")
    print(f"Total size: {total_size / (1024*1024):.1f} MB  |  Time: {elapsed:.1f}s")


def _copy_files(files: list[Path], dest_dir: Path) -> tuple[int, int]:
    """Copy a list of files into dest_dir. Returns (count, total_bytes).

    Returns (-1, 0) on fatal error.
    """
    count = 0
    total = 0
    for f in files:
        dst = dest_dir / f.name
        try:
            if not dst.exists():
                shutil.copy2(f, dst)
            count += 1
            total += f.stat().st_size
        except OSError:
            pass  # skip individual file errors
    return count, total


def _find_sequence_files(path: Path) -> list[Path]:
    """If path looks like a frame in an image sequence, return all matching frames."""
    if not path.parent.is_dir():
        return []
    # Match filenames with numbered padding (e.g. image_0001.png)
    m = re.match(r'^(.+?)(\d{2,})(\.\w+)$', path.name)
    if not m:
        return []
    prefix, digits, ext = m.groups()
    pad_len = len(digits)
    # Find files with same prefix, extension, and digit count
    pattern = re.compile(
        rf'^{re.escape(prefix)}\d{{{pad_len}}}{re.escape(ext)}$')
    files = sorted(f for f in path.parent.iterdir()
                   if f.is_file() and pattern.match(f.name))
    # Only count as sequence if there are multiple frames
    if len(files) > 1:
        return files
    return []


def _write_report(path: Path, src_aep: Path, out_root: Path,
                  entries: list[dict], *, total: int, copied: int,
                  missing: int, errors: int,
                  total_size: int, elapsed: float, proj: Project):
    """Generate the collection report."""
    size_mb = total_size / (1024 * 1024)
    ver = proj.ae_version or "unknown"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 70,
        "AEP Collect Files Report",
        "=" * 70,
        "",
        f"Date:           {now}",
        f"Source:         {src_aep}",
        f"Output:         {out_root}",
        f"AE Version:     {ver}",
        "",
        f"Compositions:   {len(proj.compositions)}",
        f"Total Assets:   {total}",
        f"Copied:         {copied}",
        f"Missing:        {missing}",
        f"Errors:         {errors}",
        f"Total Size:     {size_mb:.1f} MB",
        f"Time:           {elapsed:.1f}s",
        "",
        "-" * 70,
        "Compositions",
        "-" * 70,
    ]
    for comp in proj.compositions:
        n_layers = len(list(comp.layers))
        lines.append(
            f"  {comp.name}  ({comp.width}x{comp.height}, "
            f"{comp.frame_rate:g} fps, {comp.duration:.2f}s, "
            f"{n_layers} layers)"
        )

    lines += [
        "",
        "-" * 70,
        "Assets",
        "-" * 70,
        "",
    ]

    # Group by folder, then by status within each folder
    folders: dict[str, list[dict]] = {}
    for e in entries:
        folder = e.get("folder", "(root)")
        folders.setdefault(folder, []).append(e)

    for folder, group in folders.items():
        lines.append(f"[{folder}]")
        for e in group:
            status = e["status"]
            size_str = f" ({e['size'] / (1024*1024):.1f} MB)" if e["size"] else ""
            if status == "skip_solid":
                lines.append(f"  {e['name']}  [solid]")
            elif status == "missing":
                lines.append(f"  {e['name']}  [MISSING]")
                lines.append(f"    src: {e['source']}")
            elif status.startswith("error"):
                lines.append(f"  {e['name']}  [ERROR]")
                lines.append(f"    {status}")
            else:
                lines.append(f"  {e['name']}  [ok]{size_str}")
                if e["destination"]:
                    lines.append(f"    -> {e['destination']}")
        lines.append("")

    # Missing files summary for manual follow-up
    missing_entries = [e for e in entries if e["status"] == "missing"]
    if missing_entries:
        lines += [
            "-" * 70,
            "Missing Files (copy these manually)",
            "-" * 70,
        ]
        for e in missing_entries:
            lines.append(f"  {e['source']}")
        lines.append("")

    lines.append("=" * 70)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    aep_path = r"S:\MHY\MHY_AV\3_vfx\034\MHYav_034_V1.aep"
    output_path = r"C:\Users\cmp094\Desktop\MHYav_034_V1_collected"
    collect_project(aep_path, output_path)


if __name__ == "__main__":
    main()
