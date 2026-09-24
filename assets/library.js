/* Progressive discovery. Static links are complete before this script runs. */
(() => {
  'use strict';
  const form = document.querySelector('.library-search');
  if (!form) return;
  const query = document.getElementById('library-query');
  const kind = document.getElementById('library-kind');
  const count = document.getElementById('library-count');
  const clear = document.getElementById('library-clear');
  const empty = document.getElementById('library-empty');
  const mode = document.getElementById('library-search-mode');
  const items = Array.from(document.querySelectorAll('.library-item'));
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  let records = new Map();
  let request;
  let timer;
  const validKinds = new Set(Array.from(kind.options, option => option.value));

  function filter(updateAddress = true) {
    const words = normalize(query.value.trim()).split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const item of items) {
      const record = records.get(item.dataset.record);
      const searchable = record ? `${record.title} ${record.text}` : item.textContent;
      const matches = (!kind.value || kind.value === item.dataset.kind) && words.every(word => normalize(searchable).includes(word));
      item.hidden = !matches;
      if (matches) visible += 1;
    }
    count.textContent = `${visible} ${visible === 1 ? 'record' : 'records'}${query.value.trim() || kind.value ? ' found' : ''}`;
    clear.hidden = !query.value && !kind.value;
    empty.hidden = visible !== 0;
    if (updateAddress) {
      const url = new URL(window.location.href);
      if (query.value.trim()) url.searchParams.set('q', query.value.trim()); else url.searchParams.delete('q');
      if (kind.value) url.searchParams.set('type', kind.value); else url.searchParams.delete('type');
      window.history.replaceState(null, '', url);
    }
  }

  function loadIndex() {
    if (request) return request;
    request = fetch('/publication/search-index.json', {credentials: 'same-origin'})
      .then(response => {
        if (!response.ok) throw new Error('Search index unavailable');
        return response.json();
      })
      .then(data => {
        if (!Array.isArray(data.records)) throw new Error('Invalid search index');
        records = new Map(data.records.filter(record => typeof record.id === 'string' && typeof record.title === 'string' && typeof record.text === 'string').map(record => [record.id, record]));
        mode.textContent = 'Search uses the exact text of canonical pages and their source records.';
        filter(false);
      })
      .catch(() => {
        mode.textContent = 'Full-text search is unavailable. You can still search titles and use every link below.';
        filter(false);
      });
    return request;
  }

  function fromAddress() {
    const params = new URLSearchParams(window.location.search);
    query.value = params.get('q') || '';
    kind.value = validKinds.has(params.get('type')) ? params.get('type') : '';
    filter(false);
    if (query.value) loadIndex();
  }
  mode.textContent = 'Search titles now, or enter words to search the full canonical text.';
  query.addEventListener('focus', loadIndex, {once:true});
  query.addEventListener('input', () => {
    loadIndex();
    clearTimeout(timer);
    timer = setTimeout(filter, 120);
  });
  kind.addEventListener('change', () => filter());
  form.addEventListener('submit', event => {
    event.preventDefault();
    clearTimeout(timer);
    loadIndex();
    filter();
  });
  clear.addEventListener('click', () => {
    query.value = '';
    kind.value = '';
    filter();
    query.focus();
  });
  window.addEventListener('popstate', fromAddress);
  fromAddress();
})();
