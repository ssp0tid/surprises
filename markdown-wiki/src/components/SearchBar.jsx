import { searchQuery } from '../store';

export function SearchBar() {
  const handleInput = (e) => {
    searchQuery.value = e.target.value;
  };

  return (
    <div class="search-bar">
      <input
        type="text"
        class="search-input"
        value={searchQuery.value}
        onInput={handleInput}
        placeholder="Search notes..."
      />
    </div>
  );
}