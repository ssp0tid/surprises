#!/usr/bin/env node

const { Command } = require('commander');
const path = require('path');
const { scanFiles } = require('./scanner');
const { parseLinks } = require('./parser');
const { validateLinks } = require('./validator');
const { Reporter } = require('./reporter');

const program = new Command();

program
  .name('mdlink')
  .description('Check for broken links in markdown files')
  .version('1.0.0')
  .option('-r, --recursive', 'Scan directories recursively', true)
  .option('-e, --extensions <ext>', 'File extensions to scan', '.md,.markdown')
  .option('-t, --timeout <ms>', 'Request timeout in ms', '5000')
  .option('-c, --concurrency <n>', 'Max concurrent requests', '10')
  .option('-j, --json', 'Output JSON format')
  .option('-q, --quiet', 'Suppress summary output')
  .option('-v, --verbose', 'Show all link checks')
  .option('--no-color', 'Disable color output')
  .argument('[path]', 'File or directory to scan', '.')

async function main() {
  const opts = program.opts();
  const targetPath = program.args[0] || '.';

  const extensions = opts.extensions.split(',');
  const timeout = parseInt(opts.timeout, 10);
  const concurrency = parseInt(opts.concurrency, 10);

  const absolutePath = path.isAbsolute(targetPath) ? targetPath : path.join(process.cwd(), targetPath);
  const baseDir = path.dirname(absolutePath);

  const files = scanFiles(absolutePath, extensions, opts.recursive);

  if (files.length === 0) {
    console.log('No markdown files found');
    process.exit(0);
  }

  const results = [];

  for (const file of files) {
    const links = parseLinks(file);

    if (links.length > 0) {
      const validated = await validateLinks(links, path.dirname(file), concurrency, timeout);
      const sorted = validated.sort((a, b) => a.line - b.line);
      results.push({ file, links: sorted });
    } else {
      results.push({ file, links: [] });
    }
  }

  const reporter = new Reporter({
    color: opts.color,
    verbose: opts.verbose
  });

  if (opts.json) {
    console.log(reporter.toJSON(results));
  } else {
    for (const result of results) {
      if (result.links.length > 0) {
        console.log(reporter.reportFile(result.file, result.links));
      }
    }
    if (!opts.quiet) {
      console.log(reporter.reportSummary(results));
    }
  }

  const brokenCount = results.reduce(
    (sum, r) => sum + r.links.filter(l => l.status === 'broken').length,
    0
  );

  process.exit(brokenCount > 0 ? 1 : 0);
}

program.parse();
main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});