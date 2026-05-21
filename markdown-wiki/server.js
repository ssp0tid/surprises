import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import Fastify from 'fastify';
import cors from '@fastify/cors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fastify = Fastify({ logger: true });

await fastify.register(cors, { 
  origin: true 
});

const NOTES_DIR = path.join(__dirname, 'notes');
const PORT = 3456;
const WIKI_LINK_REGEX = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
const TAG_REGEX = /#([\w-]+)/g;

if (!fs.existsSync(NOTES_DIR)) {
  fs.mkdirSync(NOTES_DIR, { recursive: true });
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

function getTitleFromContent(content, fallbackTitle) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : fallbackTitle;
}

function parseWikiLinks(content) {
  const links = [];
  let match;
  const regex = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
  while ((match = regex.exec(content)) !== null) {
    links.push(match[1].trim());
  }
  return [...new Set(links)];
}

function parseTags(content) {
  const tags = [];
  let match;
  while ((match = TAG_REGEX.exec(content)) !== null) {
    tags.push(match[1].trim());
  }
  return [...new Set(tags)];
}

function readAllNotes() {
  const notes = [];
  const files = fs.readdirSync(NOTES_DIR).filter(f => f.endsWith('.md'));
  
  for (const file of files) {
    const slug = path.basename(file, '.md');
    const filePath = path.join(NOTES_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const stats = fs.statSync(filePath);
    
    const title = getTitleFromContent(content, slug);
    const tags = parseTags(content);
    const links = parseWikiLinks(content);
    
    notes.push({
      slug,
      title,
      content,
      tags,
      links,
      createdAt: stats.birthtime.toISOString(),
      updatedAt: stats.mtime.toISOString(),
    });
  }
  
  return notes;
}

function readNote(slug) {
  const filePath = path.join(NOTES_DIR, `${slug}.md`);
  if (!fs.existsSync(filePath)) {
    return null;
  }
  
  const content = fs.readFileSync(filePath, 'utf-8');
  const stats = fs.statSync(filePath);
  
  const title = getTitleFromContent(content, slug);
  const tags = parseTags(content);
  const links = parseWikiLinks(content);
  
  return {
    slug,
    title,
    content,
    tags,
    links,
    createdAt: stats.birthtime.toISOString(),
    updatedAt: stats.mtime.toISOString(),
  };
}

function buildBacklinksIndex(notes) {
  const backlinksMap = new Map();
  
  for (const note of notes) {
    backlinksMap.set(note.slug, []);
  }
  
  for (const note of notes) {
    for (const link of note.links) {
      const linkSlug = slugify(link);
      if (backlinksMap.has(linkSlug)) {
        const existing = backlinksMap.get(linkSlug);
        existing.push({
          slug: note.slug,
          title: note.title,
        });
        backlinksMap.set(linkSlug, existing);
      }
    }
  }
  
  return backlinksMap;
}

fastify.get('/api/notes', async (request, reply) => {
  try {
    const notes = readAllNotes();
    const backlinksMap = buildBacklinksIndex(notes);
    
    const summaries = notes.map(note => ({
      slug: note.slug,
      title: note.title,
      tags: note.tags,
      links: note.links,
      backlinks: backlinksMap.get(note.slug) || [],
      createdAt: note.createdAt,
      updatedAt: note.updatedAt,
    }));
    
    return summaries;
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to read notes', message: error.message };
  }
});

fastify.get('/api/notes/:slug', async (request, reply) => {
  try {
    const { slug } = request.params;
    const note = readNote(slug);
    
    if (!note) {
      reply.code(404);
      return { error: 'Note not found', slug };
    }
    
    const allNotes = readAllNotes();
    const backlinksMap = buildBacklinksIndex(allNotes);
    note.backlinks = backlinksMap.get(note.slug) || [];
    
    return note;
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to read note', message: error.message };
  }
});

fastify.post('/api/notes', async (request, reply) => {
  try {
    const { title, content } = request.body;
    
    if (!title || !content) {
      reply.code(400);
      return { error: 'Title and content are required' };
    }
    
    const slug = slugify(title);
    const filePath = path.join(NOTES_DIR, `${slug}.md`);
    
    if (fs.existsSync(filePath)) {
      reply.code(400);
      return { error: 'Note already exists', slug };
    }
    
    let noteContent = content;
    if (!noteContent.startsWith('# ')) {
      noteContent = `# ${title}\n\n${content}`;
    }
    
    fs.writeFileSync(filePath, noteContent, 'utf-8');
    
    const stats = fs.statSync(filePath);
    const tags = parseTags(noteContent);
    const links = parseWikiLinks(noteContent);
    
    reply.code(201);
    return {
      slug,
      title,
      content: noteContent,
      tags,
      links,
      backlinks: [],
      createdAt: stats.birthtime.toISOString(),
      updatedAt: stats.mtime.toISOString(),
    };
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to create note', message: error.message };
  }
});

fastify.put('/api/notes/:slug', async (request, reply) => {
  try {
    const { slug } = request.params;
    const { title, content } = request.body;
    
    const filePath = path.join(NOTES_DIR, `${slug}.md`);
    
    if (!fs.existsSync(filePath)) {
      reply.code(404);
      return { error: 'Note not found', slug };
    }
    
    let noteContent = content;
    
    if (title && title !== slug) {
      if (content) {
        if (content.startsWith('# ')) {
          noteContent = content.replace(/^#\s+.+$/m, `# ${title}`);
        } else {
          noteContent = `# ${title}\n\n${content}`;
        }
      } else {
        const existingContent = fs.readFileSync(filePath, 'utf-8');
        if (existingContent.startsWith('# ')) {
          noteContent = existingContent.replace(/^#\s+.+$/m, `# ${title}`);
        } else {
          noteContent = `# ${title}\n\n${existingContent}`;
        }
      }
    } else if (content) {
      const existingContent = fs.readFileSync(filePath, 'utf-8');
      if (!content.startsWith('# ') && existingContent.startsWith('# ')) {
        const existingTitle = existingContent.match(/^#\s+(.+)$/m);
        if (existingTitle) {
          noteContent = `# ${existingTitle[1]}\n\n${content}`;
        }
      }
    } else {
      reply.code(400);
      return { error: 'No content or title provided' };
    }
    
    fs.writeFileSync(filePath, noteContent, 'utf-8');
    
    const updatedNote = readNote(slug);
    const allNotes = readAllNotes();
    const backlinksMap = buildBacklinksIndex(allNotes);
    updatedNote.backlinks = backlinksMap.get(slug) || [];
    
    return updatedNote;
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to update note', message: error.message };
  }
});

fastify.delete('/api/notes/:slug', async (request, reply) => {
  try {
    const { slug } = request.params;
    const filePath = path.join(NOTES_DIR, `${slug}.md`);
    
    if (!fs.existsSync(filePath)) {
      reply.code(404);
      return { error: 'Note not found', slug };
    }
    
    fs.unlinkSync(filePath);
    
    return { success: true, slug };
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to delete note', message: error.message };
  }
});

fastify.get('/api/tags', async (request, reply) => {
  try {
    const notes = readAllNotes();
    const tagCounts = new Map();
    
    for (const note of notes) {
      for (const tag of note.tags) {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      }
    }
    
    const tags = Array.from(tagCounts.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
    
    return tags;
  } catch (error) {
    reply.code(500);
    return { error: 'Failed to read tags', message: error.message };
  }
});

fastify.get('/api/search', async (request, reply) => {
  try {
    const { q } = request.query;
    
    if (!q || q.trim().length === 0) {
      return [];
    }
    
    const query = q.toLowerCase().trim();
    const notes = readAllNotes();
    const results = [];
    
    for (const note of notes) {
      const titleMatch = note.title.toLowerCase().includes(query);
      const contentMatch = note.content.toLowerCase().includes(query);
      
      if (titleMatch || contentMatch) {
        let score = 0;
        if (titleMatch) score += 10;
        
        const regex = new RegExp(query, 'gi');
        const matches = note.content.match(regex);
        if (matches) {
          score += matches.length;
        }
        
        results.push({
          slug: note.slug,
          title: note.title,
          score,
        });
      }
    }
    
    results.sort((a, b) => b.score - a.score);
    
    return results;
  } catch (error) {
    reply.code(500);
    return { error: 'Search failed', message: error.message };
  }
});

fastify.get('/health', async () => {
  return { status: 'ok', timestamp: new Date().toISOString() };
});

try {
  await fastify.listen({ port: PORT, host: '0.0.0.0' });
  console.log(`Server running at http://localhost:${PORT}`);
} catch (err) {
  fastify.log.error(err);
  process.exit(1);
}