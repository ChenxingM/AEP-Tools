//! AEP project file collector — extract assets, copy files, rewrite paths.

use std::collections::HashMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc};
use std::time::Instant;

use crate::rifx::{self, Chunk};
use crate::version;

pub const APP_ABOUT: &str = concat!("AEP Collector - by: 千石まよひ - V", env!("CARGO_PKG_VERSION"));

/// Progress message sent to the GUI.
pub enum ProgressMsg {
    /// General info line.
    Info(String),
    /// A new AEP file is starting. (file_index 0-based, file_total)
    FileStart { file_idx: usize, file_total: usize, name: String },
    /// Asset progress within current file. (asset_index 1-based, asset_total, display text)
    Asset { current: usize, total: usize, text: String },
    /// Current AEP file finished.
    FileDone,
    /// All files done.
    AllDone,
    /// Fatal error.
    Error(String),
}

/// Options for collect operation.
pub struct CollectOptions {
    pub aep_path: PathBuf,
    pub output_dir: PathBuf,
    /// Raw version_id to write. None = keep original version.
    pub target_version: Option<u32>,
}

/// Convert version only (no asset collection). Writes modified AEP next to original with _converted suffix,
/// or into output_dir if provided.
pub fn convert_version_only(
    files: &[PathBuf], target_vid: u32,
    output_dir: Option<&Path>,
    tx: &mpsc::Sender<ProgressMsg>,
    cancel: &Arc<AtomicBool>,
) {
    let target_ver = version::decode_version_id(target_vid);
    let target_label = target_ver.label();
    let total = files.len();

    for (i, aep_path) in files.iter().enumerate() {
        if cancel.load(Ordering::Relaxed) {
            let _ = tx.send(ProgressMsg::Info("Stopped by user".into()));
            break;
        }
        let name = aep_path.file_name().unwrap_or_default().to_string_lossy().to_string();
        let _ = tx.send(ProgressMsg::FileStart { file_idx: i, file_total: total, name: name.clone() });

        let data = match fs::read(aep_path) {
            Ok(d) => d,
            Err(e) => {
                let _ = tx.send(ProgressMsg::Error(format!("Cannot read {}: {}", aep_path.display(), e)));
                continue;
            }
        };
        let (mut root, big_endian) = match rifx::parse_aep(&data) {
            Ok(r) => r,
            Err(e) => {
                let _ = tx.send(ProgressMsg::Error(e));
                continue;
            }
        };

        let original = version::read_version(&root)
            .map(|v| v.label()).unwrap_or_default();

        version::write_version(&mut root, target_vid);

        let out_path = if let Some(dir) = output_dir {
            let _ = fs::create_dir_all(dir);
            dir.join(aep_path.file_name().unwrap_or_default())
        } else {
            aep_path.to_path_buf()
        };

        let serialized = rifx::serialize(&root, big_endian);
        match fs::write(&out_path, serialized) {
            Ok(_) => {
                let _ = tx.send(ProgressMsg::Info(format!(
                    "[OK] {} : {} -> {}", name, original, target_label
                )));
            }
            Err(e) => {
                let _ = tx.send(ProgressMsg::Error(format!("Cannot write {}: {}", out_path.display(), e)));
            }
        }
        let _ = tx.send(ProgressMsg::FileDone);
    }
    let _ = tx.send(ProgressMsg::AllDone);
}

/// Collect multiple AEP files (batch mode).
pub fn collect_batch(files: &[PathBuf], output_base: &Path,
                     target_version: Option<u32>,
                     tx: &mpsc::Sender<ProgressMsg>,
                     cancel: &Arc<AtomicBool>) {
    let total = files.len();
    for (i, aep_path) in files.iter().enumerate() {
        if cancel.load(Ordering::Relaxed) {
            let _ = tx.send(ProgressMsg::Info("Stopped by user".into()));
            break;
        }
        let stem = aep_path.file_stem().unwrap_or_default().to_string_lossy();
        let name = aep_path.file_name().unwrap_or_default().to_string_lossy().to_string();
        let output_dir = output_base.join(format!("{}_collected", stem));
        let _ = tx.send(ProgressMsg::FileStart { file_idx: i, file_total: total, name });

        let opts = CollectOptions {
            aep_path: aep_path.clone(),
            output_dir,
            target_version: target_version.clone(),
        };
        collect_project(&opts, tx, cancel);
        let _ = tx.send(ProgressMsg::FileDone);
    }
    let _ = tx.send(ProgressMsg::AllDone);
}

