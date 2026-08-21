// HubVision membership shell. Replace local session calls with the auth API before launch.
(function () {
  const modal = document.getElementById('authModal');
  const form = document.getElementById('authForm');
  const feedback = document.getElementById('authFeedback');
  const submit = document.getElementById('authSubmit');
  if (!modal || !form) return;

  let mode = 'login';

  async function refreshSession() {
    const token = localStorage.getItem('hubvision.authToken');
    if (!token || window.location.protocol === 'file:') return;
    try {
      const response = await fetch('/api/auth/me', { headers: { authorization: `Bearer ${token}` } });
      if (!response.ok) return localStorage.removeItem('hubvision.authToken');
      const result = await response.json();
      localStorage.setItem('hubvision.user', JSON.stringify(result.user));
    } catch {
      // The public landing page remains usable if the API is temporarily offline.
    }
  }

  refreshSession();

  function setMode(nextMode) {
    mode = nextMode;
    document.querySelectorAll('[data-auth-tab]').forEach((tab) => {
      tab.classList.toggle('is-active', tab.dataset.authTab === mode);
    });
    submit.textContent = mode === 'signup' ? 'Criar conta grátis' : 'Entrar na plataforma';
    feedback.textContent = '';
  }

  function openAuth(nextMode = 'login') {
    setMode(nextMode);
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.getElementById('authEmail').focus();
  }

  function closeAuth() {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  }

  function showAuthLoading() {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'auth-loading';
      overlay.innerHTML = `
        <div class="auth-loading-orbit" aria-hidden="true"></div>
        <div class="auth-loading-card" role="status" aria-live="polite">
          <span class="auth-loading-kicker">HUBVISION / ACCESS</span>
          <strong class="auth-loading-title">Preparando seu acesso</strong>
          <span class="auth-loading-status">Validando credenciais</span>
          <div class="auth-loading-track"><span class="auth-loading-progress"></span></div>
          <span class="auth-loading-percent">00%</span>
        </div>`;
      document.body.appendChild(overlay);
      const status = overlay.querySelector('.auth-loading-status');
      const progress = overlay.querySelector('.auth-loading-progress');
      const percent = overlay.querySelector('.auth-loading-percent');
      const steps = [
        ['Validando credenciais', 28],
        ['Sincronizando biblioteca', 68],
        ['Acesso liberado', 100]
      ];
      requestAnimationFrame(() => overlay.classList.add('is-visible'));
      steps.forEach(([label, value], index) => {
        window.setTimeout(() => {
          status.textContent = label;
          progress.style.width = `${value}%`;
          percent.textContent = `${String(value).padStart(2, '0')}%`;
        }, index * 420);
      });
      window.setTimeout(() => {
        overlay.classList.add('is-done');
        window.setTimeout(() => {
          overlay.remove();
          resolve();
        }, 260);
      }, 1420);
    });
  }

  window.addEventListener('hubvision:upgrade', () => {
    if (!localStorage.getItem('hubvision.authToken')) return openAuth('login');
    document.getElementById('precos')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

  document.querySelectorAll('[data-open-auth]').forEach((trigger) => {
    trigger.addEventListener('click', () => openAuth(trigger.dataset.authMode || 'login'));
  });
  document.querySelectorAll('[data-close-auth]').forEach((trigger) => trigger.addEventListener('click', closeAuth));
  document.querySelectorAll('[data-auth-tab]').forEach((tab) => tab.addEventListener('click', () => setMode(tab.dataset.authTab)));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('is-open')) closeAuth();
  });

  async function startCheckout() {
    const token = localStorage.getItem('hubvision.authToken');
    if (!token) return openAuth('login');
    const response = await fetch('/api/billing/checkout', { method: 'POST', headers: { authorization: `Bearer ${token}` } });
    const result = await response.json();
    if (response.ok && result.checkoutUrl) window.location.href = result.checkoutUrl;
    else window.alert(result.error || 'Nao foi possivel iniciar a assinatura.');
  }

  document.querySelectorAll('[data-start-checkout]').forEach((trigger) => trigger.addEventListener('click', startCheckout));

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form));
    const endpoint = mode === 'signup' ? '/api/auth/signup' : '/api/auth/login';
    try {
      const response = await fetch(endpoint, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Nao foi possivel concluir o acesso.');
      localStorage.setItem('hubvision.authToken', result.token);
      localStorage.setItem('hubvision.user', JSON.stringify(result.user));
      closeAuth();
      await showAuthLoading();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      window.location.reload();
    } catch (error) {
      feedback.textContent = window.location.protocol === 'file:'
        ? 'Inicie o servidor local para ativar o login real.'
        : error.message;
      feedback.classList.remove('is-success');
    }
  });
})();
