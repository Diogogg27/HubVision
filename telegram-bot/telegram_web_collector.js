// =============================================================
// HubVision - Coletor de Prompts via Telegram Web
// =============================================================
// COMO USAR:
// 1. Abra https://web.telegram.org
// 2. Abra o Console (F12 -> Console)
// 3. Cole todo este codigo e pressione Enter
// 4. Curta uma mensagem com foto e o prompt sera coletado!
// =============================================================

(function() {
  'use strict';

  const CONFIG = {
    REACTION_KEYWORDS: ['like', 'heart', 'thumbsup', '👍', '❤️', 'curtir', 'gostei'],
    AUTO_DOWNLOAD: true,
    SHOW_NOTIFICATIONS: true,
    SAVE_FORMAT: 'json' // json ou txt
  };

  let collectedPrompts = [];
  let isMonitoring = false;

  // Estilo da notificacao
  const notifStyle = document.createElement('style');
  notifStyle.textContent = `
    .hv-notification {
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #0087BD, #00d4ff);
      color: white;
      padding: 15px 25px;
      border-radius: 10px;
      font-family: 'Segoe UI', sans-serif;
      font-size: 14px;
      z-index: 99999;
      box-shadow: 0 4px 20px rgba(0,135,189,0.4);
      animation: hvSlideIn 0.3s ease;
      max-width: 350px;
    }
    .hv-notification.error {
      background: linear-gradient(135deg, #ff4444, #cc0000);
    }
    .hv-notification.success {
      background: linear-gradient(135deg, #00c853, #009624);
    }
    @keyframes hvSlideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    .hv-panel {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1a1a2e;
      border: 1px solid rgba(0,135,189,0.3);
      border-radius: 12px;
      padding: 20px;
      z-index: 99998;
      color: white;
      font-family: 'Segoe UI', sans-serif;
      min-width: 300px;
      box-shadow: 0 4px 30px rgba(0,0,0,0.5);
    }
    .hv-panel h3 {
      margin: 0 0 15px 0;
      color: #00d4ff;
      font-size: 16px;
    }
    .hv-panel .stats {
      display: flex;
      justify-content: space-around;
      margin-bottom: 15px;
    }
    .hv-panel .stat {
      text-align: center;
    }
    .hv-panel .stat-num {
      font-size: 24px;
      font-weight: bold;
      color: #00d4ff;
    }
    .hv-panel .stat-label {
      font-size: 11px;
      color: #888;
    }
    .hv-btn {
      background: linear-gradient(135deg, #0087BD, #00d4ff);
      border: none;
      color: white;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      margin: 5px;
      transition: transform 0.2s;
    }
    .hv-btn:hover {
      transform: scale(1.05);
    }
    .hv-btn.secondary {
      background: rgba(255,255,255,0.1);
    }
  `;
  document.head.appendChild(notifStyle);

  function showNotification(msg, type = 'info') {
    if (!CONFIG.SHOW_NOTIFICATIONS) return;
    const div = document.createElement('div');
    div.className = `hv-notification ${type}`;
    div.textContent = msg;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 4000);
  }

  function extractPromptFromMessage(messageEl) {
    let text = '';
    let imageUrl = '';

    // Pegar texto da mensagem
    const textEl = messageEl.querySelector('.text-content, .message-text, .peer-title, .rich-text');
    if (textEl) {
      text = textEl.innerText || textEl.textContent;
    }

    // Pegar caption da foto (se tiver)
    const captionEl = messageEl.querySelector('.media-caption, .message-text');
    if (captionEl) {
      text = captionEl.innerText || captionEl.textContent;
    }

    // Pegar URL da imagem
    const imgEl = messageEl.querySelector('img.media-photo, img.media-image, img[src*="file"]');
    if (imgEl) {
      imageUrl = imgEl.src;
    }

    // Pegar video thumbnail se tiver
    const videoEl = messageEl.querySelector('video');
    if (videoEl && !imageUrl) {
      imageUrl = videoEl.poster || '';
    }

    return { text: text.trim(), imageUrl };
  }

  function savePrompt(data) {
    const prompt = {
      id: Date.now(),
      text: data.text,
      image_url: data.imageUrl,
      source: 'Telegram Web',
      collected_at: new Date().toISOString(),
      chat_name: getCurrentChatName()
    };

    collectedPrompts.push(prompt);
    showNotification(`Prompt coletado! (${collectedPrompts.length} total)`, 'success');

    // Salvar no localStorage
    localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));

    console.log('[HubVision] Prompt coletado:', prompt);
  }

  function getCurrentChatName() {
    const chatTitle = document.querySelector('.chat-info-container .peer-title');
    return chatTitle ? chatTitle.innerText : 'Desconhecido';
  }

  function handleReaction(event) {
    // Verificar se e uma reacao de like/curtir
    const target = event.target;
    const isReaction = target.closest('.ReactionButton, .reaction-btn, [data-react]');

    if (!isReaction) return;

    // Encontrar a mensagem pai
    const messageEl = target.closest('.Message, .message, .bubble, [data-message-id]');
    if (!messageEl) return;

    // Verificar se tem imagem
    const hasImage = messageEl.querySelector('.media-photo, .media-image, img[src*="file"], video');

    if (!hasImage) return;

    // Extrair dados
    const data = extractPromptFromMessage(messageEl);

    if (data.text || data.imageUrl) {
      savePrompt(data);
    }
  }

  function handleClick(event) {
    // Detectar clique em botoes de reacao
    const target = event.target;

    // Verificar se e um botao de reacao
    const isReactionBtn = target.closest(
      '.ReactionButton, ' +
      '.reaction-btn, ' +
      '[data-react], ' +
      '.btn-icon.reaction, ' +
      '.toggle-btn, ' +
      'button[title*="Like"], ' +
      'button[title*="Curtir"], ' +
      'button[title*="Gostei"]'
    );

    if (!isReactionBtn) return;

    // Encontrar a mensagem
    const messageEl = target.closest('.Message, .message, .bubble, [data-message-id]');
    if (!messageEl) return;

    // Verificar se tem imagem
    const hasImage = messageEl.querySelector(
      '.media-photo, .media-image, img[src*="file"], video, .media-container'
    );

    if (!hasImage) return;

    // Delay para capturar a reacao
    setTimeout(() => {
      const data = extractPromptFromMessage(messageEl);
      if (data.text || data.imageUrl) {
        savePrompt(data);
      }
    }, 300);
  }

  function observeReactions() {
    if (isMonitoring) return;
    isMonitoring = true;

    // Monitorar cliques
    document.addEventListener('click', handleClick, true);

    // Monitorar mutacoes do DOM
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList') {
          // Verificar se novas reacoes apareceram
          const reactions = document.querySelectorAll('.ReactionButton, .reaction-btn');
          reactions.forEach(r => {
            if (!r.dataset.hvMonitored) {
              r.dataset.hvMonitored = 'true';
            }
          });
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    showNotification('HubVision Monitor ATIVO! Curte uma msg com foto.', 'success');
  }

  function createPanel() {
    // Remover painel existente
    const existing = document.getElementById('hv-panel');
    if (existing) existing.remove();

    const panel = document.createElement('div');
    panel.id = 'hv-panel';
    panel.className = 'hv-panel';
    panel.innerHTML = `
      <h3>HubVision Collector</h3>
      <div class="stats">
        <div class="stat">
          <div class="stat-num" id="hv-count">${collectedPrompts.length}</div>
          <div class="stat-label">Coletados</div>
        </div>
        <div class="stat">
          <div class="stat-num" id="hv-status">ON</div>
          <div class="stat-label">Status</div>
        </div>
      </div>
      <div style="text-align: center;">
        <button class="hv-btn" onclick="hvExport()">Exportar JSON</button>
        <button class="hv-btn secondary" onclick="hvClear()">Limpar</button>
        <button class="hv-btn secondary" onclick="document.getElementById('hv-panel').remove()">Fechar</button>
      </div>
    `;
    document.body.appendChild(panel);
  }

  function exportPrompts() {
    const data = JSON.stringify(collectedPrompts, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hubvision_prompts_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification(`Exportado ${collectedPrompts.length} prompts!`, 'success');
  }

  function clearPrompts() {
    if (confirm('Limpar todos os prompts coletados?')) {
      collectedPrompts = [];
      localStorage.removeItem('hv_prompts');
      document.getElementById('hv-count').textContent = '0';
      showNotification('Prompts limpos!', 'info');
    }
  }

  // Funcoes globais
  window.hvExport = exportPrompts;
  window.hvClear = clearPrompts;
  window.hvShow = createPanel;
  window.hvStart = observeReactions;
  window.hvPrompts = () => collectedPrompts;

  // Carregar prompts salvos
  const saved = localStorage.getItem('hv_prompts');
  if (saved) {
    try {
      collectedPrompts = JSON.parse(saved);
    } catch(e) {}
  }

  // Iniciar automaticamente
  observeReactions();
  createPanel();

  console.log('%c[HubVision] Coletor Iniciado!', 'color: #00d4ff; font-size: 16px; font-weight: bold;');
  console.log('%cCurte uma mensagem com foto para coletar o prompt.', 'color: #888;');
  console.log('%cComandos: hvExport(), hvClear(), hvShow(), hvPrompts()', 'color: #888;');

})();