/// Collect a single AEP project.
pub fn collect_project(opts: &CollectOptions, tx: &mpsc::Sender<ProgressMsg>, cancel: &Arc<AtomicBool>) {
    let t0 = Instant::now();
    let aep_path = &opts.aep_path;
    let output_dir = &opts.output_dir;

    let data = match fs::read(aep_path) {
        Ok(d) => d,
        Err(e) => {
            let _ = tx.send(ProgressMsg::Error(format!("Cannot read {}: {}", aep_path.display(), e)));
            return;
        }
    };
    let (mut root, big_endian) = match rifx::parse_aep(&data) {
        Ok(r) => r,
        Err(e) => {
            let _ = tx.send(ProgressMsg::Error(e));
            return;
        }
    };

    let mut original_version = String::new();
    let mut converted_version = String::new();

    if let Some(ver) = version::read_version(&root) {
        original_version = ver.label();
        let _ = tx.send(ProgressMsg::Info(format!("Version: {}", original_version)));
    }

    if let Some(target_vid) = opts.target_version {
        version::write_version(&mut root, target_vid);
        let target_ver = version::decode_version_id(target_vid);
        converted_version = target_ver.label();
        let _ = tx.send(ProgressMsg::Info(format!("Convert to: {}", converted_version)));
    }

    let footage_root = output_dir.join("(Footage)");
    if let Err(e) = fs::create_dir_all(&footage_root) {
        let _ = tx.send(ProgressMsg::Error(format!("Cannot create dir: {}", e)));
        return;
    }

    let assets = extract_assets(&root);
    let total = assets.len();
    let mut copied = 0usize;
    let mut missing = 0usize;
    let mut errors = 0usize;
    let mut total_bytes = 0u64;
    let mut report_entries: Vec<ReportEntry> = Vec::new();
    let mut seen_destinations: HashMap<String, usize> = HashMap::new();

    let _ = tx.send(ProgressMsg::Info(format!("Assets: {}  Output: {}", total, output_dir.display())));

    for (idx, asset) in assets.iter().enumerate() {
        if cancel.load(Ordering::Relaxed) {
            let _ = tx.send(ProgressMsg::Info("Stopped by user".into()));
            return;
        }
        let folder_display = if asset.folder_path.is_empty() {
            "(root)".to_string()
        } else {
            asset.folder_path.join("/")
        };

        let src = PathBuf::from(&asset.full_path);
        let mut target_dir = footage_root.clone();
        for folder_name in &asset.folder_path {
            target_dir = target_dir.join(sanitize_folder_name(folder_name));
        }
        if let Err(e) = fs::create_dir_all(&target_dir) {
            errors += 1;
            let msg = format!("[ERR] {}/{}: {}", folder_display, asset.name, e);
            let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
            report_entries.push(ReportEntry {
                name: asset.name.clone(), folder: folder_display,
                source: asset.full_path.clone(), destination: String::new(),
                status: format!("error: {}", e), size: 0,
            });
            continue;
        }

        // Directory-based sequence
        if src.is_dir() {
            let seq_subdir = target_dir.join(sanitize_folder_name(
                src.file_name().unwrap_or_default().to_str().unwrap_or("seq"),
            ));
            let _ = fs::create_dir_all(&seq_subdir);
            match copy_dir_contents(&src, &seq_subdir) {
                Ok((count, bytes)) => {
                    let new_path = seq_subdir.to_string_lossy().to_string();
                    rewrite_asset_path(&mut root, asset.id, &new_path);
                    total_bytes += bytes;
                    copied += 1;
                    let msg = format!("[OK] [SEQ] {}/{} ({} files)", folder_display, asset.name, count);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: new_path,
                        status: format!("copied_seq ({} files)", count), size: bytes,
                    });
                }
                Err(e) => {
                    errors += 1;
                    let msg = format!("[ERR] {}/{}: {}", folder_display, asset.name, e);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: String::new(),
                        status: format!("error: {}", e), size: 0,
                    });
                }
            }
            continue;
        }

        // File-based sequence
        if let Some(seq_files) = find_sequence_files(&src) {
            let parent_name = src.parent().and_then(|p| p.file_name())
                .unwrap_or_default().to_string_lossy();
            let seq_subdir = target_dir.join(sanitize_folder_name(&parent_name));
            let _ = fs::create_dir_all(&seq_subdir);
            match copy_files(&seq_files, &seq_subdir) {
                Ok((count, bytes)) => {
                    let new_path = seq_subdir.join(src.file_name().unwrap_or_default())
                        .to_string_lossy().to_string();
                    rewrite_asset_path(&mut root, asset.id, &new_path);
                    total_bytes += bytes;
                    copied += 1;
                    let msg = format!("[OK] [SEQ] {}/{} ({} files)", folder_display, asset.name, count);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: new_path,
                        status: format!("copied_seq ({} files)", count), size: bytes,
                    });
                }
                Err(e) => {
                    errors += 1;
                    let msg = format!("[ERR] {}/{}: {}", folder_display, asset.name, e);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: String::new(),
                        status: format!("error: {}", e), size: 0,
                    });
                }
            }
            continue;
        }

        // Single file
        if src.is_file() {
            let mut dst_name = src.file_name().unwrap_or_default().to_string_lossy().to_string();
            let dest_key = target_dir.join(&dst_name).to_string_lossy().to_string();
            let counter = seen_destinations.entry(dest_key).or_insert(0);
            if *counter > 0 {
                let stem = src.file_stem().unwrap_or_default().to_string_lossy().to_string();
                let ext = src.extension().map(|e| format!(".{}", e.to_string_lossy())).unwrap_or_default();
                dst_name = format!("{}_{}{}", stem, counter, ext);
            }
            *counter += 1;
            let dst = target_dir.join(&dst_name);
            match copy_single_file(&src, &dst) {
                Ok(bytes) => {
                    let new_path = dst.to_string_lossy().to_string();
                    rewrite_asset_path(&mut root, asset.id, &new_path);
                    total_bytes += bytes;
                    copied += 1;
                    let mb = bytes as f64 / (1024.0 * 1024.0);
                    let msg = format!("[OK] {}/{} ({:.1} MB)", folder_display, asset.name, mb);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: new_path,
                        status: "copied".into(), size: bytes,
                    });
                }
                Err(e) => {
                    errors += 1;
                    let msg = format!("[ERR] {}/{}: {}", folder_display, asset.name, e);
                    let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
                    report_entries.push(ReportEntry {
                        name: asset.name.clone(), folder: folder_display,
                        source: asset.full_path.clone(), destination: String::new(),
                        status: format!("error: {}", e), size: 0,
                    });
                }
            }
        } else {
            missing += 1;
            let msg = format!("[MISS] {}/{}: {}", folder_display, asset.name, asset.full_path);
            let _ = tx.send(ProgressMsg::Asset { current: idx + 1, total, text: msg });
            report_entries.push(ReportEntry {
                name: asset.name.clone(), folder: folder_display,
                source: asset.full_path.clone(), destination: String::new(),
                status: "missing".into(), size: 0,
            });
        }
    }

    // Save modified AEP
    let out_aep = output_dir.join(aep_path.file_name().unwrap_or_default());
    let serialized = rifx::serialize(&root, big_endian);
    if let Err(e) = fs::write(&out_aep, serialized) {
        let _ = tx.send(ProgressMsg::Error(format!("Cannot write: {}", e)));
        return;
    }

    let elapsed = t0.elapsed().as_secs_f64();

    // Write report
    let report = generate_report(
        aep_path, output_dir, &report_entries,
        total, copied, missing, errors, total_bytes, elapsed,
        &original_version, &converted_version,
    );
    let report_path = output_dir.join("collect_report.txt");
    let _ = fs::write(&report_path, &report);

    let size_mb = total_bytes as f64 / (1024.0 * 1024.0);
    let _ = tx.send(ProgressMsg::Info(format!(
        "Done: {} copied, {} missing, {} errors  ({:.1} MB, {:.1}s)",
        copied, missing, errors, size_mb, elapsed
    )));
}

