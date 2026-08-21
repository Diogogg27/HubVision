// HubVision - Horizontal Parallax Gallery (Inspirado no Codrops Horizontal Parallax Gallery por David Faure)
// Implementação adaptada com smooth lerp scrolling, drag/swipe, wheel horizontal scroll e parallax de contra-movimento nos cards.

(function () {
  const appContainer = document.getElementById('promptLibraryApp');
  if (!appContainer || !window.PROMPTS_LIBRARY) return;

  const data = window.PROMPTS_LIBRARY;
  // Keep the free allowance in one place as the library grows.
  const FREE_PROMPT_LIMIT = 70;
  const ADMIN_EMAIL = 'diogogg27@gmail.com';

  function hasFullAccess() {
    const user = JSON.parse(localStorage.getItem('hubvision.user') || 'null');
    return Boolean(user && (user.isAdmin || user.email === ADMIN_EMAIL));
  }

  // Atualiza contador de prompts
  const countEl = document.getElementById('promptCount');
  if (countEl) {
    countEl.textContent = String(data.length).padStart(2, '0');
  }

  const CAT_LABELS = {
    retrato: 'Retrato',
    fotografia: 'Fotografia',
    publicidade: 'Publicidade',
    fantasia: 'Fantasia',
    'ficcao cientifica': 'Ficção Científica',
    arquitetura: 'Arquitetura',
    '3d': '3D',
    paisagem: 'Paisagem',
    'arte conceitual': 'Arte Conceitual',
    outros: 'Outros'
  };

  const MODEL_BADGES = {
    midjourney: 'MJ',
    'gpt image': 'GPT',
    'nano banana': 'NB',
    gemini: 'GM',
    leonardo: 'LEO',
    flux: 'FLX',
    ideogram: 'ID',
    'dall-e': 'DE',
    dalle: 'DE'
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function badgeFor(modelo) {
    const m = (modelo || '').toLowerCase();
    const key = Object.keys(MODEL_BADGES).find(k => m.includes(k));
    return key ? MODEL_BADGES[key] : 'AI';
  }

  function clamp(min, max, v) {
    return Math.max(min, Math.min(max, v));
  }

  function lerp(start, end, factor) {
    return start + (end - start) * factor;
  }

  class HorizontalParallaxGallery {
    constructor() {
      this.wrapper = appContainer.querySelector('.pl-parallax-wrapper');
      this.container = appContainer.querySelector('.pl-parallax-container');
      this.prevBtn = document.getElementById('plNavPrev');
      this.nextBtn = document.getElementById('plNavNext');
      this.progressFill = document.getElementById('plProgressFill');
      this.zoom = document.getElementById('plZoom');

      this.scroll = {
        current: 0,
        target: 0,
        ease: 0.08,
        limit: 0
      };

      this.isDragging = false;
      this.dragStartX = 0;
      this.dragStartTarget = 0;
      this.hasMoved = false;

      this.init();
    }

    init() {
      this.renderCards();
      this.images = Array.from(this.container.querySelectorAll('.pl-parallax-img'));
      this.items = Array.from(this.container.querySelectorAll('.pl-parallax-item'));

      this.setLimit();
      this.addEventListeners();
      this.render();
    }

    renderCards() {
      this.container.innerHTML = data.map((item, idx) => {
        const badge = badgeFor(item.modelo);
        const premium = idx >= FREE_PROMPT_LIMIT && !hasFullAccess();

        return `
          <div class="pl-parallax-item${premium ? ' pl-locked' : ''}" data-index="${idx}" data-premium="${premium}">
            <img src="${item.img}" alt="Prompt" class="pl-parallax-img" draggable="false" loading="lazy" />
            <div class="pl-parallax-overlay"></div>
            <div class="pl-parallax-header">
              <span class="pl-parallax-badge">${badge}</span>
              ${premium ? '<span class="pl-lock-badge">PRO</span>' : ''}
            </div>
            ${premium ? '<div class="pl-lock-overlay"><span class="pl-lock-icon">+</span><span>Desbloquear prompt</span></div>' : ''}
          </div>
        `;
      }).join('');
    }

    setLimit() {
      if (!this.container || !this.wrapper) return;
      this.scroll.limit = Math.max(0, this.container.scrollWidth - this.wrapper.clientWidth);
    }

    applyParallax() {
      const vw = window.innerWidth;
      const viewportCenter = vw * 0.5;

      this.items.forEach((item) => {
        const img = item.querySelector('.pl-parallax-img');
        if (!img) return;

        const rect = item.getBoundingClientRect();
        
        // Se estiver fora do viewport visível (com margem de 100px), não precisa calcular
        if (rect.right < -100 || rect.left > vw + 100) return;

        const elementCenter = rect.left + rect.width * 0.5;
        // Normalizado de -1 (esquerda) até +1 (direita)
        const t = clamp(-1, 1, (elementCenter - viewportCenter) / (viewportCenter + rect.width * 0.5));
        
        // Efeito Codrops Parallax: desloca a imagem interna de 125% em contra-movimento (-10% a +10%)
        const maxShift = 10;
        const shift = -t * maxShift;
        img.style.transform = `translate3d(${shift.toFixed(2)}%, 0, 0)`;
      });
    }

    addEventListeners() {
      window.addEventListener('resize', () => {
        this.setLimit();
      });

      // Wheel Event na seção do container para scroll horizontal suave
      this.wrapper.addEventListener('wheel', (e) => {
        // Se o modal de zoom estiver aberto, não altera o scroll da galeria
        if (this.scroll.limit <= 0 || (this.zoom && this.zoom.classList.contains('active'))) return;

        e.preventDefault();
        e.stopPropagation();

        const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
        this.scroll.target += delta * 1.5;
        this.scroll.target = clamp(0, this.scroll.limit, this.scroll.target);
      }, { passive: false });

      // Drag / Touch Navigation
      const onPointerDown = (e) => {
        this.isDragging = true;
        this.hasMoved = false;
        this.dragStartX = e.pageX || (e.touches && e.touches[0].pageX) || 0;
        this.dragStartTarget = this.scroll.target;
      };

      const onPointerMove = (e) => {
        if (!this.isDragging) return;
        const x = e.pageX || (e.touches && e.touches[0].pageX) || 0;
        const diff = this.dragStartX - x;
        if (Math.abs(diff) > 5) {
          this.hasMoved = true;
        }
        this.scroll.target = clamp(0, this.scroll.limit, this.dragStartTarget + diff * 1.5);
      };

      const onPointerUp = () => {
        this.isDragging = false;
      };

      this.wrapper.addEventListener('mousedown', onPointerDown);
      window.addEventListener('mousemove', onPointerMove);
      window.addEventListener('mouseup', onPointerUp);

      this.wrapper.addEventListener('touchstart', onPointerDown, { passive: true });
      window.addEventListener('touchmove', onPointerMove, { passive: true });
      window.addEventListener('touchend', onPointerUp);

      // Botões Prev / Next
      if (this.prevBtn) {
        this.prevBtn.addEventListener('click', () => {
          const step = Math.min(600, window.innerWidth * 0.7);
          this.scroll.target = clamp(0, this.scroll.limit, this.scroll.target - step);
        });
      }
      if (this.nextBtn) {
        this.nextBtn.addEventListener('click', () => {
          const step = Math.min(600, window.innerWidth * 0.7);
          this.scroll.target = clamp(0, this.scroll.limit, this.scroll.target + step);
        });
      }

      // Clique no Card para abrir Zoom com o Prompt
      this.container.addEventListener('click', (e) => {
        if (this.hasMoved) return; // Se estava arrastando, não abre o modal
         const card = e.target.closest('.pl-parallax-item');
         if (!card) return;
         if (card.dataset.premium === 'true') {
           const user = JSON.parse(localStorage.getItem('hubvision.user') || 'null');
            if (!user || (!user.isAdmin && user.email !== ADMIN_EMAIL && user.plan !== 'premium')) {
             window.dispatchEvent(new CustomEvent('hubvision:upgrade'));
             return;
           }
         }
         this.openZoom(Number(card.dataset.index));
      });

      // Controles do Modal de Zoom
      if (this.zoom) {
        this.zoom.addEventListener('click', (e) => {
          if (e.target.closest('[data-zoom-close]')) {
            this.closeZoom();
            return;
          }
          const copyBtn = e.target.closest('.pl-zoom-copy');
          if (copyBtn) {
            const txt = this.zoom.querySelector('.pl-zoom-prompt').textContent;
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(txt);
            }
            const original = copyBtn.textContent;
            copyBtn.textContent = 'Copiado';
            copyBtn.classList.add('is-copied');
            setTimeout(() => {
              copyBtn.textContent = original;
              copyBtn.classList.remove('is-copied');
            }, 1500);
          }
        });
      }

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.zoom && this.zoom.classList.contains('active')) {
          this.closeZoom();
        }
      });
    }

    openZoom(index) {
      const item = data[index];
      if (!item || !this.zoom) return;

       this.zoom.querySelector('.pl-zoom-img').src = item.img;
       this.zoom.querySelector('.pl-zoom-img').alt = item.prompt.slice(0, 80);
       this.zoom.querySelector('.pl-zoom-model').textContent = item.modelo || 'AI PROMPT';
       this.zoom.querySelector('.pl-zoom-group').textContent = item.grupo ? `/${item.grupo}` : '';
       this.zoom.querySelector('.pl-zoom-prompt').textContent = item.prompt;

      this.zoom.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    closeZoom() {
      if (!this.zoom) return;
      this.zoom.classList.remove('active');
      document.body.style.overflow = '';
    }

    render() {
      this.scroll.target = clamp(0, this.scroll.limit, this.scroll.target);
      this.scroll.current = lerp(this.scroll.current, this.scroll.target, this.scroll.ease);

      // Translada o container horizontalmente
      const offset = this.scroll.current < 0.01 ? 0 : -this.scroll.current;
      this.container.style.transform = `translate3d(${offset}px, 0, 0)`;

      // Aplica o efeito parallax individual nas imagens
      this.applyParallax();

      // Atualiza a barra de progresso
      if (this.progressFill && this.scroll.limit > 0) {
        const pct = (this.scroll.current / this.scroll.limit) * 100;
        this.progressFill.style.width = `${clamp(0, 100, pct)}%`;
      }

      requestAnimationFrame(this.render.bind(this));
    }
  }

  new HorizontalParallaxGallery();
})();
