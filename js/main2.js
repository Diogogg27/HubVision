/* HubVision - Futuristic JavaScript */

function rand(min, max) { return Math.random() * (max - min) + min; }

// === PERFORMANCE: Debounce ===
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  // === PARTICLES ===
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  let particles = [];
  let mouse = { x: 0, y: 0 };
  let animationId;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', debounce(resize, 100));

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 1.5 + 0.5;
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.speedY = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.3 + 0.1;
      this.hue = Math.random() > 0.5 ? 190 : 180;
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
      if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${this.opacity})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < 100; i++) particles.push(new Particle());

  function connectParticles() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0, 135, 189, ${0.08 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
      const md = Math.sqrt((particles[i].x - mouse.x) ** 2 + (particles[i].y - mouse.y) ** 2);
      if (md < 170) {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(0,255,136,${0.35 * (1 - md / 170)})`;
        ctx.lineWidth = 0.8;
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(mouse.x, mouse.y);
        ctx.stroke();
      }
    }
  }

  function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    connectParticles();
    requestAnimationFrame(animateParticles);
  }
  animateParticles();

  // === CUSTOM CURSOR ===
  const cursor = document.getElementById('cursor');
  const cursorDot = document.getElementById('cursorDot');

  document.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
    cursorDot.style.left = e.clientX + 'px';
    cursorDot.style.top = e.clientY + 'px';
  });

  document.querySelectorAll('a, .btn, .service-card').forEach(el => {
    el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
    el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
  });

  // === SCROLL REVEAL ===
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('active');
        }, index * 100);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // === SMOOTH SCROLL ===
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        // Active state
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        this.classList.add('active');
        
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // === ACTIVE NAV ON SCROLL ===
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', debounce(() => {
    let current = '';
    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      if (window.pageYOffset >= sectionTop - 200) {
        current = section.getAttribute('id');
      }
    });
    
    document.querySelectorAll('.nav-links a').forEach(a => {
      a.classList.remove('active');
      if (a.getAttribute('href') === `#${current}`) {
        a.classList.add('active');
      }
    });
  }, 100));

  // === HERO PARALLAX ===
  document.addEventListener('mousemove', (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;
    const glow1 = document.querySelector('.hero-glow-1');
    const glow2 = document.querySelector('.hero-glow-2');
    if (glow1) glow1.style.transform = `translate(${x}px, ${y}px)`;
    if (glow2) glow2.style.transform = `translate(${-x}px, ${-y}px)`;
  });

  // === NAV SCROLL EFFECT ===
  const nav = document.querySelector('.nav');
  const mobileMenu = document.querySelector('.nav-menu-toggle');
  const mobileNav = document.getElementById('mobileNav');
  if (mobileMenu && mobileNav) {
    mobileMenu.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('is-open');
      mobileMenu.setAttribute('aria-expanded', String(isOpen));
    });
    mobileNav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      mobileMenu.setAttribute('aria-expanded', 'false');
    }));
  }
  let navLastY = window.pageYOffset;
  window.addEventListener('scroll', () => {
    const y = window.pageYOffset;
    if (nav) {
      if (y > 100) {
        nav.style.background = 'rgba(3,7,18,0.95)';
        nav.style.borderBottomColor = 'rgba(0,135,189,0.15)';
        if (y > navLastY + 4) {
          nav.classList.add('is-hidden');
        } else if (y < navLastY - 4) {
          nav.classList.remove('is-hidden');
        }
      } else {
        nav.style.background = 'rgba(3,7,18,0.8)';
        nav.style.borderBottomColor = 'rgba(0,135,189,0.08)';
        nav.classList.remove('is-hidden');
      }
    }
    navLastY = y;
  });

  // === ACCESS GRANTED MODAL ===
  window.openAccessGranted = function () {
    const modal = document.getElementById('accessModal');
    if (!modal) return;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    const bar = modal.querySelector('.access-bar-fill');
    if (bar) {
      bar.style.animation = 'none';
      void bar.offsetWidth;
      bar.style.animation = '';
    }
  };
  window.closeAccessGranted = function () {
    const modal = document.getElementById('accessModal');
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = '';
  };
  // === FULL-PAGE FOG ===
  const fogCanvas = document.getElementById('pageFog');
  if (fogCanvas) {
    const fctx = fogCanvas.getContext('2d');
    const fogPrefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function sizeFogCanvas() {
      fogCanvas.width = window.innerWidth;
      fogCanvas.height = window.innerHeight;
    }
    sizeFogCanvas();
    window.addEventListener('resize', debounce(sizeFogCanvas, 150));

    const fogPuffsFull = [];
    for (let i = 0; i < 12; i++) {
      fogPuffsFull.push({
        x: rand(0, fogCanvas.width),
        y: rand(0, fogCanvas.height),
        vx: rand(-0.4, 0.4),
        vy: rand(-0.25, 0.25),
        r: rand(140, 320),
        phase: rand(0, Math.PI * 2),
        color: ['rgba(0,128,160,', 'rgba(0,96,128,', 'rgba(0,160,192,', 'rgba(0,96,96,', 'rgba(0,64,96,', 'rgba(0,128,192,', 'rgba(0,192,192,', 'rgba(0,80,128,', 'rgba(0,144,176,', 'rgba(0,112,144,', 'rgba(0,176,208,', 'rgba(0,72,112,'][i % 12]
      });
    }

    function drawFog(t) {
      const w = fogCanvas.width, h = fogCanvas.height;
      fctx.clearRect(0, 0, w, h);
      fctx.globalCompositeOperation = 'lighter';
      fogPuffsFull.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -p.r) p.x = w + p.r;
        if (p.x > w + p.r) p.x = -p.r;
        if (p.y < -p.r) p.y = h + p.r;
        if (p.y > h + p.r) p.y = -p.r;
        const swell = 1 + Math.sin(t * 0.0015 + p.phase) * 0.25;
        const g = fctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * swell);
        g.addColorStop(0, p.color + '0.16)');
        g.addColorStop(0.5, p.color + '0.07)');
        g.addColorStop(1, p.color + '0)');
        fctx.fillStyle = g;
        fctx.beginPath();
        fctx.arc(p.x, p.y, p.r * swell, 0, Math.PI * 2);
        fctx.fill();
      });
      fctx.globalCompositeOperation = 'source-over';
    }

    if (!fogPrefersReduced) {
      let fogStart = performance.now();
      (function fogAnim(now) {
        drawFog(now - fogStart);
        requestAnimationFrame(fogAnim);
      })(performance.now());
    }
  }

  // === LOGO 3D ORBIT (cursorOrbit) ===
  const navLogo = document.querySelector('.nav-logo');
  const logo3d = document.querySelector('.logo-3d');
  if (navLogo && logo3d && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let orbitTargetX = 0, orbitTargetY = 0, orbitCurX = 0, orbitCurY = 0, orbitActive = false;
    navLogo.addEventListener('mousemove', (e) => {
      const r = navLogo.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      orbitTargetY = px * 14;
      orbitTargetX = -py * 14;
      orbitActive = true;
    });
    navLogo.addEventListener('mouseleave', () => {
      orbitTargetX = 0;
      orbitTargetY = 0;
      orbitActive = false;
    });
    (function orbitLoop() {
      const k = 0.12;
      orbitCurX += (orbitTargetX - orbitCurX) * k;
      orbitCurY += (orbitTargetY - orbitCurY) * k;
      logo3d.style.transform = `rotateX(${orbitCurX.toFixed(2)}deg) rotateY(${orbitCurY.toFixed(2)}deg) translateY(${orbitActive ? 0 : -4}px)`;
      logo3d.style.animation = orbitActive ? 'none' : '';
      requestAnimationFrame(orbitLoop);
    })();
  }

  // === HERO CONSTELLATION ===
  const heroField = document.getElementById('heroField');
  const heroMouseLight = document.getElementById('heroMouseLight');
  if (heroField) {
    const fctx = heroField.getContext('2d');
    let stars = [];
    let fmouse = { x: -9999, y: -9999 };
    const COUNT = 70;

    function resizeHero() {
      const hero = document.querySelector('.hero');
      const rect = hero.getBoundingClientRect();
      heroField.width = rect.width;
      heroField.height = rect.height;
      stars = [];
      for (let i = 0; i < COUNT; i++) {
        stars.push({
          x: Math.random() * rect.width,
          y: Math.random() * rect.height,
          r: Math.random() * 1.4 + 0.4,
          sx: (Math.random() - 0.5) * 0.18,
          sy: (Math.random() - 0.5) * 0.18,
          tw: Math.random() * Math.PI * 2
        });
      }
    }
    resizeHero();
    window.addEventListener('resize', debounce(resizeHero, 150));

    function drawHero() {
      const w = heroField.width;
      const h = heroField.height;
      fctx.clearRect(0, 0, w, h);
      stars.forEach(s => {
        s.x += s.sx;
        s.y += s.sy;
        if (s.x < 0 || s.x > w) s.sx *= -1;
        if (s.y < 0 || s.y > h) s.sy *= -1;
        s.tw += 0.02;
        const alpha = 0.25 + Math.abs(Math.sin(s.tw)) * 0.35;
        fctx.beginPath();
        fctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        fctx.fillStyle = `rgba(178,255,255,${alpha})`;
        fctx.fill();
      });
      // connect stars to each other
      for (let i = 0; i < stars.length; i++) {
        for (let j = i + 1; j < stars.length; j++) {
          const dx = stars[i].x - stars[j].x;
          const dy = stars[i].y - stars[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            fctx.beginPath();
            fctx.strokeStyle = `rgba(0,135,189,${0.1 * (1 - dist / 130)})`;
            fctx.lineWidth = 0.5;
            fctx.moveTo(stars[i].x, stars[i].y);
            fctx.lineTo(stars[j].x, stars[j].y);
            fctx.stroke();
          }
        }
        // connect to mouse
        const md = Math.sqrt((stars[i].x - fmouse.x) ** 2 + (stars[i].y - fmouse.y) ** 2);
        if (md < 170) {
          fctx.beginPath();
          fctx.strokeStyle = `rgba(0,255,136,${0.35 * (1 - md / 170)})`;
          fctx.lineWidth = 0.8;
          fctx.moveTo(stars[i].x, stars[i].y);
          fctx.lineTo(fmouse.x, fmouse.y);
          fctx.stroke();
        }
      }
      requestAnimationFrame(drawHero);
    }
    drawHero();

    if (heroMouseLight) {
      document.addEventListener('mousemove', (e) => {
        const hero = document.querySelector('.hero');
        const rect = hero.getBoundingClientRect();
        const lx = e.clientX - rect.left;
        const ly = e.clientY - rect.top;
        fmouse.x = lx;
        fmouse.y = ly;
        if (rect.top < e.clientY && rect.bottom > e.clientY && rect.left < e.clientX && rect.right > e.clientX) {
          heroMouseLight.style.opacity = '1';
        } else {
          heroMouseLight.style.opacity = '0';
        }
        heroMouseLight.style.left = lx + 'px';
        heroMouseLight.style.top = ly + 'px';
      });
    }
  }

  // === HERO TYPING EFFECT ===
  const heroTitle = document.getElementById('heroTitle');
  if (heroTitle) {
    const words = Array.from(heroTitle.querySelectorAll('.hero-word'));
    const lines = Array.from(heroTitle.querySelectorAll('.hero-line'));

    const originals = words.map(w => w.dataset.text || w.textContent);

    let li = 0, ci = 0, lastT = 0;
    const speed = 120;

    words.forEach(w => { w.textContent = ''; });
    heroTitle.classList.add('is-anim');

    function type(timestamp) {
      if (!lastT) lastT = timestamp;
      const elapsed = timestamp - lastT;
      if (elapsed >= speed) {
        lastT = timestamp;
        const current = originals[li];
        ci++;
        words[li].textContent = current.slice(0, ci);
        if (ci >= current.length) {
          ci = 0;
          li++;
          if (li >= originals.length) {
            heroTitle.classList.add('typed');
            return;
          }
        }
      }
      requestAnimationFrame(type);
    }
    setTimeout(() => requestAnimationFrame(type), 1200);
  }
  const hero = document.querySelector('.hero');
  let lastScrollY = window.pageYOffset;
  const heroFadeEls = [
    '.hero-3d', '.hero-3d-instructions', '.hero-progress', '.hero-desc',
    '.hero-cta', '.hero-ais', '.hero-stats'
  ];
  window.addEventListener('scroll', debounce(() => {
    if (!hero) return;
    const y = window.pageYOffset;
    const heroBottom = hero.offsetTop + hero.offsetHeight;
    if (y < heroBottom) {
      hero.classList.toggle('is-scrolling-up', y < lastScrollY);
      hero.classList.toggle('is-scrolling-down', y > lastScrollY);
    }
    lastScrollY = y;
  }, 40));

  const heroFadeTargets = heroFadeEls.map(s => document.querySelector(s)).filter(Boolean);
  function updateHeroFade() {
    if (!hero || heroFadeTargets.length === 0) return;
    const y = window.pageYOffset;
    const start = hero.offsetTop;
    const total = hero.offsetHeight * 0.9;
    const p = Math.min(1, Math.max(0, (y - start) / total));
    const opacity = (1 - p).toFixed(3);
    heroFadeTargets.forEach(el => {
      el.style.opacity = opacity;
      el.style.pointerEvents = p >= 0.98 ? 'none' : '';
    });
  }
  updateHeroFade();
  window.addEventListener('scroll', () => requestAnimationFrame(updateHeroFade), { passive: true });
  window.addEventListener('resize', debounce(updateHeroFade, 150));

  // === AI SITES TAB FILTER ===
  const aiTabs = document.querySelectorAll('.ai-tab');
  const aiCards = document.querySelectorAll('.ai-site-card');
  if (aiTabs.length && aiCards.length) {
    aiTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        aiTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const cat = tab.dataset.cat;
        aiCards.forEach(card => {
          if (cat === 'all' || card.dataset.cat === cat) {
            card.style.display = '';
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            requestAnimationFrame(() => {
              card.style.transition = 'opacity 0.3s, transform 0.3s';
              card.style.opacity = '1';
              card.style.transform = 'translateY(0)';
            });
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }
});