/// Scan a directory for .aep files.
pub fn find_aep_files(dir: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                if let Some(ext) = path.extension() {
                    if ext.to_string_lossy().to_lowercase() == "aep" {
                        files.push(path);
                    }
                }
            }
        }
    }
    files.sort();
    files
}

// Asset extraction

fn extract_assets(root: &Chunk) -> Vec<AssetInfo> {
    let mut assets = Vec::new();
    if let Some(fold) = root.find(b"Fold") {
        scan_folder(fold, &mut Vec::new(), &mut assets);
    }
    assets
}

struct AssetInfo {
    id: u32,
    name: String,
    full_path: String,
    folder_path: Vec<String>,
}

fn scan_folder(fold: &Chunk, folder_path: &mut Vec<String>, assets: &mut Vec<AssetInfo>) {
    for child in fold.children() {
        let name = child.name();
        if name == b"Item" {
            process_item(child, folder_path, assets);
        } else if name == b"Sfdr" {
            scan_folder(child, folder_path, assets);
        }
    }
}

fn process_item(item: &Chunk, folder_path: &mut Vec<String>, assets: &mut Vec<AssetInfo>) {
    let idta = match item.find(b"idta") { Some(c) => c, None => return };
    let idta_data = match idta.as_bytes() { Some(b) if b.len() >= 20 => b, _ => return };
    let item_type = u16::from_be_bytes([idta_data[0], idta_data[1]]);
    let item_id = u32::from_be_bytes([idta_data[16], idta_data[17], idta_data[18], idta_data[19]]);

    match item_type {
        1 => {
            let name = get_item_name(item);
            if !name.is_empty() { folder_path.push(name); }
            if let Some(sfdr) = item.find(b"Sfdr") {
                scan_folder(sfdr, folder_path, assets);
            }
            if !folder_path.is_empty() { folder_path.pop(); }
        }
        7 => {
            let name = get_item_name(item);
            if let Some(pin) = item.find(b"Pin ") {
                if is_solid(pin) { return; }
                if let Some(path) = get_asset_path(pin) {
                    if !path.is_empty() {
                        assets.push(AssetInfo { id: item_id, name, full_path: path, folder_path: folder_path.clone() });
                    }
                }
            }
        }
        _ => {}
    }
}

