/* Bookmarks Library - Featured + Accordion Drawers */
(function() {
  'use strict';
  
  document.addEventListener('DOMContentLoaded', function() {
    var data = window.BOOKMARKS_CATEGORIES;
    if (!data) return;
    
    var wrapper = document.getElementById('bkRowsWrapper');
    if (!wrapper) return;
    
    var cats = Object.keys(data);
    
    // Category names only (no icons)
    var catConfig = {
      'Utilitarios': 'Utilitarios',
      'Desenvolvimento': 'Desenvolvimento',
      'Software': 'Software',
      'Design': 'Design',
      'Audio IA': 'Audio IA',
      'Texto IA': 'Texto IA',
      'Imagem IA': 'Imagem IA',
      'Jogos': 'Jogos',
      'Video IA': 'Video IA',
      'Cores': 'Cores',
      'Imagens': 'Imagens',
      'Video': 'Video',
      'Icones': 'Icones',
      'Fontes': 'Fontes',
      'Mockups': 'Mockups',
      'Livraria': 'Livraria',
      'Inspiracao': 'Inspiracao',
      'Sites': 'Sites',
      'Cursos': 'Cursos',
      'Audio': 'Audio',
      'Social': 'Social',
      'Ciberseguranca': 'Ciberseguranca',
      'Figma': 'Figma'
    };
    
    // Filter and sort categories
    var validCats = cats.filter(function(cat) {
      return data[cat] && data[cat].length > 0;
    }).sort(function(a, b) {
      return data[b].length - data[a].length;
    });
    var ADMIN_EMAIL = 'diogogg27@gmail.com';
    var FREE_CATEGORY_LIMIT = 4;
    var freeCats = new Set(validCats.slice().sort(function(a, b) {
      return data[a].length - data[b].length;
    }).slice(0, FREE_CATEGORY_LIMIT));

    function hasFullAccess() {
      var user = JSON.parse(localStorage.getItem('hubvision.user') || 'null');
      return Boolean(user && (user.isAdmin || user.email === ADMIN_EMAIL || user.plan === 'premium'));
    }

    function requiresUpgrade(cat) {
      return !freeCats.has(cat) && !hasFullAccess();
    }

    // Keep a large catalog searchable without adding another dependency.
    var toolbar = document.createElement('div');
    toolbar.className = 'bk-toolbar';
    toolbar.innerHTML = '<label class="bk-search-wrap"><span class="bk-search-icon" aria-hidden="true">⌕</span><input class="bk-search" type="search" placeholder="Buscar ferramenta ou domínio" aria-label="Buscar ferramenta ou domínio"></label>' +
      '<label class="bk-filter-wrap"><span class="bk-filter-label">Filtrar</span><select class="bk-filter" aria-label="Filtrar por categoria"><option value="all">Todas as categorias</option></select></label>' +
      '<span class="bk-results" aria-live="polite"></span>';
    var filter = toolbar.querySelector('.bk-filter');
    validCats.forEach(function(cat) {
      var option = document.createElement('option');
      option.value = cat;
      option.textContent = cat;
      filter.appendChild(option);
    });
    wrapper.appendChild(toolbar);
    
    // === ALL DRAWERS ===
    var drawersSection = document.createElement('div');
    drawersSection.className = 'bk-drawers';
    
    validCats.forEach(function(cat) {
      var links = data[cat];
      
      // Create drawer
      var drawer = document.createElement('div');
      drawer.className = 'bk-drawer' + (requiresUpgrade(cat) ? ' bk-premium-drawer' : '');
      drawer.dataset.cat = cat;
      
      // Header
      var header = document.createElement('button');
      header.className = 'bk-drawer-header';
       header.innerHTML = '<span class="bk-drawer-name">' + cat + (requiresUpgrade(cat) ? ' <span class="bk-premium-badge">PRO</span>' : '') + '</span>' +
        '<span class="bk-drawer-count">' + links.length + '</span>' +
        '<span class="bk-drawer-arrow">›</span>';
      
      // Content
      var content = document.createElement('div');
      content.className = 'bk-drawer-content';
      
      var grid = document.createElement('div');
      grid.className = 'bk-links-grid';
      
      links.forEach(function(item) {
        var a = document.createElement('a');
           a.className = 'bk-link-item';
          a.dataset.search = (item.t + ' ' + (item.u || '')).toLowerCase();
        a.href = item.u;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        
        try {
          var url = new URL(item.u);
          var domain = url.hostname.replace('www.', '');
          a.innerHTML = '<img class="bk-link-favicon" src="https://www.google.com/s2/favicons?domain=' + domain + '&sz=32" loading="lazy" onerror="this.style.display=\'none\'">' +
            '<span class="bk-link-info">' +
              '<span class="bk-link-title">' + escapeHtml(item.t) + '</span>' +
              '<span class="bk-link-domain">' + domain + '</span>' +
            '</span>';
        } catch(e) {
          a.innerHTML = '<span class="bk-link-info">' +
            '<span class="bk-link-title">' + escapeHtml(item.t) + '</span>' +
          '</span>';
        }
        
        grid.appendChild(a);
      });
      
      content.appendChild(grid);
      drawer.appendChild(header);
      drawer.appendChild(content);
      drawersSection.appendChild(drawer);
      
      // Toggle
       header.addEventListener('click', function() {
         if (requiresUpgrade(cat)) {
           window.dispatchEvent(new CustomEvent('hubvision:upgrade'));
           return;
         }
         var isOpen = drawer.classList.contains('open');
        document.querySelectorAll('.bk-drawer.open').forEach(function(d) {
          if (d !== drawer) d.classList.remove('open');
        });
        drawer.classList.toggle('open');
      });
    });
    
    wrapper.appendChild(drawersSection);

    function applyFilters() {
      var query = toolbar.querySelector('.bk-search').value.trim().toLowerCase();
      var selected = filter.value;
      var visible = 0;
      document.querySelectorAll('.bk-drawer').forEach(function(drawer) {
        var matchesCategory = selected === 'all' || drawer.dataset.cat === selected;
        var drawerMatches = 0;
        drawer.querySelectorAll('.bk-link-item').forEach(function(link) {
          var matchesQuery = !query || link.dataset.search.includes(query);
          link.classList.toggle('is-hidden', !matchesQuery);
          if (matchesQuery) drawerMatches++;
        });
        var showDrawer = matchesCategory && drawerMatches > 0;
        drawer.classList.toggle('is-hidden', !showDrawer);
        if (showDrawer) visible += drawerMatches;
        if (query && showDrawer) drawer.classList.add('open');
      });
      toolbar.querySelector('.bk-results').textContent = query || selected !== 'all'
        ? visible + ' resultado' + (visible === 1 ? '' : 's')
        : validCats.reduce(function(total, cat) { return total + data[cat].length; }, 0) + ' ferramentas catalogadas';
    }

    toolbar.querySelector('.bk-search').addEventListener('input', applyFilters);
    filter.addEventListener('change', applyFilters);
    applyFilters();
    
    function escapeHtml(str) {
      var div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    }
  });
})();
