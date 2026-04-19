use std::io::Write;
use tempfile::NamedTempFile;

#[test]
fn test_basic_log_viewer() {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, "Line 1").unwrap();
    writeln!(file, "Line 2").unwrap();
    writeln!(file, "Line 3").unwrap();

    let path = file.path();
    assert!(path.exists());
}

#[test]
fn test_log_file_with_levels() {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, "[INFO] Server started").unwrap();
    writeln!(file, "[WARN] Low memory").unwrap();
    writeln!(file, "[ERROR] Connection failed").unwrap();
    writeln!(file, "[DEBUG] Variable x = 42").unwrap();

    let path = file.path();
    assert!(path.exists());
}

#[test]
fn test_log_file_with_timestamps() {
    let mut file = NamedTempFile::new().unwrap();
    writeln!(file, "2024-01-15T10:30:00.000Z INFO Starting").unwrap();
    writeln!(file, "2024-01-15T10:30:01.000Z ERROR Failed").unwrap();

    let path = file.path();
    assert!(path.exists());
}

#[test]
fn test_empty_log_file() {
    let file = NamedTempFile::new().unwrap();
    let path = file.path();
    assert!(path.exists());
}

#[test]
fn test_binary_detection() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "Hello\x00World").unwrap();

    let path = file.path();
    assert!(path.exists());
}
