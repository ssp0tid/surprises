const fs = require('fs');
const path = require('path');

function parseLinks(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const links = [];

  const standardLinkRegex = /\[([^\]]*)\]\(([^)]+)\)/g;
  const refLinkRegex = /\[([^\]]*)\]\[([^\]]*)\]/g;
  const definedRefRegex = /^\s*\[([^\]]+)\]:\s*(\S+)/;

  const refMap = {};
  lines.forEach((line, idx) => {
    const match = line.match(definedRefRegex);
    if (match) {
      refMap[match[1]] = match[2];
    }
  });

  lines.forEach((line, lineNum) => {
    let match;
    standardLinkRegex.lastIndex = 0;
    while ((match = standardLinkRegex.exec(line))) {
      let url = match[2].trim();
      if (url && !url.startsWith('#')) {
        while (url.startsWith('(') && url.endsWith(')')) {
          url = url.slice(1, -1);
        }
        if (url) {
          links.push({
            url,
            line: lineNum + 1,
            text: match[1],
            type: url.startsWith('http') || url.startsWith('https') ? 'external' : 'internal'
          });
        }
      }
    }
  });

  lines.forEach((line, lineNum) => {
    let match;
    refLinkRegex.lastIndex = 0;
    while ((match = refLinkRegex.exec(line))) {
      const ref = match[2];
      if (refMap[ref]) {
        const url = refMap[ref].trim();
        links.push({
          url,
          line: lineNum + 1,
          text: match[1],
          type: url.startsWith('http') || url.startsWith('https') ? 'external' : 'internal'
        });
      }
    }
  });

  return links;
}

module.exports = { parseLinks };