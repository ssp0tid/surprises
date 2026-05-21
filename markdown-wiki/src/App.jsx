import { useEffect } from 'preact/hooks';
import { Sidebar } from './components/Sidebar';
import { NoteView } from './components/NoteView';
import { NoteEditor } from './components/NoteEditor';
import { SearchBar } from './components/SearchBar';
import { TagList } from './components/TagList';
import {
  fetchNotes,
  currentNote,
  isEditing,
  isLoading,
  error,
  createNewNote,
} from './store';

export function App() {
  const note = currentNote.value;
  const editing = isEditing.value;
  const loading = isLoading.value;
  const err = error.value;

  useEffect(() => {
    fetchNotes();

    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        createNewNote();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <Sidebar />
      <main class="main-content">
        <header class="header">
          <SearchBar />
          <button class="btn btn-primary" onClick={createNewNote}>
            + New
          </button>
        </header>
        <TagList />
        {loading ? (
          <div class="loading">
            <div class="spinner" />
          </div>
        ) : err ? (
          <div class="error-message">{err}</div>
        ) : editing || !note ? (
          <NoteEditor />
        ) : note ? (
          <NoteView />
        ) : (
          <div class="empty-state">
            <div class="empty-state-icon">📝</div>
            <div class="empty-state-text">Select a note or create a new one</div>
            <div class="empty-state-hint">
              <span class="kbd">Ctrl+N</span> to create new note
            </div>
          </div>
        )}
      </main>
    </>
  );
}