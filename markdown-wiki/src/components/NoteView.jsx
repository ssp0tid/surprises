import { computed } from '@preact/signals';
import { marked } from 'marked';
import { currentNote, selectNote, startEditing, deleteNote, saveNote } from '../store';

function renderMarkdown(content) {
  if (!content) return '';
  
  let html = marked.parse(content, { breaks: true, gfm: true });
  
  html = html.replace(
    /\[\[([^\]]+)\]\]/g,
    (_, text) => `<a class="wiki-link" data-wiki-link="${text}">${text}</a>`
  );
  
  return html;
}

const noteContent = computed(() => {
  const note = currentNote.value;
  return note ? renderMarkdown(note.content) : '';
});

export function NoteView() {
  const note = currentNote.value;
  
  if (!note) return null;
  
  const handleClick = (e) => {
    const link = e.target.closest('[data-wiki-link]');
    if (link) {
      e.preventDefault();
      const title = link.dataset.wikiLink;
      selectNote(title);
    }
  };
  
  const handleDelete = async () => {
    if (confirm('Delete this note?')) {
      await deleteNote(note.slug);
    }
  };

  return (
    <div class="note-view">
      <div class="note-view-header">
        <h1 class="note-title">{note.title || 'Untitled'}</h1>
        <div class="note-actions">
          <button class="btn btn-secondary" onClick={startEditing}>Edit</button>
          <button class="btn btn-danger" onClick={handleDelete}>Delete</button>
        </div>
      </div>
      <div 
        class="note-content"
        dangerouslySetInnerHTML={{ __html: noteContent.value }}
        onClick={handleClick}
      />
      {note.tags?.length > 0 && (
        <div class="tags">
          {note.tags.map(tag => (
            <span key={tag} class="tag">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}