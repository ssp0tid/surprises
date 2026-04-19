use arboard::Clipboard;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

use crate::errors::{PassgenError, Result};

static CLIPBOARD_INITIALIZED: AtomicBool = AtomicBool::new(false);

pub fn copy_to_clipboard(password: &str) -> Result<()> {
    let mut clipboard = Clipboard::new()
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))?;
    
    clipboard.set_text(password)
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))?;
    
    CLIPBOARD_INITIALIZED.store(true, Ordering::SeqCst);
    
    Ok(())
}

pub fn clear_clipboard() -> Result<()> {
    let mut clipboard = Clipboard::new()
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))?;
    
    clipboard.set_text("")
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))?;
    
    CLIPBOARD_INITIALIZED.store(false, Ordering::SeqCst);
    
    Ok(())
}

pub fn copy_with_timeout(password: &str, timeout_secs: u64) -> Result<()> {
    copy_to_clipboard(password)?;
    
    if timeout_secs > 0 {
        let timeout = Duration::from_secs(timeout_secs);
        thread::sleep(timeout);
        clear_clipboard()?;
    }
    
    Ok(())
}

pub fn copy_async(password: String, timeout_secs: u64) {
    let password_clone = password.clone();
    
    thread::spawn(move || {
        let _ = copy_to_clipboard(&password_clone);
        
        if timeout_secs > 0 {
            thread::sleep(Duration::from_secs(timeout_secs));
            let _ = clear_clipboard();
        }
    });
}

pub fn get_clipboard_content() -> Result<String> {
    let mut clipboard = Clipboard::new()
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))?;
    
    clipboard.get_text()
        .map_err(|e| PassgenError::ClipboardError(e.to_string()))
}

pub fn has_content() -> bool {
    CLIPBOARD_INITIALIZED.load(Ordering::SeqCst)
}