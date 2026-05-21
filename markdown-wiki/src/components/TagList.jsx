import { allTags, searchQuery } from '../store';

export function TagList() {
  const tags = allTags.value;
  const query = searchQuery.value;

  if (tags.length === 0) return null;

  const toggleTag = (tag) => {
    if (query.includes(tag)) {
      searchQuery.value = query.replace(tag, '').trim();
    } else {
      searchQuery.value = query ? `${query} ${tag}` : tag;
    }
  };

  const isActive = (tag) => query.includes(tag);

  return (
    <div class="tag-list">
      <span class="tag-list-label">Tags</span>
      {tags.map(tag => (
        <span 
          key={tag} 
          class={`tag ${isActive(tag) ? 'active' : ''}`}
          onClick={() => toggleTag(tag)}
        >
          {tag}
        </span>
      ))}
    </div>
  );
}