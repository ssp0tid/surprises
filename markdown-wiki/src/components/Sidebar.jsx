import { filteredNotes, currentNoteId, selectNote } from '../store';

export function Sidebar() {
  const notes = filteredNotes.value;
  const activeId = currentNoteId.value;

  return (
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="sidebar-title">Markdown Wiki</h1>
      </div>
      <div class="notes-list">
        {notes.length === 0 ? (
          <div class="empty-state">
            <div class="empty-state-text">No notes yet</div>
          </div>
        ) : (
          notes.map(note => (
            <div
              key={note.slug}
              class={`note-item ${activeId === note.slug ? 'active' : ''}`}
              onClick={() => selectNote(note.slug)}
            >
              <div class="note-item-title">{note.title || 'Untitled'}</div>
              <div class="note-item-meta">
                {note.updatedAt ? new Date(note.updatedAt).toLocaleDateString() : 'New'}
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}