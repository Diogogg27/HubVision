// HubVision - Biblioteca Dinâmica de Links de IA
// Carrega os dados de window.AI_LINKS_CATEGORIES (js/ai_links_dataset.js)

(function () {
  const container = document.getElementById('aiLinksApp');
  if (!container || !window.AI_LINKS_CATEGORIES) return;

  const data = window.AI_LINKS_CATEGORIES;

  const state = {
    search: '',
    category: 'all'
  };

  function allTools() {
    const list = [];
    data.forEach(c => {
      c.tools.forEach(t => list.push({ ...t, category: c.category }));
    });
    return list;
  }

  function filtered() {
    const tools = state.category === 'all' ? allTools() : data.find(c => c.category === state.category)?.tools || [];
    const q = state.search.toLowerCase();
    if (!q) return tools;
    return tools.filter(t => t.name.toLowerCase().includes(q));
  }

  function renderCategories() {
    const bar = container.querySelector('.ail-cats');
    if (!bar) return;
    let html = `<button class="ail-cat ail-cat-all ${state.category === 'all' ? 'active' : ''}" data-cat="all">Todos (${allTools().length})</button>`;
    data.forEach(c => {
      html += `<button class="ail-cat ${state.category === c.category ? 'active' : ''}" data-cat="${c.category}">${c.category} (${c.tools.length})</button>`;
    });
    bar.innerHTML = html;
  }

  function renderGrid() {
    const grid = container.querySelector('.ail-grid');
    const count = container.querySelector('.ail-count');
    if (!grid) return;

    const items = filtered();
    count.textContent = `${items.length} ferramentas${state.search ? ` para "${state.search}"` : ''}`;

    grid.innerHTML = items.map(t => {
      const host = (t.url || '').replace(/^https?:\/\//, '').replace(/\/.*$/, '');
      return `
      <a href="${t.url}" target="_blank" rel="noopener" class="ail-item">
        <span class="ail-item-main">
          <span class="ail-item-name">${t.name}</span>
          <span class="ail-item-url">${host}</span>
        </span>
        <span class="ail-item-arrow">→</span>
      </a>
    `;
    }).join('');
  }

  function bind() {
    const searchInput = container.querySelector('.ail-search');
    const grid = container.querySelector('.ail-grid');
    const resetScroll = () => { if (grid) grid.scrollTo({ left: 0, behavior: 'auto' }); };

    searchInput.addEventListener('input', e => {
      state.search = e.target.value.trim();
      resetScroll();
      renderGrid();
    });

    container.querySelector('.ail-cats').addEventListener('click', e => {
      const btn = e.target.closest('.ail-cat');
      if (!btn) return;
      state.category = btn.dataset.cat;
      resetScroll();
      renderCategories();
      renderGrid();
    });

    const prev = container.querySelector('.ail-scroll-prev');
    const next = container.querySelector('.ail-scroll-next');
    const step = () => grid.clientWidth * 0.85;
    if (prev) prev.addEventListener('click', () => grid.scrollBy({ left: -step(), behavior: 'smooth' }));
    if (next) next.addEventListener('click', () => grid.scrollBy({ left: step(), behavior: 'smooth' }));
  }

  renderCategories();
  renderGrid();
  bind();
})();