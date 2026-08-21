// ==UserScript==
// @name         HubVision Prompt Collector v2
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Coleta prompts quando voce curte mensagens com foto no Telegram Web
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
            max-width: 350px !important;
        }
        .hv-notification.success {
            background: linear-gradient(135deg, #00c853, #009624) !important;
        }
        .hv-notification.error {
            background: linear-gradient(135deg, #ff4444, #cc0000) !important;
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
        .hv-last {
            font-size: 11px !important;
            color: #888 !important;
            margin-top: 10px !important;
            text-align: center !important;
            max-height: 60px !important;
            overflow: hidden !important;
        }
    `;
    document.head.appendChild(style);

    // Notificacao
    function showNotification(msg, type) {
        var d = document.createElement('div');
        d.className = 'hv-notification ' + (type || '');
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(function() { d.remove(); }, 4000);
    }

    // Extrair dados da mensagem
    function extractData(messageEl) {
        var text = '';
        var imageUrl = '';

        // Tentar varios seletores de texto
        var textSelectors = [
            '.text-content',
            '.message-text',
            '.rich-text',
            '.media-caption',
            '.text',
            '[class*="text"]',
            '.peer-title'
        ];

        for (var i = 0; i < textSelectors.length; i++) {
            var el = messageEl.querySelector(textSelectors[i]);
            if (el && el.innerText) {
                text = el.innerText;
                break;
            }
        }

        // Tentar varios seletores de imagem
        var imgSelectors = [
            'img.media-photo',
            'img.media-image',
            'img[src*="file"]',
            'img[src*="telegram"]',
            'img[class*="media"]',
            'video',
            '.media-container img',
            '.media-photo',
            '.media-image'
        ];

        for (var j = 0; j < imgSelectors.length; j++) {
            var imgEl = messageEl.querySelector(imgSelectors[j]);
            if (imgEl) {
                imageUrl = imgEl.src || imgEl.poster || '';
                if (imageUrl) break;
            }
        }

        return { text: text.trim(), imageUrl: imageUrl };
    }

    // Salvar prompt
    function savePrompt(data) {
        var prompt = {
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

        // Atualizar painel
        var countEl = document.getElementById('hv-count');
        if (countEl) countEl.textContent = collectedPrompts.length;

        var lastEl = document.getElementById('hv-last');
        if (lastEl) {
            var preview = data.text ? data.text.substring(0, 50) : 'Sem texto';
            lastEl.textContent = 'Ultimo: ' + preview + '...';
        }

        console.log('[HubVision] Coletado:', prompt);
    }

    // Verificar se a mensagem tem imagem
    function hasImage(messageEl) {
        var imgChecks = [
            'img.media-photo',
            'img.media-image',
            'img[src*="file"]',
            'img[src*="telegram"]',
            'img[class*="media"]',
            'video',
            '.media-container',
            '.media-photo',
            '.media-image',
            '.grouped-item img'
        ];

        for (var i = 0; i < imgChecks.length; i++) {
            if (messageEl.querySelector(imgChecks[i])) return true;
        }
        return false;
    }

    // Encontrar mensagem pai
    function findMessage(element) {
        var selectors = [
            '.Message',
            '.message',
            '.bubble',
            '[data-message-id]',
            '.message-content',
            '.media-inner'
        ];

        for (var i = 0; i < selectors.length; i++) {
            var msg = element.closest(selectors[i]);
            if (msg) return msg;
        }
        return null;
    }

    // Verificar se e botao de reacao
    function isReactionButton(element) {
        var selectors = [
            '.ReactionButton',
            '.reaction-btn',
            '[data-react]',
            'button[title*="Like"]',
            'button[title*="Curtir"]',
            'button[title*="Gostei"]',
            'button[title*="reagir"]',
            'button[title*="reaction"]',
            '.btn-icon.reaction',
            '.toggle-btn',
            '[class*="reaction"]',
            '[class*="Reaction"]'
        ];

        for (var i = 0; i < selectors.length; i++) {
            if (element.closest(selectors[i])) return true;
        }

        // Verificar por emoji comum
        var text = element.textContent || '';
        if (['👍', '❤️', '😂', '😮', '😢', '🔥', '👏', '🎉'].indexOf(text.trim()) !== -1) {
            return true;
        }

        return false;
    }

    // Monitorar cliques
    document.addEventListener('click', function(e) {
        var target = e.target;

        // Verificar se e reacao
        if (!isReactionButton(target)) return;

        // Encontrar mensagem
        var msg = findMessage(target);
        if (!msg) return;

        // Verificar se tem imagem
        if (!hasImage(msg)) return;

        // Coletar apos delay
        setTimeout(function() {
            var data = extractData(msg);
            if (data.text || data.imageUrl) {
                savePrompt(data);
            }
        }, 500);
    }, true);

    // Monitorar mutacoes do DOM
    var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].type === 'childList') {
                // Verificar novos botoes de reacao
                var reactions = document.querySelectorAll('[class*="reaction"], [class*="Reaction"]');
                reactions.forEach(function(r) {
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

    // Criar painel
    function createPanel() {
        var existing = document.getElementById('hv-panel');
        if (existing) existing.remove();

        var panel = document.createElement('div');
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
                    <div class="stat-num" style="color:#00c853">ON</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
            <div class="hv-last" id="hv-last">Aguardando reacoes...</div>
            <div style="text-align:center;margin-top:10px">
                <button class="hv-btn" onclick="hvExport()">Exportar JSON</button>
                <button class="hv-btn secondary" onclick="hvClear()">Limpar</button>
            </div>
        `;
        document.body.appendChild(panel);
    }

    // Funcoes globais
    window.hvExport = function() {
        var data = JSON.stringify(collectedPrompts, null, 2);
        var blob = new Blob([data], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'hubvision_prompts_' + Date.now() + '.json';
        a.click();
        showNotification('Exportado ' + collectedPrompts.length + ' prompts!', 'success');
    };

    window.hvClear = function() {
        if (confirm('Limpar todos os prompts?')) {
            collectedPrompts = [];
            localStorage.removeItem('hv_prompts');
            var c = document.getElementById('hv-count');
            if (c) c.textContent = '0';
        }
    };

    window.hvPrompts = function() { return collectedPrompts; };

    window.hvDebug = function() {
        console.log('[HubVision] Prompts coletados:', collectedPrompts);
        console.log('[HubVision] Total:', collectedPrompts.length);
    };

    // Iniciar
    setTimeout(function() {
        createPanel();
        showNotification('HubVision Collector v2 ATIVO!', 'success');
        console.log('%c[HubVision] Coletor v2 Iniciado!', 'color: #00d4ff; font-size: 16px; font-weight: bold;');
        console.log('Curte uma mensagem com foto para coletar.');
        console.log('Use hvExport() para exportar.');
        console.log('Use hvDebug() para ver dados.');
    }, 3000);

})();
