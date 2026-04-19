const fs = require('fs');
const path = require('path');

function scanFiles(targetPath, extensions = ['.md', '.markdown'], recursive = true) {
  const files = [];
  const exts = new Set(extensions);
  const skipDirs = new Set(['node_modules', '.git', 'dist', 'build']);

  function walk(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (err) {
      if (err.code === 'EACCES' || err.code === 'EPERM') {
        return;
      }
      throw err;
    }
    for (const entry of entries) {
      if (skipDirs.has(entry.name)) continue;
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory() && recursive) {
        walk(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (exts.has(ext)) {
          files.push(fullPath);
        }
      }
    }
  }

  let stats;
  try {
    stats = fs.statSync(targetPath);
  } catch (err) {
    if (err.code === 'ENOENT') {
      return files;
    }
    throw err;
  }

  if (stats.isDirectory()) {
    walk(targetPath);
  } else if (stats.isFile()) {
    files.push(targetPath);
  }

  return files;
}

module.exports = { scanFiles };