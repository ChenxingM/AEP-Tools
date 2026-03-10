//! AE version reading and writing from RIFX chunk tree.

use crate::rifx::Chunk;

/// Decoded AE version information.
#[derive(Debug, Clone)]
pub struct AeVersion {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
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

/// Known AE versions: (head[0..8] bytes, display_label).
/// head[0:2] = format_major (u16 BE), head[2:4] = format_sub (u16 BE), head[4:8] = version_id (u32 BE).
/// Values extracted from real AEP files saved by each AE version.
pub const KNOWN_VERSIONS: &[([u8; 8], &str)] = &[
    ([0x00, 0x5E, 0x00, 0x09, 0x0B, 0x3B, 0x06, 0x37], "23.6 (2023)"),
    ([0x00, 0x5F, 0x00, 0x06, 0x0F, 0x03, 0x06, 0x41], "24.6 (2024)"),
    ([0x00, 0x60, 0x00, 0x01, 0x0F, 0x08, 0x86, 0x44], "25.1 (2025)"),
    ([0x00, 0x60, 0x00, 0x06, 0x0F, 0x0A, 0x06, 0x56], "25.4"),
    ([0x00, 0x61, 0x00, 0x02, 0x0F, 0x10, 0x06, 0x43], "26.0 (2026)"),
];

/// Decode version_id bit fields.
pub fn decode_version_id(vid: u32) -> AeVersion {
    let maj_a = (vid >> 26) & 0x1F;
    let os_code = (vid >> 22) & 0x0F;
    let maj_b = (vid >> 19) & 0x07;
    let minor = (vid >> 15) & 0x0F;
    let patch = (vid >> 11) & 0x0F;
    let beta_flag = (vid >> 9) & 0x01;
    let major = maj_a * 8 + maj_b;

    AeVersion {
        major,
        minor,
        patch,
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

/// Write version to chunk tree: head[0..8] (format version + version_id).
/// svap is intentionally NOT modified — it stores "last saved by" which is unrelated.
pub fn write_version(root: &mut Chunk, head_bytes: &[u8; 8]) {
    if let Some(head) = root.find_mut(b"head") {
        if let Some(data) = head.as_bytes_mut() {
            if data.len() >= 8 {
                data[..8].copy_from_slice(head_bytes);
            }
        }
    }
}
