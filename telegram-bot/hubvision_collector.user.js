// ==UserScript==
// @name         HubVision Prompt Collector
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Coleta prompts automaticamente quando voce curte mensagens com foto no Telegram Web
// @author       HubVision
// @match        https://web.telegram.org/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // Configuracoes
    const CONFIG = {
        SHOW_NOTIFICATIONS: true,
        AUTO_COLLECT: true
    };

    // Banco de dados local
    let collectedPrompts = JSON.parse(localStorage.getItem('hv_prompts') || '[]');

    // Criar estilos
    const style = document.createElement('style');
    style.textContent = `
        .hv-notification {
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            background: linear-gradient(135deg, #0087BD, #00d4ff) !important;
            color: white !important;
            padding: 15px 25px !important;
            border-radius: 10px !important;
            font-family: 'Segoe UI', sans-serif !important;
            font-size: 14px !important;
            z-index: 999999 !important;
            box-shadow: 0 4px 20px rgba(0,135,189,0.4) !important;
            animation: hvSlideIn 0.3s ease !important;
            max-width: 350px !important;
        }
        .hv-notification.success {
            background: linear-gradient(135deg, #00c853, #009624) !important;
        }
        @keyframes hvSlideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .hv-panel {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            background: #1a1a2e !important;
            border: 1px solid rgba(0,135,189,0.3) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            z-index: 999998 !important;
            color: white !important;
            font-family: 'Segoe UI', sans-serif !important;
            min-width: 280px !important;
            box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
        }
        .hv-panel h3 {
            margin: 0 0 15px 0 !important;
            color: #00d4ff !important;
            font-size: 16px !important;
        }
        .hv-panel .stats {
            display: flex !important;
            justify-content: space-around !important;
            margin-bottom: 15px !important;
        }
        .hv-panel .stat { text-align: center !important; }
        .hv-panel .stat-num {
            font-size: 24px !important;
            font-weight: bold !important;
            color: #00d4ff !important;
        }
        .hv-panel .stat-label {
            font-size: 11px !important;
            color: #888 !important;
        }
        .hv-btn {
            background: linear-gradient(135deg, #0087BD, #00d4ff) !important;
            border: none !important;
            color: white !important;
            padding: 10px 18px !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 13px !important;
            margin: 4px !important;
        }
        .hv-btn:hover { opacity: 0.9 !important; }
        .hv-btn.secondary {
            background: rgba(255,255,255,0.1) !important;
        }
    `;
    document.head.appendChild(style);

    // Mostrar notificacao
    function showNotification(msg, type) {
        if (!CONFIG.SHOW_NOTIFICATIONS) return;
        const div = document.createElement('div');
        div.className = 'hv-notification ' + (type || '');
        div.textContent = msg;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 4000);
    }

    // Extrair dados da mensagem
    function extractData(messageEl) {
        let text = '';
        let imageUrl = '';

        // Texto
        const textEl = messageEl.querySelector('.text-content, .message-text, .rich-text, .media-caption');
        if (textEl) text = textEl.innerText || textEl.textContent;

        // Imagem
        const imgEl = messageEl.querySelector('img.media-photo, img.media-image, img[src*="file"]');
        if (imgEl) imageUrl = imgEl.src;

        // Video
        const videoEl = messageEl.querySelector('video');
        if (videoEl && !imageUrl) imageUrl = videoEl.poster || '';

        return { text: text.trim(), imageUrl };
    }

    // Salvar prompt
    function savePrompt(data) {
        const prompt = {
            id: Date.now(),
            text: data.text,
            image_url: data.imageUrl,
            source: 'Telegram Web',
            collected_at: new Date().toISOString(),
            chat_name: document.querySelector('.chat-info-container .peer-title')?.innerText || 'Desconhecido'
        };

        collectedPrompts.push(prompt);
        localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));
        showNotification('Prompt coletado! (' + collectedPrompts.length + ' total)', 'success');
        console.log('[HubVision] Coletado:', prompt);

        // Atualizar painel
        const countEl = document.getElementById('hv-count');
        if (countEl) countEl.textContent = collectedPrompts.length;
    }

    // Monitorar cliques
    document.addEventListener('click', function(e) {
        // Verificar se e botao de reacao
        const btn = e.target.closest('.ReactionButton, [data-react], button[title*="Like"], button[title*="Curtir"], button[title*="Gostei"]');
        if (!btn) return;

        // Encontrar mensagem
        const msg = btn.closest('.Message, .message, .bubble, [data-message-id]');
        if (!msg) return;

        // Verificar se tem imagem
        const hasImage = msg.querySelector('.media-photo, .media-image, img[src*="file"], video, .media-container');
        if (!hasImage) return;

        // Coletar apos delay
        setTimeout(() => {
            const data = extractData(msg);
            if (data.text || data.imageUrl) savePrompt(data);
        }, 300);
    }, true);

    // Criar painel
    function createPanel() {
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
                    <div class="stat-num">ON</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
            <div style="text-align:center">
                <button class="hv-btn" onclick="hvExport()">Exportar JSON</button>
                <button class="hv-btn secondary" onclick="hvClear()">Limpar</button>
            </div>
        `;
        document.body.appendChild(panel);
    }

    // Funcoes globais
    window.hvExport = function() {
        const data = JSON.stringify(collectedPrompts, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'hubvision_prompts_' + Date.now() + '.json';
        a.click();
        showNotification('Exportado ' + collectedPrompts.length + ' prompts!', 'success');
    };

    window.hvClear = function() {
        if (confirm('Limpar todos os prompts?')) {
            collectedPrompts = [];
            localStorage.removeItem('hv_prompts');
            document.getElementById('hv-count').textContent = '0';
        }
    };

    window.hvPrompts = function() { return collectedPrompts; };

    // Iniciar
    setTimeout(() => {
        createPanel();
        showNotification('HubVision Collector ATIVO!', 'success');
        console.log('%c[HubVision] Coletor Iniciado!', 'color: #00d4ff; font-size: 16px; font-weight: bold;');
        console.log('Curte uma mensagem com foto para coletar.');
        console.log('Use hvExport() para exportar.');
    }, 3000);

})();
