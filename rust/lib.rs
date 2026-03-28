use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyList};
use std::str;

/// A leaf chunk: header (4-byte ASCII), length, and data (bytes or str).
#[pyclass]
struct Chunk {
    #[pyo3(get)]
    header: String,
    #[pyo3(get, set)]
    length: usize,
    #[pyo3(get, set)]
    data: PyObject, // bytes | str | ChunkList
}

#[pymethods]
impl Chunk {
    #[getter]
    fn name(&self, py: Python<'_>) -> PyResult<String> {
        if self.header == "LIST" {
            if let Ok(cl) = self.data.extract::<PyRef<'_, ChunkList>>(py) {
                return Ok(cl.r#type.clone());
            }
        }
        Ok(self.header.clone())
    }

    #[getter]
    fn list(&self, py: Python<'_>) -> PyResult<Py<ChunkList>> {
        self.data.extract::<Py<ChunkList>>(py).map_err(|_| {
            pyo3::exceptions::PyTypeError::new_err(format!(
                "Chunk '{}' is not a list",
                self.header
            ))
        })
    }
}

/// A named list of child chunks.
#[pyclass]
struct ChunkList {
    #[pyo3(get, set)]
    r#type: String,
    #[pyo3(get)]
    children: Py<PyList>,
}

#[pymethods]
impl ChunkList {
    fn find_optional(&self, py: Python<'_>, name: &str) -> PyResult<Option<PyObject>> {
        let list = self.children.bind(py);
        for item in list.iter() {
            let chunk = item.downcast::<Chunk>()?;
            let cname = chunk.borrow().name(py)?;
            if cname == name {
                return Ok(Some(item.into_pyobject(py)?.unbind()));
            }
        }
        Ok(None)
    }

    fn find(&self, py: Python<'_>, name: &str) -> PyResult<PyObject> {
        self.find_optional(py, name)?.ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("Chunk '{}' not found", name))
        })
    }

    fn find_multiple(&self, py: Python<'_>, names: Vec<String>) -> PyResult<Vec<Option<PyObject>>> {
        let mut result: Vec<Option<PyObject>> = (0..names.len()).map(|_| None).collect();
        let mut found = 0usize;
        let list = self.children.bind(py);
        for item in list.iter() {
            let chunk = item.downcast::<Chunk>()?;
            let cname = chunk.borrow().name(py)?;
            if let Some(idx) = names.iter().position(|n| *n == cname) {
                if result[idx].is_none() {
                    result[idx] = Some(item.into_pyobject(py)?.unbind());
                    found += 1;
                    if found >= names.len() {
                        break;
                    }
                }
            }
        }
        Ok(result)
    }

    fn find_all(&self, py: Python<'_>, name: &str) -> PyResult<Vec<PyObject>> {
        let list = self.children.bind(py);
        let mut result = Vec::new();
        for item in list.iter() {
            let chunk = item.downcast::<Chunk>()?;
            let cname = chunk.borrow().name(py)?;
            if cname == name {
                result.push(item.into_pyobject(py)?.unbind());
            }
        }
        Ok(result)
    }
}

// ── Internal parser ─────────────────────────────────────────────────────────

struct Parser<'a> {
    data: &'a [u8],
    offset: usize,
    big_endian: bool,
}

impl<'a> Parser<'a> {
    fn new(data: &'a [u8]) -> Self {
        Parser {
            data,
            offset: 0,
            big_endian: true,
        }
    }