fn get_item_name(item: &Chunk) -> String {
    for child in item.children() {
        if &child.header == b"Utf8" {
            if let Some(s) = child.as_str() { return s.to_string(); }
        }
    }
    String::new()
}

fn is_solid(pin: &Chunk) -> bool {
    if let Some(opti) = pin.find(b"opti") {
        if let Some(data) = opti.as_bytes() {
            if data.len() >= 4 { return &data[0..4] == b"Soli"; }
        }
    }
    false
}

fn get_asset_path(pin: &Chunk) -> Option<String> {
    let als2 = pin.find(b"Als2")?;
    let alas = als2.find(b"alas")?;
    let json_str = alas.as_str()?;
    let json: serde_json::Value = serde_json::from_str(json_str).ok()?;
    json.get("fullpath")?.as_str().map(|s| s.to_string())
}

// Path rewriting

fn rewrite_asset_path(root: &mut Chunk, asset_id: u32, new_path: &str) {
    if let Some(fold) = root.find_mut(b"Fold") {
        rewrite_in_folder(fold, asset_id, new_path);
    }
}

fn rewrite_in_folder(fold: &mut Chunk, asset_id: u32, new_path: &str) {
    for child in fold.children_mut().iter_mut() {
        let name = *child.name();
        if &name == b"Item" {
            if let Some(idta) = child.find(b"idta") {
                if let Some(data) = idta.as_bytes() {
                    if data.len() >= 20 {
                        let id = u32::from_be_bytes([data[16], data[17], data[18], data[19]]);
                        if id == asset_id { rewrite_item_path(child, new_path); return; }
                    }
                }
            }
            if let Some(sfdr) = child.find_mut(b"Sfdr") {
                rewrite_in_folder(sfdr, asset_id, new_path);
            }
        } else if &name == b"Sfdr" {
            rewrite_in_folder(child, asset_id, new_path);
        }
    }
}

