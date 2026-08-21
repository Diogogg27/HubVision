// ==UserScript==
// @name         HubVision Simple Collector
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Lista prompts com imagem - voce clica pra salvar
// @match        https://web.telegram.org/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    var collectedPrompts = JSON.parse(localStorage.getItem('hv_prompts') || '[]');
    var lastImages = [];

    // Notificacao simples
    function notify(msg) {
        var d = document.createElement('div');
        d.style.cssText = 'position:fixed;top:20px;right:20px;background:#00c853;color:white;padding:15px 25px;border-radius:10px;z-index:999999;font-family:sans-serif;font-size:14px';
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(function() { d.remove(); }, 3000);
    }

    // Pegar todas as imagens da tela
    function scanImages() {
        lastImages = [];
        var allImgs = document.querySelectorAll('img');

        allImgs.forEach(function(img, i) {
            // Filtrar imagens de perfil e icones pequenos
            if (img.width < 100 || img.height < 100) return;
            if (img.src.includes('avatar') || img.src.includes('profile')) return;
            if (img.src.includes('emoji')) return;

            // Encontrar texto proximo
            var parent = img.closest('.Message, .message, .bubble, [data-message-id], .media-container');
            var text = '';
            if (parent) {
                var textEl = parent.querySelector('.text-content, .message-text, .media-caption');
                if (textEl) text = textEl.innerText || textEl.textContent;
            }

            lastImages.push({
                index: i,
                src: img.src,
                text: text.trim().substring(0, 100),
                element: img
            });
        });

        updatePanel();
    }

    // Atualizar painel
    function updatePanel() {
        var list = document.getElementById('hv-list');
        if (!list) return;

        if (lastImages.length === 0) {
            list.innerHTML = '<div style="color:#888;text-align:center;padding:10px">Nenhuma imagem encontrada</div>';
            return;
        }

        var html = '';
        lastImages.forEach(function(img, i) {
            var preview = img.text || 'Sem texto';
            html += '<div style="display:flex;align-items:center;gap:10px;padding:8px;margin:5px 0;background:rgba(255,255,255,0.05);border-radius:6px;cursor:pointer" onclick="hvSave(' + i + ')">';
            html += '<img src="' + img.src + '" style="width:40px;height:40px;object-fit:cover;border-radius:4px">';
            html += '<div style="flex:1;font-size:11px;color:#aaa;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">' + preview + '</div>';
            html += '<button style="background:#0087BD;color:white;border:none;padding:4px 8px;border-radius:4px;font-size:10px;cursor:pointer">Salvar</button>';
            html += '</div>';
        });
        list.innerHTML = html;
    }

    // Salvar prompt
    window.hvSave = function(index) {
        var img = lastImages[index];
        if (!img) return;

        var prompt = {
            id: Date.now(),
            text: img.text,
            image_url: img.src,
            source: 'Telegram Web',
            collected_at: new Date().toISOString()
        };

        collectedPrompts.push(prompt);
        localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));

        var c = document.getElementById('hv-count');
        if (c) c.textContent = collectedPrompts.length;

        notify('Prompt salvo! (' + collectedPrompts.length + ' total)');
    };

    // Salvar todos
    window.hvSaveAll = function() {
        lastImages.forEach(function(img, i) {
            var prompt = {
                id: Date.now() + i,
                text: img.text,
                image_url: img.src,
                source: 'Telegram Web',
                collected_at: new Date().toISOString()
            };
            collectedPrompts.push(prompt);
        });
        localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));
        var c = document.getElementById('hv-count');
        if (c) c.textContent = collectedPrompts.length;
        notify('Salvos ' + lastImages.length + ' prompts!');
    };

    // Exportar
    window.hvExport = function() {
        var d = JSON.stringify(collectedPrompts, null, 2);
        var b = new Blob([d], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = 'prompts_' + Date.now() + '.json';
        a.click();
        notify('Exportado ' + collectedPrompts.length + ' prompts!');
    };

    // Limpar
    window.hvClear = function() {
        if (confirm('Limpar?')) {
            collectedPrompts = [];
            localStorage.removeItem('hv_prompts');
            var c = document.getElementById('hv-count');
            if (c) c.textContent = '0';
        }
    };

    // Criar painel
    function createPanel() {
        var p = document.createElement('div');
        p.id = 'hv-panel';
        p.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#1a1a2e;border:1px solid rgba(0,135,189,0.3);border-radius:12px;padding:20px;z-index:999998;color:white;font-family:sans-serif;width:350px;max-height:500px;box-shadow:0 4px 30px rgba(0,0,0,0.5)';

        p.innerHTML = '<h3 style="margin:0 0 10px;color:#00d4ff;font-size:16px">HubVision Collector</h3>' +
            '<div style="display:flex;justify-content:space-around;margin-bottom:15px">' +
                '<div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#00d4ff" id="hv-count">' + collectedPrompts.length + '</div><div style="font-size:11px;color:#888">Coletados</div></div>' +
                '<div style="text-align:center"><div style="font-size:24px;font-weight:bold;color:#00c853" id="hv-scanned">' + lastImages.length + '</div><div style="font-size:11px;color:#888">Na tela</div></div>' +
            '</div>' +
            '<div style="display:flex;gap:5px;margin-bottom:10px">' +
                '<button onclick="hvScan()" style="flex:1;background:#0087BD;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-size:12px">Atualizar</button>' +
                '<button onclick="hvSaveAll()" style="flex:1;background:#00c853;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-size:12px">Salvar Todos</button>' +
            '</div>' +
            '<div id="hv-list" style="max-height:250px;overflow-y:auto"></div>' +
            '<div style="display:flex;gap:5px;margin-top:10px">' +
                '<button onclick="hvExport()" style="flex:1;background:#0087BD;color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-size:12px">Exportar JSON</button>' +
                '<button onclick="hvClear()" style="flex:1;background:rgba(255,255,255,0.1);color:white;border:none;padding:8px;border-radius:6px;cursor:pointer;font-size:12px">Limpar</button>' +
            '</div>';

        document.body.appendChild(p);
    }

    // Escanear imagens
    window.hvScan = function() {
        scanImages();
        var s = document.getElementById('hv-scanned');
        if (s) s.textContent = lastImages.length;
        notify('Encontradas ' + lastImages.length + ' imagens');
    };

    // Iniciar
    setTimeout(function() {
        createPanel();
        scanImages();
        notify('HubVision pronto! Clique em "Atualizar" pra ver imagens');
    }, 2000);

    // Escanear automaticamente quando rolar
    window.addEventListener('scroll', function() {
        clearTimeout(window.hvScrollTimer);
        window.hvScrollTimer = setTimeout(scanImages, 1000);
    });

})();
