# -*- coding: utf-8 -*-
"""
Coletor enriquecido v2 — executado DENTRO do contexto browser-use (js/cdp pre-importados).
Captura pares imagem+prompt com metadados estruturais:
  - mid (id da mensagem), peer-id (canal), username (para link publico)
  - data, autor, link publico
  - imagem base64, resolucao, proporcao
  - texto original (prompt) preservado integralmente
  - classificacao estrutural EXATA/FORTE/PROVAVEL/INDETERMINADA

Uso:
    exec(open('P:/LandingPage-PromptHub/scripts/tg_collect2.py', encoding='utf-8').read())
    collect_channel(grupo, max_items=120, scroll_passes=60)
"""
import base64
import hashlib
import json
import os
import time

OUT_DIR = 'P:/LandingPage-PromptHub/PromptHub_coleta_v2'
MANIFEST_FILE = 'P:/LandingPage-PromptHub/.freebuff/coleta_v2_manifest.json'


def _scroll_up(retries=3):
    for _ in range(retries):
        try:
            js("(() => { const el = document.querySelector('.bubbles-scrollable'); if (el) el.focus(); return true; })()")
            cdp("Input.dispatchKeyEvent", type="keyDown", key="PageUp", code="PageUp", windowsVirtualKeyCode=33, nativeVirtualKeyCode=33)
            cdp("Input.dispatchKeyEvent", type="keyUp", key="PageUp", code="PageUp", windowsVirtualKeyCode=33, nativeVirtualKeyCode=33)
            return True
        except Exception:
            time.sleep(0.6)
    return False


def _chat_center():
    try:
        pos = js("(() => { const el = document.querySelector('.bubbles-scrollable'); if (!el) return '{}'; const r = el.getBoundingClientRect(); return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}); })()")
        p = json.loads(pos) if pos and pos.startswith('{') else {}
        if p.get('x'):
            return p['x'], p['y']
    except Exception:
        pass
    return 1000, 340


def scroll_to_top(steps=60, wait=0.45):
    x, y = _chat_center()
    for _ in range(steps):
        _wheel_up(x, y)
        time.sleep(wait)


def _wheel_up(x, y, times=4):
    try:
        cdp("Input.dispatchMouseEvent", type="mouseWheel", x=x, y=y, deltaX=0, deltaY=-600, deltaY_precise=-600)
    except Exception:
        pass


def current_channel_info():
    """Pega username (hash #@xxx), peer-title e header do chat aberto."""
    res = js("""
    (() => {
      const hash = location.hash || '';
      const header = document.querySelector('.chat-header .peer-title, .topbar .peer-title, .right-column .peer-title');
      const peerIdEl = document.querySelector('.album-item, [data-peer-id]');
      return JSON.stringify({
        hash: hash,
        peerTitle: header ? header.textContent.trim().slice(0,80) : '',
        peerId: peerIdEl ? peerIdEl.getAttribute('data-peer-id') : ''
      });
    })()
    """)
    try:
        return json.loads(res)
    except Exception:
        return {}


