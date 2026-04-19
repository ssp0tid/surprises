# LNFS - Local Network File Sharing Server

A beautiful, feature-rich file sharing server for your local network. Built with Flask and vanilla JavaScript, featuring a modern dark UI with drag-and-drop uploads, file previews, and mobile support.

## Features

- **🌐 Web Interface** - Modern dark theme UI, fully responsive for mobile devices
- **📁 Directory Browsing** - Navigate folders with breadcrumb navigation
- **⬆️ Drag & Drop Upload** - Upload files via drag-and-drop or file picker with progress bar
- **⬇️ Folder Downloads** - Download entire folders as ZIP archives
- **🖼️ File Preview** - Preview images and text files directly in the browser
- **📱 Mobile QR Code** - Scan QR code to access from mobile devices
- **🔐 Password Protection** - Optional password authentication
- **📂 Create Folders** - Create new directories directly from the UI
- **🔔 Toast Notifications** - Visual feedback for all operations
- **⚡ Auto IP Detection** - Automatically detects your local network IP

## Installation

```bash
pip install -r requirements.txt
```

Requirements:
- Python 3.8+
- Flask >= 3.0
- qrcode[pil] >= 7.4

## Usage

### Basic Usage

Serve the current directory:
```bash
python server.py
```

### Share a Specific Directory

```bash
python server.py /path/to/share
```

### Custom Port

```bash
python server.py --port 9000
```

### Password Protection

```bash
python server.py --password your-secret-password
```

### Combined Options

```bash
python server.py -p 8080 -P secret /data
```

## Accessing Your Files

### From the Same Computer
Open your browser and go to: `http://localhost:8888`

### From Other Devices on Your Network
1. Note the IP address shown in the terminal (e.g., `http://192.168.1.100:8888`)
2. Open that URL on any device connected to the same network
3. For mobile: scan the QR code displayed in the terminal

## UI Overview

### Header
- Logo and branding
- "New Folder" button to create directories
- "Upload" button to upload files

### Breadcrumb Navigation
- Shows current path
- Click any part to navigate back
- "Root" returns to the shared directory root

### Upload Zone
- Drag files directly onto the upload area
- Or click to open file picker
- Supports multiple file uploads
- Progress bar shows upload status

### File Grid
- Displays all files and folders with emoji icons
- Click folders to navigate inside
- Click files to preview (images and text)
- Hover to see download/delete actions

### Preview Modal
- Images display inline
- Text files show syntax-highlighted content
- Binary files offer download option

## Supported Previews

### Images
- PNG, JPG, GIF, BMP, WebP, ICO, SVG

### Text Files
- TXT, MD, PY, JS, JSON, HTML, CSS, XML, YAML, TOML
- Source code: C, C++, Java, Go, Rust, Ruby, PHP, etc.
- Config files: INI, CFG, CONF, ENV

### Other Files
- Binary files and unsupported formats offer direct download

## File Type Icons

| Icon | File Types |
|------|------------|
| 🖼️ | Images |
| 🎬 | Videos |
| 🎵 | Audio |
| 📕 | PDF |
| 📄 | Word Documents |
| 📊 | Spreadsheets |
| 💻 | Code Files |
| 🌐 | Web Files |
| 📦 | Archives |
| 📝 | Text Files |
| ⚙️ | Config Files |
| ⚡ | Executables |

## Security

- **Directory Traversal Protection**: Prevents access outside the shared directory
- **Password Hashing**: Passwords are hashed with SHA256
- **File Validation**: Filenames are sanitized on upload

## Architecture

```
server.py          # Single-file Flask application
├── Flask routes   # API endpoints for file operations
├── HTML/CSS/JS    # Embedded frontend (no external dependencies)
└── CLI parser     # Command-line argument handling
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/files` | GET | List directory contents |
| `/api/preview` | GET | Preview file content |
| `/api/download` | GET | Download file or folder as ZIP |
| `/api/upload` | POST | Upload files |
| `/api/mkdir` | POST | Create new folder |
| `/api/delete` | POST | Delete file or folder |

## Troubleshooting

### Can't Access from Mobile
1. Make sure your mobile device is on the same network
2. Check if your firewall allows the port
3. Try using the IP address shown in terminal, not localhost

### QR Code Not Showing
Install qrcode library:
```bash
pip install qrcode[pil]
```

### Upload Fails
- Check file permissions on the shared directory
- Verify sufficient disk space
- Large files may take time (16GB max per file)

## License

MIT License - Feel free to use and modify.
