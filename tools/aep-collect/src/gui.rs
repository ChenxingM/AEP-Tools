//! egui-based GUI for the AEP collector.

use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc};
use std::thread;

use eframe::egui;

use crate::collect::{self, CollectOptions, ProgressMsg};
use crate::version::{self, KNOWN_VERSIONS};

const WIN_W: f32 = 620.0;
const WIN_H: f32 = 480.0;

pub fn run_gui() {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title(collect::APP_ABOUT)
            .with_inner_size([WIN_W, WIN_H])
            .with_min_inner_size([WIN_W, WIN_H])
            .with_max_inner_size([WIN_W, WIN_H])
            .with_resizable(false),
        ..Default::default()
    };
    let _ = eframe::run_native(collect::APP_ABOUT, options, Box::new(|cc| {
        setup_fonts(&cc.egui_ctx);
        Ok(Box::new(App::new()))
    }));
}

fn setup_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();
    for font_path in &[
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\msgothic.ttc",
        "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\YuGothM.ttc",
    ] {
        if let Ok(data) = std::fs::read(font_path) {
            fonts.font_data.insert("cjk".to_owned(), egui::FontData::from_owned(data).into());
            fonts.families.entry(egui::FontFamily::Proportional).or_default().push("cjk".to_owned());
            fonts.families.entry(egui::FontFamily::Monospace).or_default().push("cjk".to_owned());
            break;
        }
    }
    ctx.set_fonts(fonts);
}

struct App {
    // Queued AEP files (supports multiple files + folders)
    queued_files: Vec<PathBuf>,
    input_display: String,
    output_path: String,
    console_lines: Vec<String>,
    file_progress: f32,
    file_current: usize,
    file_total: usize,
    file_name: String,
    asset_progress: f32,
    asset_current: usize,
    asset_total: usize,
    is_batch: bool,
    started: bool,
    running: bool,
    done: bool,
    rx: Option<mpsc::Receiver<ProgressMsg>>,
    cancel: Arc<AtomicBool>,
    convert_version: bool,
    selected_version_idx: usize,
    current_version_label: String,
}

impl App {
    fn new() -> Self {
        Self {
            queued_files: Vec::new(),
            input_display: String::new(),
            output_path: String::new(),
            console_lines: vec!["Ready".into()],
            file_progress: 0.0, file_current: 0, file_total: 0, file_name: String::new(),
            asset_progress: 0.0, asset_current: 0, asset_total: 0,
            is_batch: false,
            started: false, running: false, done: false, rx: None, cancel: Arc::new(AtomicBool::new(false)),
            convert_version: false,
            selected_version_idx: KNOWN_VERSIONS.len() - 1,
            current_version_label: String::new(),
        }
    }

    fn set_input_files(&mut self, files: Vec<PathBuf>) {
        self.queued_files = files;
        self.update_input_display();
        self.detect_version();
    }

    fn add_input_files(&mut self, files: Vec<PathBuf>) {
        for f in files {
            if !self.queued_files.iter().any(|q| q == &f) {
                self.queued_files.push(f);
            }
        }
        self.update_input_display();
        self.detect_version();
    }

    fn update_input_display(&mut self) {
        self.input_display = self.queued_files.iter()
            .map(|p| p.to_string_lossy().to_string())
            .collect::<Vec<_>>()
            .join("\n");
    }

    fn sync_files_from_display(&mut self) {
        self.queued_files = self.input_display.lines()
            .map(|l| l.trim())
            .filter(|l| !l.is_empty())
            .map(PathBuf::from)
            .collect();
        self.detect_version();
    }

    fn resolve_files(&self) -> Vec<PathBuf> {
        let mut result = Vec::new();
        for path in &self.queued_files {
            if path.is_dir() {
                result.extend(collect::find_aep_files(path));
            } else if path.is_file() {
                result.push(path.clone());
            }
        }
        result
    }

    fn auto_output(&mut self) {
        if !self.output_path.is_empty() || self.queued_files.is_empty() {
            return;
        }
        let first = &self.queued_files[0];
        if first.is_file() {
            if self.queued_files.len() == 1 {
                let stem = first.file_stem().unwrap_or_default().to_string_lossy();
                if let Some(parent) = first.parent() {
                    self.output_path = parent.join(format!("{}_collected", stem))
                        .to_string_lossy().to_string();
                }
            } else if let Some(parent) = first.parent() {
                self.output_path = parent.join("_collected_aeps")
                    .to_string_lossy().to_string();
            }
        } else if first.is_dir() {
            self.output_path = first.to_string_lossy().to_string();
        }
    }