def capture_pairs():
    """Extrai bubbles: image (base64 jpeg), caption (prompt integral), mid, data, autor."""
    raw = js("""(() => {
      const out = [];
      const bubbles = Array.from(document.querySelectorAll('.bubble'));
      let lastDate = '';
      for (const b of bubbles) {
        if (b.classList.contains('service')) {
          const d = b.querySelector('.service-msg');
          if (d) lastDate = d.textContent.trim();
          continue;
        }
        const img = b.querySelector('img.media-photo');
        const txtEl = b.querySelector('.translatable-message');
        const txt = txtEl ? txtEl.textContent : '';
        const midEl = b.querySelector('[data-mid]');
        const mid = midEl ? midEl.getAttribute('data-mid') : '';
        const peerIdEl = b.querySelector('[data-peer-id]');
        const peerId = peerIdEl ? peerIdEl.getAttribute('data-peer-id') : '';
        const timeEl = b.querySelector('.time');
        const time = timeEl ? timeEl.textContent.trim() : '';
        const authorEl = b.querySelector('.sender-name, .from-name, .message-name');
        const author = authorEl ? authorEl.textContent.trim() : '';
        const isAlbum = b.classList.contains('is-album');
        const entry = {mid, peerId, time, date: lastDate, author, isAlbum, txt, hasImg: false, w: 0, h: 0};
        if (img && img.naturalWidth) {
          entry.hasImg = true;
          entry.w = img.naturalWidth;
          entry.h = img.naturalHeight;
          try {
            const c = document.createElement('canvas');
            c.width = img.naturalWidth; c.height = img.naturalHeight;
            c.getContext('2d').drawImage(img, 0, 0);
            entry.data = c.toDataURL('image/jpeg', 0.92);
          } catch (e) {
            entry.data = '';
            entry.err = String(e);
          }
        }
        out.push(entry);
      }
      return JSON.stringify(out);
    })()""")
    try:
        return json.loads(raw)
    except Exception:
        return []


def _extract_params(prompt):
    """Extrai parametros comuns do prompt: --ar, --v, --seed, --s, --no, sampler, steps, cfg."""
    params = {}
    if not prompt:
        return params
    import re
    m = re.search(r'--ar\s+([\\d:]+)', prompt)
    if m: params['ar'] = m.group(1)
    m = re.search(r'--v\s+([\\d.]+)', prompt)
    if m: params['version'] = m.group(1)
    m = re.search(r'--seed\s+(\\d+)', prompt)
    if m: params['seed'] = m.group(1)
    m = re.search(r'--s\s+(\\d+)', prompt)
    if m: params['stylize'] = m.group(1)
    m = re.search(r'--no\s+([\\w ,]+)', prompt)
    if m: params['negative'] = m.group(1).strip()
    m = re.search(r'Steps:\s*(\\d+)', prompt, re.I)
    if m: params['steps'] = m.group(1)
    m = re.search(r'CFG|CFG scale|Guidance:\s*(\\d+(?:\\.\\d+)?)', prompt, re.I)
    if m: params['cfg'] = m.group(1)
    m = re.search(r'\\b(SAMPLER|Sampler):\\s*([\\w-]+)', prompt, re.I)
    if m: params['sampler'] = m.group(2)
    m = re.search(r'(Midjourney|Nano ?Banana|Stable Diffusion|DALL-?E|Flux|Leonardo|Ideogram|Freepik|Gemini|GPT Image|Imagen)', prompt, re.I)
    if m: params['model'] = m.group(1)
    return params


def _classify(entry):
    """Classificacao estrutural da associacao prompt<->imagem."""
    has_img = entry.get('hasImg')
    txt = (entry.get('txt') or '').strip()
    is_album = entry.get('isAlbum')
    if has_img and txt:
        return 'EXATA'  # imagem com caption/prompt na mesma mensagem
    if has_img and not txt:
        return 'INDETERMINADA'  # imagem sem prompt na mesma bolha
    if not has_img and txt:
        return 'PROVAVEL'  # prompt solto, sem imagem na mesma bolha
    return 'INDETERMINADA'


def _categorize(prompt):
    """Categorias por keywords no prompt."""
    p = (prompt or '').lower()
    cats = []
    mapping = {
        'retrato': ['portrait', 'headshot', 'face', 'retrato'],
        'fotografia': ['photograph', 'photo of', 'fotografia', 'camera', '35mm', 'film'],
        'fantasia': ['fantasy', 'dragon', 'magic', 'wizard', 'elf', 'castelo', 'fairy'],
        'ficcao cientifica': ['sci-fi', 'sci fi', 'cyberpunk', 'robot', 'spaceship', 'alien', 'futuristic'],
        'arquitetura': ['architecture', 'building', 'interior', 'facade', 'house', 'casa', 'moderna'],
        'publicidade': ['advertisement', 'advertising', 'product photo', 'packaging', 'commercial'],
        'anime': ['anime', 'manga', 'japanese', 'cartoon'],
        '3d': ['3d render', '3d', 'pixar', 'blender', 'cgi', 'render'],
        'paisagem': ['landscape', 'mountain', 'ocean', 'sunset', 'nature', 'forest', 'cidade'],
        'arte conceitual': ['concept art', 'conceptart', 'matte painting', 'digital art', 'artstation']
    }
    for cat, keys in mapping.items():
        if any(k in p for k in keys):
            cats.append(cat)
    return cats[0] if cats else 'outros'


