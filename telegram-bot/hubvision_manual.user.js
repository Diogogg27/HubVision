// ==UserScript==
// @name         HubVision Manual Collector
// @match        https://web.telegram.org/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    var collectedPrompts = JSON.parse(localStorage.getItem('hv_prompts') || '[]');

    // Criar botao flutuante
    var fab = document.createElement('div');
    fab.innerHTML = '+';
    fab.style.cssText = 'position:fixed;bottom:100px;right:30px;width:60px;height:60px;background:linear-gradient(135deg,#0087BD,#00d4ff);color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;cursor:pointer;z-index:999999;box-shadow:0 4px 20px rgba(0,135,189,0.5);transition:transform 0.2s';
    fab.onmouseover = function() { fab.style.transform = 'scale(1.1)'; };
    fab.onmouseout = function() { fab.style.transform = 'scale(1)'; };
    document.body.appendChild(fab);

    // Modal
    var modal = document.createElement('div');
    modal.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:999998;align-items:center;justify-content:center';
    modal.innerHTML = '<div style="background:#1a1a2e;border-radius:16px;padding:30px;width:400px;max-width:90vw;color:white;font-family:sans-serif">' +
        '<h2 style="margin:0 0 20px;color:#00d4ff;text-align:center">Salvar Prompt</h2>' +
        '<textarea id="hv-text" placeholder="Cole o texto do prompt aqui..." style="width:100%;height:150px;background:#0d1117;color:white;border:1px solid #333;border-radius:8px;padding:12px;font-size:14px;resize:vertical;box-sizing:border-box"></textarea>' +
        '<input type="text" id="hv-url" placeholder="URL da imagem (opcional)" style="width:100%;margin-top:10px;padding:10px;background:#0d1117;color:white;border:1px solid #333;border-radius:8px;box-sizing:border-box">' +
        '<div style="display:flex;gap:10px;margin-top:20px">' +
            '<button id="hv-save" style="flex:1;background:#00c853;color:white;border:none;padding:12px;border-radius:8px;font-size:14px;cursor:pointer;font-weight:bold">Salvar</button>' +
            '<button id="hv-cancel" style="flex:1;background:rgba(255,255,255,0.1);color:white;border:none;padding:12px;border-radius:8px;font-size:14px;cursor:pointer">Cancelar</button>' +
        '</div>' +
        '<div style="margin-top:20px;border-top:1px solid #333;padding-top:15px">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">' +
                '<span style="color:#888;font-size:13px">Salvos: <strong id="hv-count" style="color:#00d4ff">' + collectedPrompts.length + '</strong></span>' +
                '<button id="hv-export" style="background:#0087BD;color:white;border:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer">Exportar JSON</button>' +
            '</div>' +
            '<button id="hv-clear" style="width:100%;background:rgba(255,68,68,0.2);color:#ff4444;border:none;padding:8px;border-radius:6px;font-size:12px;cursor:pointer">Limpar Tudo</button>' +
        '</div>';
    document.body.appendChild(modal);

    // Abrir modal
    fab.onclick = function() {
        modal.style.display = 'flex';
        document.getElementById('hv-text').value = '';
        document.getElementById('hv-url').value = '';
        document.getElementById('hv-text').focus();
    };

    // Fechar modal
    document.getElementById('hv-cancel').onclick = function() {
        modal.style.display = 'none';
    };

    modal.onclick = function(e) {
        if (e.target === modal) modal.style.display = 'none';
    };

    // Salvar
    document.getElementById('hv-save').onclick = function() {
        var text = document.getElementById('hv-text').value.trim();
        var url = document.getElementById('hv-url').value.trim();

        if (!text && !url) {
            alert('Cole o texto ou URL da imagem!');
            return;
        }

        var prompt = {
            id: Date.now(),
            text: text,
            image_url: url,
            source: 'Telegram Web',
            collected_at: new Date().toISOString()
        };

        collectedPrompts.push(prompt);
        localStorage.setItem('hv_prompts', JSON.stringify(collectedPrompts));

        document.getElementById('hv-count').textContent = collectedPrompts.length;

        modal.style.display = 'none';

        // Notificacao
        var n = document.createElement('div');
        n.style.cssText = 'position:fixed;top:20px;right:20px;background:#00c853;color:white;padding:15px 25px;border-radius:10px;z-index:999999;font-family:sans-serif;font-size:14px';
        n.textContent = 'Prompt salvo! (' + collectedPrompts.length + ' total)';
        document.body.appendChild(n);
        setTimeout(function() { n.remove(); }, 3000);
    };

    // Exportar
    document.getElementById('hv-export').onclick = function() {
        var d = JSON.stringify(collectedPrompts, null, 2);
        var b = new Blob([d], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = 'prompts_' + Date.now() + '.json';
        a.click();
    };

    // Limpar
    document.getElementById('hv-clear').onclick = function() {
        if (confirm('Limpar todos os prompts?')) {
            collectedPrompts = [];
            localStorage.removeItem('hv_prompts');
            document.getElementById('hv-count').textContent = '0';
        }
    };

    // Atalho: Ctrl+Shift+S abre o modal
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            fab.click();
        }
    });

    // Iniciar com dica
    setTimeout(function() {
        var tip = document.createElement('div');
        tip.style.cssText = 'position:fixed;bottom:170px;right:30px;background:#1a1a2e;color:white;padding:10px 15px;border-radius:8px;z-index:999997;font-family:sans-serif;font-size:12px;max-width:200px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,0.3)';
        tip.innerHTML = 'Clique no <strong>+</strong> ou pressione <strong>Ctrl+Shift+S</strong>';
        document.body.appendChild(tip);
        setTimeout(function() { tip.remove(); }, 5000);
    }, 2000);

})();
