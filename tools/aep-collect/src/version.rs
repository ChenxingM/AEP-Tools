//! AE version reading and writing from RIFX chunk tree.

use crate::rifx::Chunk;

/// Decoded AE version information.
#[derive(Debug, Clone)]
pub struct AeVersion {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
    pub _build: u32,
    pub os_code: u32,
    pub beta: bool,
}

impl AeVersion {
    pub fn display(&self) -> String {
        if self.patch > 0 {
            format!("{}.{}.{}", self.major, self.minor, self.patch)
        } else {
            format!("{}.{}", self.major, self.minor)
        }
    }

    pub fn os_name(&self) -> &'static str {
        match self.os_code {
            12 => "Windows",
            13 => "macOS",
            14 => "macOS ARM",
            _ => "Unknown",
        }
    }

    pub fn label(&self) -> String {
        let beta_str = if self.beta { " Beta" } else { "" };
        format!("AE {}{} ({})", self.display(), beta_str, self.os_name())
    }
}

/// Known AE versions: (raw_version_id, display_label).
pub const KNOWN_VERSIONS: &[(u32, &str)] = &[
    (0x0B3B2E04, "23.6.5 (2023)"),
    (0x0F000604, "24.0 (2024)"),
    (0x0F008604, "24.1"),
    (0x0F010604, "24.2"),
    (0x0F018604, "24.3"),
    (0x0F020604, "24.4"),
    (0x0F028604, "24.5"),
    (0x0F030604, "24.6"),
    (0x0F080604, "25.0 (2025)"),
    (0x0F088604, "25.1"),
    (0x0F090604, "25.2"),
    (0x0F098604, "25.3"),
    (0x0F0A0604, "25.4"),
    (0x0F0A8604, "25.5"),
    (0x0F0B0604, "25.6"),
    (0x0F100604, "26.0 (2026)"),
];

/// Decode version_id bit fields.
pub fn decode_version_id(vid: u32) -> AeVersion {
    let maj_a = (vid >> 26) & 0x1F;
    let os_code = (vid >> 22) & 0x0F;
    let maj_b = (vid >> 19) & 0x07;
    let minor = (vid >> 15) & 0x0F;
    let patch = (vid >> 11) & 0x0F;
    let beta_flag = (vid >> 9) & 0x01;
    let build = vid & 0xFF;
    let major = maj_a * 8 + maj_b;

    AeVersion {
        major,
        minor,
        patch,
        _build: build,
        os_code,
        beta: beta_flag == 0,
    }
}



/// Read AE version from chunk tree.
pub fn read_version(root: &Chunk) -> Option<AeVersion> {
    let head = root.find(b"head")?;
    let data = head.as_bytes()?;
    if data.len() < 8 {
        return None;
    }
    let vid = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);
    Some(decode_version_id(vid))
}

/// Write a raw version_id to chunk tree (head and svap chunks).
pub fn write_version(root: &mut Chunk, vid: u32) {
    let vid_bytes = vid.to_be_bytes();

    // Update head chunk [4:8]
    if let Some(head) = root.find_mut(b"head") {
        if let Some(data) = head.as_bytes_mut() {
            if data.len() >= 8 {
                data[4..8].copy_from_slice(&vid_bytes);
            }
        }
    }

    // Update svap chunk (4 bytes = version_id)
    if let Some(svap) = root.find_mut(b"svap") {
        if let Some(data) = svap.as_bytes_mut() {
            if data.len() >= 4 {
                data[0..4].copy_from_slice(&vid_bytes);
            }
        }
    }
}