fn rewrite_item_path(item: &mut Chunk, new_path: &str) {
    let pin = match item.find_mut(b"Pin ") { Some(c) => c, None => return };
    let als2 = match pin.find_mut(b"Als2") { Some(c) => c, None => return };
    let alas = match als2.find_mut(b"alas") { Some(c) => c, None => return };
    let json_str = match alas.as_str() { Some(s) => s.to_string(), None => return };
    if let Ok(mut json) = serde_json::from_str::<serde_json::Value>(&json_str) {
        json["fullpath"] = serde_json::Value::String(new_path.to_string());
        if let Ok(new_json) = serde_json::to_string(&json) {
            if let Some(s) = alas.as_str_mut() { *s = new_json; }
        }
    }
}

// File operations

fn sanitize_folder_name(name: &str) -> String {
    let s: String = name.chars().map(|c| match c {
        '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*' => '_',
        _ => c,
    }).collect();
    s.trim_matches(|c: char| c == '.' || c == ' ').to_string()
}

fn copy_single_file(src: &Path, dst: &Path) -> Result<u64, io::Error> {
    if !dst.exists() { fs::copy(src, dst)?; }
    Ok(src.metadata()?.len())
}

fn copy_dir_contents(src_dir: &Path, dst_dir: &Path) -> Result<(usize, u64), io::Error> {
    let mut count = 0;
    let mut total = 0u64;
    let mut entries: Vec<_> = fs::read_dir(src_dir)?
        .filter_map(|e| e.ok()).filter(|e| e.path().is_file()).collect();
    entries.sort_by_key(|e| e.file_name());
    for entry in entries {
        let src = entry.path();
        let dst = dst_dir.join(entry.file_name());
        if !dst.exists() { if fs::copy(&src, &dst).is_err() { continue; } }
        if let Ok(meta) = src.metadata() { total += meta.len(); }
        count += 1;
    }
    Ok((count, total))
}

fn copy_files(files: &[PathBuf], dst_dir: &Path) -> Result<(usize, u64), io::Error> {
    let mut count = 0;
    let mut total = 0u64;
    for src in files {
        let dst = dst_dir.join(src.file_name().unwrap_or_default());
        if !dst.exists() { if fs::copy(src, &dst).is_err() { continue; } }
        if let Ok(meta) = src.metadata() { total += meta.len(); }
        count += 1;
    }
    Ok((count, total))
}

fn find_sequence_files(path: &Path) -> Option<Vec<PathBuf>> {
    let parent = path.parent()?;
    if !parent.is_dir() { return None; }
    let fname = path.file_name()?.to_str()?;
    let (prefix, pad_len, ext) = find_sequence_pattern(fname)?;
    let mut files: Vec<PathBuf> = fs::read_dir(parent).ok()?
        .filter_map(|e| e.ok()).filter(|e| e.path().is_file())
        .filter(|e| {
            let n = e.file_name(); let n = n.to_string_lossy();
            matches_sequence_pattern(&n, prefix, pad_len, ext)
        })
        .map(|e| e.path()).collect();
    if files.len() > 1 { files.sort(); Some(files) } else { None }
}

fn find_sequence_pattern(name: &str) -> Option<(&str, usize, &str)> {
    let dot = name.rfind('.')?;
    let ext = &name[dot..];
    let stem = &name[..dot];
    let ds = stem.bytes().rposition(|b| !b.is_ascii_digit()).map(|p| p + 1).unwrap_or(0);
    let digits = &stem[ds..];
    if digits.len() < 2 { return None; }
    Some((&stem[..ds], digits.len(), ext))
}