def collect_channel(grupo, max_items=120, scroll_passes=60, min_txt_len=20):
    """Coleta do canal atualmente aberto. Retorna resumo."""
    info = current_channel_info()
    username = (info.get('hash') or '').replace('#@', '')
    peer_id = info.get('peerId') or ''
    if not peer_id:
        # tenta pegar de qualquer bubble
        r = js("(() => { const el = document.querySelector('[data-peer-id]'); return el ? el.getAttribute('data-peer-id') : ''; })()")
        peer_id = r or peer_id
    title = info.get('peerTitle') or grupo

    os.makedirs(os.path.join(OUT_DIR, grupo), exist_ok=True)
    manifest = []
    if os.path.exists(MANIFEST_FILE):
        try:
            manifest = json.load(open(MANIFEST_FILE, encoding='utf-8'))
        except Exception:
            manifest = []
    seen = set()

    # scrool to top first (history), entao coleta subindo continua
    total_scroll = 0
    while len(seen) < max_items and total_scroll < scroll_passes:
        pairs = capture_pairs()
        for e in pairs:
            if not e.get('hasImg'):
                continue
            txt = (e.get('txt') or '').strip()
            if len(txt) < min_txt_len:
                continue
            h = hashlib.md5(txt.encode('utf-8', 'ignore')).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            cls = _classify(e)
            params = _extract_params(txt)
            b64 = e.get('data', '')
            if not b64:
                continue
            try:
                jpg_bytes = base64.b64decode(b64.split(',', 1)[1])
            except Exception:
                continue
            n = len(seen)
            base = 'pair_%03d' % n
            jpg_path = os.path.join(OUT_DIR, grupo, base + '.jpg')
            txt_path = os.path.join(OUT_DIR, grupo, base + '.txt')
            with open(jpg_path, 'wb') as f:
                f.write(jpg_bytes)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt)
            public_link = ('https://t.me/%s/%s' % (username, e['mid'])) if (username and e.get('mid')) else ''
            manifest.append({
                'grupo': grupo,
                'file': base,
                'titulo': txt.split('\n')[0][:80],
                'prompt_original': txt,
                'prompt_negativo': params.get('negative', ''),
                'modelo': params.get('model', ''),
                'seed': params.get('seed', ''),
                'sampler': params.get('sampler', ''),
                'steps': params.get('steps', ''),
                'cfg': params.get('cfg', ''),
                'resolucao': '%dx%d' % (e['w'], e['h']) if e.get('w') else '',
                'proporcao': ('%.3f' % (e['w'] / e['h'])) if e.get('w') and e.get('h') else '',
                'associacao': cls,
                'categoria': _categorize(txt),
                'hash_imagem': hashlib.md5(jpg_bytes).hexdigest()[:12],
                'link_publico': public_link,
                'canal': title,
                'username': username or '',
                'data': e.get('date', ''),
                'hora': e.get('time', ''),
                'autor': e.get('author', ''),
                'mid': e.get('mid', ''),
                'album': e.get('isAlbum', False),
            })
        if _scroll_up():
            total_scroll += 1
        time.sleep(0.5)

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    exata = sum(1 for m in manifest if m['associacao'] == 'EXATA')
    forte = sum(1 for m in manifest if m['associacao'] == 'FORTE')
    print('canal=%s username=%s peer=%s titulo=%s pares=%d (EXATA=%d FORTE=%d)' % (grupo, username, peer_id, title, len(manifest), exata, forte))
    return len(manifest)