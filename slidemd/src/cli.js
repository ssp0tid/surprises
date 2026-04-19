import { Command } from 'commander';
import { readFile, writeFile } from 'fs/promises';
import { parseMarkdown } from './parser.js';
import { render, getAllThemes } from './renderer.js';
import { getTheme } from './themes.js';
import { isValidPath } from './utils.js';
import { 
  FileNotFoundError, 
  ThemeNotFoundError, 
  EmptyPresentationError,
  handleError 
} from './errors.js';

const VALID_ASPECT_RATIOS = ['16:9', '16:10', '4:3', '1:1'];
const VALID_TRANSITIONS = ['slide', 'fade', 'none'];

function validateOptions(options) {
  const errors = [];
  const availableThemes = getAllThemes();
  
  if (options.aspectRatio && !VALID_ASPECT_RATIOS.includes(options.aspectRatio)) {
    errors.push(`Invalid aspect ratio: ${options.aspectRatio}. Valid: ${VALID_ASPECT_RATIOS.join(', ')}`);
  }
  
  if (options.transition && !VALID_TRANSITIONS.includes(options.transition)) {
    errors.push(`Invalid transition: ${options.transition}. Valid: ${VALID_TRANSITIONS.join(', ')}`);
  }
  
  if (options.theme && !availableThemes.includes(options.theme)) {
    errors.push(`Invalid theme: ${options.theme}. Valid: ${availableThemes.join(', ')}`);
  }
  
  return errors;
}

export async function generate(inputPath, options = {}) {
  if (!isValidPath(inputPath)) {
    throw new FileNotFoundError(inputPath);
  }

  let content;
  try {
    content = await readFile(inputPath, 'utf-8');
  } catch (e) {
    throw new FileNotFoundError(inputPath);
  }

  const presentation = parseMarkdown(content);

  if (!presentation.slides || presentation.slides.length === 0) {
    throw new EmptyPresentationError();
  }

  if (options.theme) {
    const availableThemes = getAllThemes();
    if (!availableThemes.includes(options.theme)) {
      throw new ThemeNotFoundError(options.theme, availableThemes);
    }
  }

  const html = render(presentation, {
    theme: options.theme,
    title: options.title,
    author: options.author,
    transition: options.transition,
    aspectRatio: options.aspectRatio
  });

  return html;
}

export async function generateFile(inputPath, outputPath, options = {}) {
  const html = await generate(inputPath, options);
  await writeFile(outputPath, html, 'utf-8');
  return outputPath;
}

export function createCLI() {
  const program = new Command();

  program
    .name('slidemd')
    .description('Single-file markdown presentation generator')
    .version('1.0.0');

  program
    .option('-i, --input <file>', 'Input markdown file (required)')
    .option('-o, --output <file>', 'Output HTML file (default: input-name.html)')
    .option('-t, --theme <name>', 'Theme name (default, dark, minimal, gradient, serif)', 'default')
    .option('--title <text>', 'Presentation title')
    .option('--author <name>', 'Author name')
    .option('--transition <type>', 'Slide transition (slide, fade, none)', 'slide')
    .option('--aspect <ratio>', 'Aspect ratio (16:9, 16:10, 4:3, 1:1)', '16:9')
    .option('--list-themes', 'Show available themes')
    .option('-v, --version', 'Show version')
    .option('-h, --help', 'Show help');

  return program;
}

export async function runCLI(args = process.argv) {
  const program = createCLI();
  
  program.parse(args);

  const opts = program.opts();

  if (opts.listThemes) {
    const themes = getAllThemes();
    console.log('Available themes:');
    themes.forEach(t => console.log(`  - ${t}`));
    return;
  }

  const validationErrors = validateOptions({
    aspectRatio: opts.aspect,
    transition: opts.transition,
    theme: opts.theme
  });
  
  if (validationErrors.length > 0) {
    validationErrors.forEach(err => console.error(`Error: ${err}`));
    process.exit(1);
  }

  if (!opts.input && !opts.help && args.length > 2) {
    console.error('Error: --input is required');
    console.log('Usage: slidemd --input <file> [options]');
    console.log('Run: slidemd --help for more information');
    process.exit(1);
  }

  if (!opts.input) {
    return;
  }

  let outputPath = opts.output;
  if (!outputPath) {
    const inputBase = opts.input.replace(/\.md$/, '');
    outputPath = `${inputBase}.html`;
  }

  try {
    await generateFile(opts.input, outputPath, {
      theme: opts.theme,
      title: opts.title,
      author: opts.author,
      transition: opts.transition,
      aspectRatio: opts.aspect
    });
    console.log(`Generated: ${outputPath}`);
  } catch (error) {
    handleError(error);
    process.exit(1);
  }
}

export default { generate, generateFile, createCLI, runCLI };