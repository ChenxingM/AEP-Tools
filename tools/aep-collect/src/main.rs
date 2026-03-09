// Hide console window when launched as GUI (double-click)
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod collect;
mod gui;
mod rifx;
mod version;

use std::path::{Path, PathBuf};
use std::sync::atomic::AtomicBool;
use std::sync::{mpsc, Arc};

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 || args[1] == "--gui" {
        gui::run_gui();
        return;
    }

    if args[1] == "-h" || args[1] == "--help" {
        print_usage();
        return;
    }

    let input = PathBuf::from(&args[1]);
    let output_dir: Option<PathBuf> = args.get(2).map(PathBuf::from);

    if input.is_dir() {
        collect_folder(&input, output_dir.as_deref());
    } else if input.is_file() {
        collect_single(&input, output_dir.as_deref());
    } else {
        eprintln!("Error: '{}' not found", input.display());
        std::process::exit(1);
    }
}

fn collect_single(aep_path: &Path, output_dir: Option<&Path>) {
    let ext = aep_path.extension().unwrap_or_default().to_string_lossy().to_lowercase();
    if ext != "aep" {
        eprintln!("Error: not an .aep file: {}", aep_path.display());
        std::process::exit(1);
    }

    let out = match output_dir {
        Some(dir) => dir.to_path_buf(),
        None => {
            let stem = aep_path.file_stem().unwrap_or_default().to_string_lossy();
            aep_path.parent().unwrap_or(Path::new(".")).join(format!("{}_collected", stem))
        }
    };

    let (tx, rx) = mpsc::channel();
    let cancel = Arc::new(AtomicBool::new(false));
    let opts = collect::CollectOptions {
        aep_path: aep_path.to_path_buf(), output_dir: out, target_version: None,
    };

    std::thread::spawn(move || {
        collect::collect_project(&opts, &tx, &cancel);
    });

    for msg in rx {
        match msg {
            collect::ProgressMsg::Info(text) => println!("{}", text),
            collect::ProgressMsg::Asset { text, .. } => println!("  {}", text),
            collect::ProgressMsg::FileStart { name, .. } => println!("=== {} ===", name),
            collect::ProgressMsg::FileDone => {}
            collect::ProgressMsg::AllDone => {}
            collect::ProgressMsg::Error(text) => eprintln!("Error: {}", text),
        }
    }
}

fn collect_folder(dir: &Path, output_base: Option<&Path>) {
    let files = collect::find_aep_files(dir);
    if files.is_empty() {
        eprintln!("No .aep files found in {}", dir.display());
        std::process::exit(1);
    }

    let base = output_base.unwrap_or(dir).to_path_buf();
    let (tx, rx) = mpsc::channel();
    let cancel = Arc::new(AtomicBool::new(false));

    std::thread::spawn(move || {
        collect::collect_batch(&files, &base, None, &tx, &cancel);
    });

    for msg in rx {
        match msg {
            collect::ProgressMsg::Info(text) => println!("{}", text),
            collect::ProgressMsg::Asset { text, .. } => println!("  {}", text),
            collect::ProgressMsg::FileStart { name, file_idx, file_total } => {
                println!("\n{}", "=".repeat(70));
                println!("{} ({}/{})", name, file_idx + 1, file_total);
            }
            collect::ProgressMsg::FileDone | collect::ProgressMsg::AllDone => {}
            collect::ProgressMsg::Error(text) => eprintln!("Error: {}", text),
        }
    }
}

fn print_usage() {
    println!("aep-collect — Lightweight AEP project file collector");
    println!();
    println!("Usage:");
    println!("  aep-collect                         Launch GUI");
    println!("  aep-collect <file.aep> [output_dir]  Collect single file (CLI)");
    println!("  aep-collect <folder> [output_dir]     Batch collect folder (CLI)");
}
