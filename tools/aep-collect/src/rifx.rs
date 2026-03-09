//! Minimal RIFX parser — only parses enough structure for asset path extraction.

use std::fmt;
use std::str;

/// A node in the RIFX chunk tree.
pub struct Chunk {
    pub header: [u8; 4],
    pub data: ChunkData,
}

pub enum ChunkData {
    /// Raw binary data (most chunks — idta, sspc, opti, tdmn, wsnm, etc.)
    Raw(Vec<u8>),
    /// UTF-8 string (Utf8, alas)
    Str(String),
    /// Container with children (LIST, tdsn, fnam, pdnm)
    List {
        list_type: [u8; 4],
        children: Vec<Chunk>,
    },
}

impl Chunk {
    /// Effective name: for LIST chunks returns the list type, otherwise the header.
    pub fn name(&self) -> &[u8; 4] {
        if let ChunkData::List { list_type, .. } = &self.data {
            if &self.header == b"LIST" {
                return list_type;
            }
        }
        &self.header
    }

    /// Get children if this is a container chunk.
    pub fn children(&self) -> &[Chunk] {
        match &self.data {
            ChunkData::List { children, .. } => children,
            _ => &[],
        }
    }

    /// Get mutable children (returns None for non-container chunks).
    pub fn children_mut(&mut self) -> Option<&mut Vec<Chunk>> {
        match &mut self.data {
            ChunkData::List { children, .. } => Some(children),
            _ => None,
        }
    }

    /// Find first child by effective name.
    pub fn find(&self, name: &[u8; 4]) -> Option<&Chunk> {
        self.children().iter().find(|c| c.name() == name)
    }

    /// Find first child by effective name (mutable).
    pub fn find_mut(&mut self, name: &[u8; 4]) -> Option<&mut Chunk> {
        self.children_mut()?.iter_mut().find(|c| c.name() == name)
    }

    /// Get string data.
    pub fn as_str(&self) -> Option<&str> {
        match &self.data {
            ChunkData::Str(s) => Some(s),
            _ => None,
        }
    }

    /// Get mutable string reference.
    pub fn as_str_mut(&mut self) -> Option<&mut String> {
        match &mut self.data {
            ChunkData::Str(s) => Some(s),
            _ => None,
        }
    }

    /// Get raw bytes.
    pub fn as_bytes(&self) -> Option<&[u8]> {
        match &self.data {
            ChunkData::Raw(b) => Some(b),
            _ => None,
        }
    }

    /// Get mutable raw bytes.
    pub fn as_bytes_mut(&mut self) -> Option<&mut Vec<u8>> {
        match &mut self.data {
            ChunkData::Raw(b) => Some(b),
            _ => None,
        }
    }
}

impl fmt::Debug for Chunk {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = str::from_utf8(self.name()).unwrap_or("????");
        write!(f, "Chunk({})", name)
    }
}

/// RIFX parser state.
struct Parser<'a> {
    data: &'a [u8],
    offset: usize,
    big_endian: bool,
}

impl<'a> Parser<'a> {
    fn remaining(&self) -> usize {
        self.data.len().saturating_sub(self.offset)
    }

    fn read_bytes(&mut self, n: usize) -> Result<&'a [u8], String> {
        if self.offset + n > self.data.len() {
            return Err(format!(
                "read past end: offset={}, need={}, have={}",
                self.offset, n, self.remaining()
            ));
        }
        let s = &self.data[self.offset..self.offset + n];
        self.offset += n;
        Ok(s)
    }

    fn read_4(&mut self) -> Result<[u8; 4], String> {
        let b = self.read_bytes(4)?;
        Ok([b[0], b[1], b[2], b[3]])
    }

    fn read_u32(&mut self) -> Result<u32, String> {
        let b = self.read_4()?;
        Ok(if self.big_endian {
            u32::from_be_bytes(b)
        } else {
            u32::from_le_bytes(b)
        })
    }

}

/// Parse an AEP binary file into a chunk tree.
/// Returns (root_chunk, big_endian).
pub fn parse_aep(data: &[u8]) -> Result<(Chunk, bool), String> {
    if data.len() < 12 {
        return Err("file too small".into());
    }
    let mut p = Parser {
        data,
        offset: 0,
        big_endian: true,
    };

    let header = p.read_4()?;
    match &header {
        b"RIFF" => p.big_endian = false,
        b"RIFX" => p.big_endian = true,
        _ => return Err(format!("not RIFF/RIFX: {:?}", header)),
    }

    let size = p.read_u32()? as usize;
    let file_id = p.read_4()?;
    if &file_id != b"Egg!" {
        return Err(format!("not AEP (expected Egg!, got {:?})", file_id));
    }

    let content_size = (size.saturating_sub(4)).min(p.remaining());
    let big_endian = p.big_endian;
    let children = parse_children(&mut p, content_size)?;

    let root = Chunk {
        header,
        data: ChunkData::List {
            list_type: file_id,
            children,
        },
    };
    Ok((root, big_endian))
}

fn parse_children(p: &mut Parser, size: usize) -> Result<Vec<Chunk>, String> {
    let end = (p.offset + size).min(p.data.len());
    let mut children = Vec::new();
    while p.offset < end && p.remaining() >= 8 {
        children.push(parse_chunk(p)?);
    }
    p.offset = end; // Clamp to parent boundary
    Ok(children)
}