    fn start_collect(&mut self) {
        let files = self.resolve_files();
        if files.is_empty() { return; }

        self.console_lines.clear();
        self.file_progress = 0.0;
        self.file_current = 0;
        self.file_total = files.len();
        self.file_name.clear();
        self.asset_progress = 0.0;
        self.asset_current = 0;
        self.asset_total = 0;
        self.done = false;
        self.started = true;
        self.running = true;
        self.cancel = Arc::new(AtomicBool::new(false));
        self.is_batch = files.len() > 1;

        let target_version = if self.convert_version {
            let (head_bytes, _) = KNOWN_VERSIONS[self.selected_version_idx];
            Some(head_bytes)
        } else {
            None
        };

        let (tx, rx) = mpsc::channel();
        self.rx = Some(rx);

        if files.len() == 1 {
            let aep_path = files[0].clone();
            let output_dir = if self.output_path.is_empty() {
                let stem = aep_path.file_stem().unwrap_or_default().to_string_lossy();
                aep_path.parent().unwrap_or(std::path::Path::new("."))
                    .join(format!("{}_collected", stem))
            } else {
                PathBuf::from(&self.output_path)
            };
            let name = aep_path.file_name().unwrap_or_default().to_string_lossy().to_string();
            let tx2 = tx.clone();
            let cancel = self.cancel.clone();
            thread::spawn(move || {
                let _ = tx.send(ProgressMsg::FileStart { file_idx: 0, file_total: 1, name });
                let opts = CollectOptions { aep_path, output_dir, target_version };
                collect::collect_project(&opts, &tx2, &cancel);
                let _ = tx2.send(ProgressMsg::FileDone);
                let _ = tx2.send(ProgressMsg::AllDone);
            });
        } else {
            let output_base = if self.output_path.is_empty() {
                files[0].parent().unwrap_or(std::path::Path::new(".")).to_path_buf()
            } else {
                PathBuf::from(&self.output_path)
            };
            let cancel = self.cancel.clone();
            thread::spawn(move || {
                collect::collect_batch(&files, &output_base, target_version, &tx, &cancel);
            });
        }
    }

    fn start_convert_only(&mut self) {
        let files = self.resolve_files();
        if files.is_empty() { return; }

        let (target_head, _) = KNOWN_VERSIONS[self.selected_version_idx];

        self.console_lines.clear();
        self.file_progress = 0.0;
        self.file_current = 0;
        self.file_total = files.len();
        self.file_name.clear();
        self.asset_progress = 0.0;
        self.asset_current = 0;
        self.asset_total = 0;
        self.done = false;
        self.started = true;
        self.running = true;
        self.cancel = Arc::new(AtomicBool::new(false));
        self.is_batch = files.len() > 1;

        let output_dir = if self.output_path.is_empty() {
            None
        } else {
            Some(PathBuf::from(&self.output_path))
        };

        let (tx, rx) = mpsc::channel();
        self.rx = Some(rx);
        let cancel = self.cancel.clone();

        thread::spawn(move || {
            collect::convert_version_only(
                &files, target_head,
                output_dir.as_deref(), &tx, &cancel,
            );
        });
    }

    fn poll_messages(&mut self) {
        let rx = match &self.rx { Some(rx) => rx, None => return };
        while let Ok(msg) = rx.try_recv() {
            match msg {
                ProgressMsg::Info(text) => {
                    self.console_lines.push(text);
                    if self.console_lines.len() > 5000 {
                        self.console_lines.drain(..1000);
                    }
                }
                ProgressMsg::FileStart { file_idx, file_total, name } => {
                    self.file_current = file_idx + 1;
                    self.file_total = file_total;
                    self.file_name = name.clone();
                    self.file_progress = file_idx as f32 / file_total as f32;
                    self.asset_progress = 0.0;
                    self.asset_current = 0;
                    self.asset_total = 0;
                    if file_total > 1 {
                        self.console_lines.push(format!("--- {} ({}/{}) ---", name, file_idx + 1, file_total));
                    }
                }
                ProgressMsg::Asset { current, total, text } => {
                    self.console_lines.push(format!("  {}", text));
                    if self.console_lines.len() > 5000 {
                        self.console_lines.drain(..1000);
                    }
                    self.asset_current = current;
                    self.asset_total = total;
                    if total > 0 {
                        self.asset_progress = current as f32 / total as f32;
                    }
                }
                ProgressMsg::FileDone => {
                    if self.file_total > 0 {
                        self.file_progress = self.file_current as f32 / self.file_total as f32;
                    }
                    self.asset_progress = 1.0;
                }
                ProgressMsg::AllDone => {
                    self.running = false;
                    self.done = true;
                    self.file_progress = 1.0;
                    self.asset_progress = 1.0;
                }
                ProgressMsg::Error(text) => {
                    self.console_lines.push(format!("ERROR: {}", text));
                    // Don't stop — per-file errors should not halt the batch.
                    // AllDone will signal completion.
                }
            }
        }
    }