fn matches_sequence_pattern(name: &str, prefix: &str, pad_len: usize, ext: &str) -> bool {
    if !name.starts_with(prefix) || !name.ends_with(ext) { return false; }
    let mid = &name[prefix.len()..name.len() - ext.len()];
    mid.len() == pad_len && mid.bytes().all(|b| b.is_ascii_digit())
}

// Report

struct ReportEntry {
    name: String, folder: String, source: String,
    destination: String, status: String, size: u64,
}

fn generate_report(
    src_aep: &Path, out_root: &Path, entries: &[ReportEntry],
    total: usize, copied: usize, missing: usize, errors: usize,
    total_bytes: u64, elapsed: f64,
    original_version: &str, converted_version: &str,
) -> String {
    let size_mb = total_bytes as f64 / (1024.0 * 1024.0);
    let now = timestamp_now();
    let sep = "=".repeat(70);
    let dash = "-".repeat(70);
    let mut lines = vec![
        sep.clone(), format!("AEP Collect Files Report — {}", APP_ABOUT), sep.clone(), String::new(),
        format!("Date:           {}", now),
        format!("Source:         {}", src_aep.display()),
        format!("Output:         {}", out_root.display()),
    ];
    if !original_version.is_empty() {
        lines.push(format!("AE Version:     {}", original_version));
    }
    if !converted_version.is_empty() {
        lines.push(format!("Converted to:   {}", converted_version));
    }
    lines.extend([
        String::new(),
        format!("Total Assets:   {}", total),
        format!("Copied:         {}", copied),
        format!("Missing:        {}", missing),
        format!("Errors:         {}", errors),
        format!("Total Size:     {:.1} MB", size_mb),
        format!("Time:           {:.1}s", elapsed),
        String::new(), dash.clone(), "Assets".into(), dash.clone(), String::new(),
    ]);

    let mut folders: Vec<(&str, Vec<&ReportEntry>)> = Vec::new();
    for entry in entries {
        if let Some(g) = folders.iter_mut().find(|(f, _)| *f == entry.folder) {
            g.1.push(entry);
        } else {
            folders.push((&entry.folder, vec![entry]));
        }
    }
    for (folder, group) in &folders {
        lines.push(format!("[{}]", folder));
        for e in group {
            let sz = if e.size > 0 { format!(" ({:.1} MB)", e.size as f64 / (1024.0 * 1024.0)) } else { String::new() };
            if e.status == "missing" {
                lines.push(format!("  {}  [MISSING]", e.name));
                lines.push(format!("    src: {}", e.source));
            } else if e.status.starts_with("error") {
                lines.push(format!("  {}  [ERROR]", e.name));
                lines.push(format!("    {}", e.status));
            } else {
                lines.push(format!("  {}  [ok]{}", e.name, sz));
                if !e.destination.is_empty() { lines.push(format!("    -> {}", e.destination)); }
            }
        }
        lines.push(String::new());
    }

    let miss: Vec<_> = entries.iter().filter(|e| e.status == "missing").collect();
    if !miss.is_empty() {
        lines.push(dash.clone());
        lines.push("Missing Files (copy these manually)".into());
        lines.push(dash);
        for e in &miss { lines.push(format!("  {}", e.source)); }
        lines.push(String::new());
    }
    lines.push(sep);
    lines.join("\n")
}

fn timestamp_now() -> String {
    use std::time::SystemTime;
    let secs = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap_or_default().as_secs();
    let days = secs / 86400;
    let ds = secs % 86400;
    let (h, m, s) = (ds / 3600, (ds % 3600) / 60, ds % 60);
    let mut y = 1970i64;
    let mut rem = days as i64;
    loop {
        let dy = if is_leap(y) { 366 } else { 365 };
        if rem < dy { break; }
        rem -= dy; y += 1;
    }
    let md = if is_leap(y) { [31,29,31,30,31,30,31,31,30,31,30,31] }
             else { [31,28,31,30,31,30,31,31,30,31,30,31] };
    let mut mo = 1;
    for &d in &md { if rem < d { break; } rem -= d; mo += 1; }
    format!("{:04}-{:02}-{:02} {:02}:{:02}:{:02}", y, mo, rem + 1, h, m, s)
}

fn is_leap(y: i64) -> bool { (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 }
