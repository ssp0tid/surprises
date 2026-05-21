import { signal, computed } from '@preact/signals';

const API_URL = 'http://localhost:3456';

// State signals
export const notes = signal([]);
export const currentNoteId = signal(null);
export const searchQuery = signal('');
export const isEditing = signal(false);
export const isLoading = signal(false);
export const error = signal(null);

// Computed values
export const currentNote = computed(() => {
  return notes.value.find(n => n.slug === currentNoteId.value) || null;
});

export const filteredNotes = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  if (!query) return notes.value;
  return notes.value.filter(n => 
    n.title?.toLowerCase().includes(query) ||
    n.content?.toLowerCase().includes(query) ||
    n.tags?.some(t => t.toLowerCase().includes(query))
  );
});

export const allTags = computed(() => {
  const tags = new Set();
  notes.value.forEach(n => n.tags?.forEach(t => tags.add(t)));
  return Array.from(tags).sort();
});

// Actions
export async function fetchNotes() {
  isLoading.value = true;
  error.value = null;
  try {
    const res = await fetch(`${API_URL}/api/notes`);
    if (!res.ok) throw new Error('Failed to fetch notes');
    const data = await res.json();
    notes.value = data;
  } catch (e) {
    error.value = e.message;
    console.error('fetchNotes error:', e);
  } finally {
    isLoading.value = false;
  }
}

export async function saveNote(note) {
  error.value = null;
  try {
    const method = note.slug ? 'PUT' : 'POST';
    const url = note.slug ? `${API_URL}/api/notes/${note.slug}` : `${API_URL}/api/notes`;
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(note),
    });
    if (!res.ok) throw new Error('Failed to save note');
    const saved = await res.json();
    
    if (note.slug) {
      notes.value = notes.value.map(n => n.slug === saved.slug ? saved : n);
    } else {
      notes.value = [...notes.value, saved];
      currentNoteId.value = saved.slug;
    }
    return saved;
  } catch (e) {
    error.value = e.message;
    console.error('saveNote error:', e);
    throw e;
  }
}

export async function deleteNote(id) {
  error.value = null;
  try {
    const res = await fetch(`${API_URL}/api/notes/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete note');
    notes.value = notes.value.filter(n => n.slug !== id);
    if (currentNoteId.value === id) {
      currentNoteId.value = null;
    }
  } catch (e) {
    error.value = e.message;
    console.error('deleteNote error:', e);
    throw e;
  }
}

export function selectNote(id) {
  currentNoteId.value = id;
  isEditing.value = false;
}

export function createNewNote() {
  currentNoteId.value = null;
  isEditing.value = true;
}

export function startEditing() {
  isEditing.value = true;
}

export function cancelEditing() {
  isEditing.value = false;
  if (!currentNoteId.value) {
    currentNoteId.value = null;
  }
}