    #[inline(always)]
    fn check_bounds(&self, n: usize) -> PyResult<()> {
        if self.offset + n > self.data.len() {
            Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Read past end of data: offset {}, requested {} bytes, available {}",
                self.offset,
                n,
                self.data.len() - self.offset
            )))
        } else {
            Ok(())
        }
    }

    fn read_u32(&mut self) -> PyResult<u32> {
        self.check_bounds(4)?;
        let b = &self.data[self.offset..self.offset + 4];
        self.offset += 4;
        Ok(if self.big_endian {
            u32::from_be_bytes([b[0], b[1], b[2], b[3]])
        } else {
            u32::from_le_bytes([b[0], b[1], b[2], b[3]])
        })
    }

    fn read_id(&mut self) -> PyResult<&'a str> {
        self.check_bounds(4)?;
        let s = &self.data[self.offset..self.offset + 4];
        self.offset += 4;
        Ok(str::from_utf8(s).unwrap_or("????"))
    }

    fn read_bytes(&mut self, n: usize) -> PyResult<&'a [u8]> {
        self.check_bounds(n)?;
        let s = &self.data[self.offset..self.offset + n];
        self.offset += n;
        Ok(s)
    }

    fn read_nul_string_utf8(&mut self, n: usize) -> PyResult<String> {
        let bytes = self.read_bytes(n)?;
        let end = bytes.iter().position(|&b| b == 0).unwrap_or(bytes.len());
        Ok(String::from_utf8_lossy(&bytes[..end]).into_owned())
    }

    fn parse_aep(&mut self, py: Python<'_>) -> PyResult<(Py<Chunk>, bool)> {
        let header = self.read_id()?.to_string();
        match header.as_str() {
            "RIFF" => self.big_endian = false,
            "RIFX" => self.big_endian = true,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "Unknown format: '{}' (expected RIFF or RIFX)",
                    header
                )))
            }
        }
        let size = self.read_u32()? as usize;
        let file_id = self.read_id()?;
        if file_id != "Egg!" {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Invalid AEP file (expected 'Egg!', got '{}')",
                file_id
            )));
        }
        // Clamp declared size to actual remaining data
        let content_size = (size - 4).min(self.data.len() - self.offset);
        let cl = self.parse_chunk_list(py, file_id, content_size)?;
        let big_endian = self.big_endian;
        let chunk = Py::new(
            py,
            Chunk {
                header,
                length: size,
                data: cl.into_any(),
            },
        )?;
        Ok((chunk, big_endian))
    }

    fn parse_chunk_list(
        &mut self,
        py: Python<'_>,
        list_type: &str,
        size: usize,
    ) -> PyResult<Py<ChunkList>> {
        let end = (self.offset + size).min(self.data.len());
        let children = PyList::empty(py);
        while self.offset < end && (self.data.len() - self.offset) >= 8 {
            let chunk = self.parse_chunk(py)?;
            children.append(chunk)?;
        }
        self.offset = end; // Clamp to parent boundary
        Py::new(
            py,
            ChunkList {
                r#type: list_type.to_string(),
                children: children.unbind(),
            },
        )
    }

    fn parse_chunk(&mut self, py: Python<'_>) -> PyResult<Py<Chunk>> {
        let header = self.read_id()?.to_string();
        let raw_size = self.read_u32()? as usize;
        // Clamp to remaining data to survive truncated files
        let size = raw_size.min(self.data.len() - self.offset);
        let chunk = self.parse_chunk_data(py, &header, size)?;
        if raw_size % 2 == 1 && self.offset < self.data.len() {
            self.offset += 1;
        }
        Ok(chunk)
    }

    fn parse_chunk_data(
        &mut self,
        py: Python<'_>,
        header: &str,
        size: usize,
    ) -> PyResult<Py<Chunk>> {
        if header == "LIST" {
            if size < 4 {
                let raw = self.read_bytes(size)?;
                return Py::new(py, Chunk {
                    header: header.to_string(), length: size,
                    data: PyBytes::new(py, raw).into_any().unbind(),
                });
            }
            let list_type = self.read_id()?.to_string();

            // btdk: read as raw bytes (COS text data)
            if list_type == "btdk" {
                let raw = self.read_bytes(size - 4)?;
                return Py::new(
                    py,
                    Chunk {
                        header: list_type,
                        length: size,
                        data: PyBytes::new(py, raw).into_any().unbind(),
                    },
                );
            }

            let cl = self.parse_chunk_list(py, &list_type, size - 4)?;
            return Py::new(
                py,
                Chunk {
                    header: header.to_string(),
                    length: size,
                    data: cl.into_any(),
                },
            );
        }

        match header {
            "Utf8" | "alas" => {
                let raw = self.read_bytes(size)?;
                let data = match str::from_utf8(raw) {
                    Ok(s) => s.into_pyobject(py)?.into_any().unbind(),
                    Err(_) => PyBytes::new(py, raw).into_any().unbind(),
                };
                Py::new(py, Chunk { header: header.to_string(), length: size, data })
            }
            "tdmn" => {
                let s = self.read_nul_string_utf8(size)?;
                Py::new(
                    py,
                    Chunk {
                        header: header.to_string(),
                        length: size,
                        data: s.into_pyobject(py)?.into_any().unbind(),
                    },
                )
            }
            // wsnm: store raw bytes for perfect round-trip
            "tdsn" | "fnam" | "pdnm" => {
                let cl = self.parse_chunk_list(py, "", size)?;
                Py::new(
                    py,
                    Chunk {
                        header: header.to_string(),
                        length: size,
                        data: cl.into_any(),
                    },
                )
            }
            _ => {
                let raw = self.read_bytes(size)?;
                Py::new(
                    py,
                    Chunk {
                        header: header.to_string(),
                        length: size,
                        data: PyBytes::new(py, raw).into_any().unbind(),
                    },
                )
            }
        }
    }
}

// ── Public Python API ───────────────────────────────────────────────────────

/// Parse an AEP binary file. Returns (root_chunk, big_endian, trailing_data).
#[pyfunction]
fn parse_riff(py: Python<'_>, data: &[u8]) -> PyResult<(Py<Chunk>, bool, PyObject)> {
    let mut parser = Parser::new(data);
    let (root, big_endian) = parser.parse_aep(py)?;
    let trailing = &data[parser.offset..];
    let trailing_py = PyBytes::new(py, trailing).into_any().unbind();
    Ok((root, big_endian, trailing_py))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Chunk>()?;
    m.add_class::<ChunkList>()?;
    m.add_function(wrap_pyfunction!(parse_riff, m)?)?;
    Ok(())
}
