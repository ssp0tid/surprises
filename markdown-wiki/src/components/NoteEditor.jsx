import { useState, useEffect, useRef } from 'preact/hooks';
import { currentNote, saveNote, cancelEditing } from '../store';

export function NoteEditor() {
  const note = currentNote.value;
  const [title, setTitle] = useState(note?.title || '');
  const [content, setContent] = useState(note?.content || '');
  const [tags, setTags] = useState(note?.tags?.join(', ') || '');
  const [saving, setSaving] = useState(false);
  const titleRef = useRef(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    try {
      const tagArray = tags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);
      
      await saveNote({
        id: note?.slug,
        title: title || 'Untitled',
        content,
        tags: tagArray,
      });
      cancelEditing();
    } catch (e) {
      console.error('Save failed:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  return (
    <div class="note-editor" onKeyDown={handleKeyDown}>
      <div class="editor-field">
        <label class="editor-label">Title</label>
        <input
          ref={titleRef}
          type="text"
          class="editor-input"
          value={title}
          onInput={(e) => setTitle(e.target.value)}
          placeholder="Note title..."
        />
      </div>
      
      <div class="editor-field" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <label class="editor-label">Content (Markdown)</label>
        <textarea
          class="editor-textarea"
          value={content}
          onInput={(e) => setContent(e.target.value)}
          placeholder="Write your note in markdown... Use [[wiki-links]] to link to other notes."
        />
      </div>
      
      <div class="editor-field">
        <label class="editor-label">Tags (comma separated)</label>
        <input
          type="text"
          class="editor-input"
          value={tags}
          onInput={(e) => setTags(e.target.value)}
          placeholder="tag1, tag2, tag3..."
        />
      </div>
      
      <div class="editor-actions">
        <button class="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </button>
        <button class="btn btn-secondary" onClick={cancelEditing}>
          Cancel
        </button>
      </div>
    </div>
  );
}