// ==UserScript==
// @name         HubVision Prompt Collector v3
// @namespace    http://tampermonkey.net/
// @version      3.0
// @description  Coleta prompts com um clique nas mensagens com foto
// @author       HubVision
// @match        https://web.telegram.org/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    var collectedPrompts = JSON.parse(localStorage.getItem('hv_prompts') || '[]');

    // Estilos
    var style = document.createElement('style');
    style.textContent = `
        .hv-save-btn {
            position: absolute !important;
            bottom: 5px !important;
            right: 5px !important;
            background: linear-gradient(135deg, #0087BD, #00d4ff) !important;
            color: white !important;
            border: none !important;
            padding: 6px 12px !important;
            border-radius: 20px !important;
            font-size: 11px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            z-index: 100 !important;
            opacity: 0 !important;
            transition: opacity 0.2s !important;
            box-shadow: 0 2px 10px rgba(0,135,189,0.4) !important;
        }
        .hv-save-btn:hover {
            transform: scale(1.05) !important;
        }
        .hv-message:hover .hv-save-btn {
            opacity: 1 !important;
        }
        .hv-message {
            position: relative !important;
        }
        .hv-notification {
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            background: linear-gradient(135deg, #00c853, #009624) !important;
            color: white !important;
            padding: 15px 25px !important;
            border-radius: 10px !important;
            font-family: 'Segoe UI', sans-serif !important;
            font-size: 14px !important;
            z-index: 999999 !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
            animation: hvSlide 0.3s ease !important;
        }
        @keyframes hvSlide {
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
        .hv-btn.secondary {
            background: rgba(255,255,255,0.1) !important;
        }
    `;
    document.head.appendChild(style);

    // Notificacao
    function showNotification(msg) {
        var d = document.createElement('div');
        d.className = 'hv-notification';
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(function() { d.remove(); }, 3000);
    }

    // Verificar se tem imagem
    function hasImage(el) {
        return el.querySelector('img.media-photo, img.media-image, img[src*="file"], video, .media-container, .media-photo, .media-image');
    }

    // Extrair dados
    function extractData(el) {
        var text = '';
        var imageUrl = '';

        // Texto
        var textEl = el.querySelector('.text-content, .message-text, .rich-text, .media-caption');
        if (textEl) text = textEl.innerText || textEl.textContent;

        // Imagem
        var imgEl = el.querySelector('img.media-photo, img.media-image, img[src*="file"]');
        if (imgEl) imageUrl = imgEl.src;

        return { text: text.trim(), imageUrl: imageUrl };
    }

    // Salvar prompt
    function savePrompt(data, messageEl) {
        var prompt = {
            id: Date.now(),
            text: data.text,
            image_url: data.imageUrl,
            source: 'Telegram Web',
            collected_at: new Date().toISOString()
        };

        collectedPrompts.push(prompt);
        localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));

        // Feedback visual
        var btn = messageEl.querySelector('.hv-save-btn');
        if (btn) {
            btn.textContent = 'SALVO!';
            btn.style.background = 'linear-gradient(135deg, #00c853, #009624)';
            setTimeout(function() {
                btn.textContent = 'SALVAR PROMPT';
                btn.style.background = '';
            }, 1500);
        }

        showNotification('Prompt coletado! (' + collectedPrompts.length + ' total)');

        // Atualizar painel
        var c = document.getElementById('hv-count');
        if (c) c.textContent = collectedPrompts.length;
    }

    // Adicionar botoes de salvar
    function addSaveButtons() {
        var messages = document.querySelectorAll('.Message:not(.hv-processed), .message:not(.hv-processed), .bubble:not(.hv-processed)');

        messages.forEach(function(msg) {
            if (!hasImage(msg)) return;

            msg.classList.add('hv-processed');
            msg.classList.add('hv-message');

            var btn = document.createElement('button');
            btn.className = 'hv-save-btn';
            btn.textContent = 'SALVAR PROMPT';
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                var data = extractData(msg);
                if (data.text || data.imageUrl) {
                    savePrompt(data, msg);
                } else {
                    showNotification('Nao encontrou texto ou imagem');
                }
            };

            msg.appendChild(btn);
        });
    }

    // Monitorar novas mensagens
    var observer = new MutationObserver(function() {
        addSaveButtons();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Criar painel
    function createPanel() {
        var existing = document.getElementById('hv-panel');
        if (existing) existing.remove();

        var panel = document.createElement('div');
        panel.id = 'hv-panel';
        panel.className = 'hv-panel';
        panel.innerHTML = '<h3>HubVision Collector v3</h3>' +
            '<div class="stats">' +
                '<div class="stat"><div class="stat-num" id="hv-count">' + collectedPrompts.length + '</div><div class="stat-label">Coletados</div></div>' +
                '<div class="stat"><div class="stat-num" style="color:#00c853">ON</div><div class="stat-label">Status</div></div>' +
            '</div>' +
            '<div style="text-align:center;font-size:12px;color:#888;margin-bottom:10px">Passe o mouse na msg e clique em SALVAR</div>' +
            '<div style="text-align:center">' +
                '<button class="hv-btn" onclick="hvExport()">Exportar JSON</button>' +
                '<button class="hv-btn secondary" onclick="hvClear()">Limpar</button>' +
            '</div>';
        document.body.appendChild(panel);
    }

    // Funcoes globais
    window.hvExport = function() {
        var d = JSON.stringify(collectedPrompts, null, 2);
        var b = new Blob([d], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = 'hubvision_prompts_' + Date.now() + '.json';
        a.click();
        showNotification('Exportado ' + collectedPrompts.length + ' prompts!');
    };

    window.hvClear = function() {
        if (confirm('Limpar todos?')) {
            collectedPrompts = [];
            localStorage.removeItem('hv_prompts');
            var c = document.getElementById('hv-count');
            if (c) c.textContent = '0';
        }
    };

    // Iniciar
    setTimeout(function() {
        createPanel();
        addSaveButtons();
        showNotification('HubVision v3 ATIVO! Passe o mouse nas msgs com foto');
        console.log('%c[HubVision] v3 Iniciado!', 'color: #00d4ff; font-size: 16px; font-weight: bold;');
    }, 2000);

})();