fn parse_chunk(p: &mut Parser) -> Result<Chunk, String> {
    let header = p.read_4()?;
    let raw_size = p.read_u32()? as usize;
    let size = raw_size.min(p.remaining());

    let chunk = parse_chunk_data(p, header, size)?;

    // Pad to even boundary
    if raw_size % 2 == 1 && p.offset < p.data.len() {
        p.offset += 1;
    }
    Ok(chunk)
}

fn parse_chunk_data(p: &mut Parser, header: [u8; 4], size: usize) -> Result<Chunk, String> {
    if &header == b"LIST" {
        if size < 4 {
            let raw = p.read_bytes(size)?;
            return Ok(Chunk { header, data: ChunkData::Raw(raw.to_vec()) });
        }
        let list_type = p.read_4()?;

        // btdk: store as raw bytes
        if &list_type == b"btdk" {
            let raw = p.read_bytes(size - 4)?;
            return Ok(Chunk {
                header: list_type,
                data: ChunkData::Raw(raw.to_vec()),
            });
        }

        let children = parse_children(p, size - 4)?;
        return Ok(Chunk {
            header,
            data: ChunkData::List {
                list_type,
                children,
            },
        });
    }

    // Non-LIST containers (tdsn, fnam, pdnm) — children without type prefix
    if &header == b"tdsn" || &header == b"fnam" || &header == b"pdnm" {
        let children = parse_children(p, size)?;
        return Ok(Chunk {
            header,
            data: ChunkData::List {
                list_type: [0; 4],
                children,
            },
        });
    }

    match &header {
        b"Utf8" | b"alas" => {
            let raw = p.read_bytes(size)?;
            // Only decode as string if valid UTF-8; otherwise store as Raw
            // to avoid from_utf8_lossy changing byte length with replacement chars
            match std::str::from_utf8(raw) {
                Ok(s) => Ok(Chunk { header, data: ChunkData::Str(s.to_string()) }),
                Err(_) => Ok(Chunk { header, data: ChunkData::Raw(raw.to_vec()) }),
            }
        }
        // All other chunks: store raw bytes for perfect round-trip
        _ => {
            let raw = p.read_bytes(size)?;
            Ok(Chunk {
                header,
                data: ChunkData::Raw(raw.to_vec()),
            })
        }
    }
}

/// Serialize the chunk tree back to binary.
pub fn serialize(root: &Chunk, big_endian: bool) -> Vec<u8> {
    let mut buf = Vec::new();
    write_root(&mut buf, root, big_endian);
    buf
}

fn pack_u32(val: u32, big_endian: bool) -> [u8; 4] {
    if big_endian {
        val.to_be_bytes()
    } else {
        val.to_le_bytes()
    }
}

fn write_root(buf: &mut Vec<u8>, root: &Chunk, big_endian: bool) {
    buf.extend_from_slice(&root.header);
    let size_pos = buf.len();
    buf.extend_from_slice(&[0; 4]);

    if let ChunkData::List {
        list_type,
        children,
    } = &root.data
    {
        buf.extend_from_slice(list_type);
        for child in children {
            write_chunk(buf, child, big_endian);
        }
    }

    let data_size = (buf.len() - size_pos - 4) as u32;
    buf[size_pos..size_pos + 4].copy_from_slice(&pack_u32(data_size, big_endian));
}

fn write_chunk(buf: &mut Vec<u8>, chunk: &Chunk, big_endian: bool) {
    match &chunk.data {
        ChunkData::List {
            list_type,
            children,
        } => {
            if &chunk.header == b"LIST" {
                // LIST [size] [type] [children...]
                buf.extend_from_slice(b"LIST");
                let size_pos = buf.len();
                buf.extend_from_slice(&[0; 4]);
                buf.extend_from_slice(list_type);
                for child in children {
                    write_chunk(buf, child, big_endian);
                }
                let data_size = (buf.len() - size_pos - 4) as u32;
                buf[size_pos..size_pos + 4].copy_from_slice(&pack_u32(data_size, big_endian));
            } else {
                // Non-LIST container (tdsn, fnam, pdnm) [header] [size] [children...]
                buf.extend_from_slice(&chunk.header);
                let size_pos = buf.len();
                buf.extend_from_slice(&[0; 4]);
                for child in children {
                    write_chunk(buf, child, big_endian);
                }
                let data_size = (buf.len() - size_pos - 4) as u32;
                buf[size_pos..size_pos + 4].copy_from_slice(&pack_u32(data_size, big_endian));
            }
        }
        ChunkData::Str(s) => {
            let encoded = s.as_bytes();
            buf.extend_from_slice(&chunk.header);
            buf.extend_from_slice(&pack_u32(encoded.len() as u32, big_endian));
            buf.extend_from_slice(encoded);
            if encoded.len() % 2 == 1 {
                buf.push(0);
            }
        }
        ChunkData::Raw(data) => {
            if &chunk.header == b"btdk" {
                // btdk is stored as LIST btdk [data]
                buf.extend_from_slice(b"LIST");
                let size = (data.len() + 4) as u32;
                buf.extend_from_slice(&pack_u32(size, big_endian));
                buf.extend_from_slice(b"btdk");
                buf.extend_from_slice(data);
                if data.len() % 2 == 1 {
                    buf.push(0);
                }
            } else {
                buf.extend_from_slice(&chunk.header);
                buf.extend_from_slice(&pack_u32(data.len() as u32, big_endian));
                buf.extend_from_slice(data);
                if data.len() % 2 == 1 {
                    buf.push(0);
                }
            }
        }
    }
}