    fn detect_version(&mut self) {
        self.current_version_label.clear();
        if let Some(path) = self.queued_files.first() {
            if path.is_file() {
                // Read only first 8KB — head chunk is near the beginning
                use std::io::Read;
                let mut buf = vec![0u8; 8192];
                if let Ok(mut f) = std::fs::File::open(path) {
                    let n = f.read(&mut buf).unwrap_or(0);
                    buf.truncate(n);
                    if let Ok((root, _)) = crate::rifx::parse_aep(&buf) {
                        if let Some(ver) = version::read_version(&root) {
                            self.current_version_label = ver.label();
                        }
                    }
                }
            }
        }
    }

    fn handle_drop(&mut self, ctx: &egui::Context) {
        let dropped: Vec<PathBuf> = ctx.input(|i| {
            i.raw.dropped_files.iter()
                .filter_map(|d| d.path.clone())
                .collect()
        });
        if dropped.is_empty() { return; }

        let mut files = Vec::new();
        for path in dropped {
            if path.is_dir() {
                files.extend(collect::find_aep_files(&path));
            } else if path.is_file() {
                if let Some(ext) = path.extension() {
                    if ext.to_string_lossy().to_lowercase() == "aep" {
                        files.push(path);
                    }
                }
            }
        }
        if !files.is_empty() {
            self.add_input_files(files);
            self.auto_output();
        }
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if self.running {
            self.poll_messages();
            ctx.request_repaint();
        }

        self.handle_drop(ctx);
        ctx.set_visuals(egui::Visuals::dark());

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.spacing_mut().item_spacing.y = 4.0;

            let label_w = 48.0;
            let btn_w = 26.0;

            // Input
            ui.horizontal(|ui| {
                ui.allocate_ui_with_layout(
                    egui::vec2(label_w, 60.0),
                    egui::Layout::left_to_right(egui::Align::TOP),
                    |ui| { ui.label("Input:"); },
                );
                let edit_w = ui.available_width() - btn_w - ui.spacing().item_spacing.x;
                let response = ui.add(
                    egui::TextEdit::multiline(&mut self.input_display)
                        .desired_width(edit_w)
                        .desired_rows(3)
                        .hint_text("Drop AEP files or folder here..."),
                );
                if response.changed() {
                    self.sync_files_from_display();
                }
                if ui.button("...").clicked() {
                    if let Some(paths) = rfd::FileDialog::new()
                        .add_filter("AEP files", &["aep"])
                        .add_filter("All files", &["*"])
                        .pick_files()
                    {
                        self.set_input_files(paths);
                        self.auto_output();
                    }
                }
            });

            // Output
            ui.horizontal(|ui| {
                ui.add_sized([label_w, 18.0], egui::Label::new("Output:"));
                let edit_w = ui.available_width() - btn_w - ui.spacing().item_spacing.x;
                ui.add(
                    egui::TextEdit::singleline(&mut self.output_path)
                        .desired_width(edit_w)
                        .hint_text("Output directory..."),
                );
                if ui.button("...").clicked() {
                    if let Some(path) = rfd::FileDialog::new().pick_folder() {
                        self.output_path = path.to_string_lossy().to_string();
                    }
                }
            });

            ui.add_space(2.0);

            // Version conversion
            ui.horizontal(|ui| {
                ui.add_enabled(!self.running, egui::Checkbox::new(&mut self.convert_version, "Convert version"));
                if !self.current_version_label.is_empty() {
                    ui.label(egui::RichText::new(format!("Current: {}", self.current_version_label))
                        .color(egui::Color32::from_rgb(156, 220, 254)).small());
                }
            });
            if self.convert_version {
                ui.add_enabled_ui(!self.running, |ui| {
                    ui.horizontal(|ui| {
                        ui.add_space(24.0);
                        ui.label("Target:");
                        egui::ComboBox::from_id_salt("ver").width(120.0)
                            .selected_text(KNOWN_VERSIONS[self.selected_version_idx].1)
                            .show_ui(ui, |ui| {
                                for (i, (_, label)) in KNOWN_VERSIONS.iter().enumerate() {
                                    ui.selectable_value(&mut self.selected_version_idx, i, *label);
                                }
                            });
                        ui.label(egui::RichText::new("Only changes version number, not features")
                            .color(egui::Color32::from_rgb(232, 166, 36)).small());
                    });
                });
            }

            ui.add_space(2.0);

            // Progress bars
            if self.started {
                if self.is_batch {
                    let file_pct = (self.file_progress * 100.0) as u32;
                    ui.add(egui::ProgressBar::new(self.file_progress).text(format!("{}%", file_pct)));
                }
                let asset_pct = (self.asset_progress * 100.0) as u32;
                ui.add(egui::ProgressBar::new(self.asset_progress).text(format!("{}%", asset_pct)));
            }

            // Button + status
            ui.horizontal(|ui| {
                let can_start = !self.running && !self.queued_files.is_empty();
                if ui.add_enabled(
                    can_start,
                    egui::Button::new(egui::RichText::new("Collect").size(14.0))
                        .min_size(egui::vec2(100.0, 28.0))
                ).clicked() {
                    self.start_collect();
                }
                let can_convert = can_start && self.convert_version;
                if ui.add_enabled(
                    can_convert,
                    egui::Button::new(egui::RichText::new("Convert Version").size(14.0))
                        .min_size(egui::vec2(100.0, 28.0))
                ).clicked() {
                    self.start_convert_only();
                }
                if self.running {
                    if ui.add(
                        egui::Button::new(egui::RichText::new("Stop").size(14.0))
                            .min_size(egui::vec2(60.0, 28.0))
                    ).clicked() {
                        self.cancel.store(true, Ordering::Relaxed);
                    }
                }
                if self.running {
                    ui.spinner();
                    if self.is_batch {
                        ui.label(format!(
                            "Collecting {} ({}/{})  {}/{}",
                            self.file_name, self.file_current, self.file_total,
                            self.asset_current, self.asset_total
                        ));
                    } else {
                        ui.label(format!("Collecting...  {}/{}", self.asset_current, self.asset_total));
                    }
                }
                if self.done && !self.running {
                    ui.label(egui::RichText::new("Complete").color(COL_OK));
                }
            });

            ui.add_space(2.0);

            // Console
            let available = ui.available_height();
            egui::Frame::new()
                .fill(egui::Color32::from_rgb(24, 24, 24))
                .corner_radius(3.0)
                .inner_margin(4.0)
                .show(ui, |ui| {
                    egui::ScrollArea::vertical()
                        .id_salt("console_scroll")
                        .max_height(available - 12.0)
                        .auto_shrink([false, false])
                        .stick_to_bottom(true)
                        .show(ui, |ui| {
                            ui.set_min_width(ui.available_width());
                            ui.set_min_height(available - 20.0);
                            for line in &self.console_lines {
                                let color = line_color(line);
                                ui.label(egui::RichText::new(line).color(color).monospace().size(11.0));
                            }
                        });
                });
        });
    }
}

const COL_OK: egui::Color32 = egui::Color32::from_rgb(78, 201, 176);
const COL_ERR: egui::Color32 = egui::Color32::from_rgb(224, 80, 80);
const COL_MISS: egui::Color32 = egui::Color32::from_rgb(232, 166, 36);
const COL_INFO: egui::Color32 = egui::Color32::from_rgb(156, 220, 254);
const COL_DEFAULT: egui::Color32 = egui::Color32::from_rgb(200, 200, 200);

fn line_color(line: &str) -> egui::Color32 {
    let trimmed = line.trim_start();
    if trimmed.starts_with("[OK]") { COL_OK }
    else if trimmed.starts_with("[ERR]") || trimmed.starts_with("ERROR:") { COL_ERR }
    else if trimmed.starts_with("[MISS]") { COL_MISS }
    else if trimmed.starts_with("Done:") || trimmed.starts_with("Version:") || trimmed.starts_with("Assets:") { COL_INFO }
    else if trimmed.starts_with("---") { COL_INFO }
    else { COL_DEFAULT }
}
