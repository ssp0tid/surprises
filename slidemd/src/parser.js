import { marked } from 'marked';
import yaml from 'js-yaml';
import { normalizeLineEndings, isEmpty } from './utils.js';
import { InvalidFrontmatterError } from './errors.js';

marked.setOptions({
  gfm: true,
  breaks: false
});

export function splitSlides(content) {
  content = normalizeLineEndings(content);
  const lines = content.split('\n');
  const slides = [];
  let currentSlide = [];
  let inCodeBlock = false;
  let codeBlockChar = '';
  let inHtmlComment = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```') || line.startsWith('~~~')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockChar = line.substring(0, 3);
      } else if (line.startsWith(codeBlockChar)) {
        inCodeBlock = false;
        codeBlockChar = '';
      }
      currentSlide.push(line);
      continue;
    }

    if (inCodeBlock) {
      currentSlide.push(line);
      continue;
    }

    if (line.includes('<!--')) {
      const commentStart = line.indexOf('<!--');
      const commentEnd = line.indexOf('-->');
      if (commentStart !== -1 && commentEnd === -1) {
        inHtmlComment = true;
      }
    }

    if (line.includes('-->') && inHtmlComment) {
      inHtmlComment = false;
      currentSlide.push(line);
      continue;
    }

    if (inHtmlComment) {
      currentSlide.push(line);
      continue;
    }

    if (/^---+$/.test(line.trim()) && currentSlide.length > 0) {
      const slideContent = currentSlide.join('\n').trim();
      if (!isEmpty(slideContent)) {
        slides.push(slideContent);
      }
      currentSlide = [];
    } else {
      currentSlide.push(line);
    }
  }

  if (currentSlide.length > 0) {
    const slideContent = currentSlide.join('\n').trim();
    if (!isEmpty(slideContent)) {
      slides.push(slideContent);
    }
  }

  return slides;
}

export function extractFrontmatter(content) {
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
  const match = content.match(frontmatterRegex);

  if (!match) {
    return { metadata: {}, body: content };
  }

  const yamlContent = match[1];
  const body = content.substring(match[0].length);

  let metadata = {};
  try {
    metadata = yaml.load(yamlContent) || {};
  } catch (e) {
    throw new InvalidFrontmatterError(e.message);
  }

  return { metadata, body };
}

export function extractNotes(slideContent) {
  const notesRegex = /<!--\s*notes\s*-->[\s\S]*?<!--\s*-->/gi;
  let notes = '';
  let content = slideContent;

  const matches = slideContent.match(notesRegex);
  if (matches) {
    notes = matches
      .map(m => m.replace(/<!--\s*notes\s*-->/gi, '').replace(/<!--\s*-->/gi, '').trim())
      .join('\n');

    content = slideContent.replace(notesRegex, '').trim();
  }

  return { content, notes };
}

export function parseMarkdown(content) {
  const { metadata, body } = extractFrontmatter(content);
  const slideTexts = splitSlides(body);

  const slides = slideTexts.map((slideText, index) => {
    const { content: slideContent, notes } = extractNotes(slideText);
    let html;
    try {
      html = marked.parse(slideContent);
    } catch (e) {
      html = `<pre>${slideContent}</pre>`;
    }

    return {
      index,
      content: slideContent,
      notes,
      html
    };
  });

  return {
    metadata,
    slides
  };
}