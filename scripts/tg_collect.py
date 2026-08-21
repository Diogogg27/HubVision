# -*- coding: utf-8 -*-
"""
Coletor do Telegram Web — executado DENTRO do contexto browser-use (js/new_tab pre-importados).
Uso (via browser-use):
    exec(open('P:/LandingPage-PromptHub/scripts/tg_collect.py', encoding='utf-8').read())
    collect_group('rtm', 'https://web.telegram.org/k/', '#-123456789', max_items=90)
"""
import base64
import hashlib
import json
import os
import time

OUT_DIR = 'P:/LandingPage-PromptHub/PromptHub_coleta_fresh2'
INDEX_FILE = 'P:/LandingPage-PromptHub/.freebuff/tg_index.json'


def _load_index():
    if os.path.exists(INDEX_FILE):
        try:
            return json.load(open(INDEX_FILE, encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _save_index(idx):
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False)


def current_title():
    return js("document.title")


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
        import json as _j
        p = _j.loads(pos) if pos and pos.startswith('{') else {}
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


def capture_bubbles():
    """Retorna lista de {data(jpeg base64), txt} das fotos nos bubbles atuais."""
    raw = js("""(() => {
      const out = [];
      document.querySelectorAll('.bubble').forEach((b) => {
        const img = b.querySelector('img.media-photo');
        if (!img || !img.naturalWidth) return;
        const txtEl = b.querySelector('.translatable-message');
        const txt = txtEl ? txtEl.textContent.trim() : '';
        try {
          const c = document.createElement('canvas');
          c.width = img.naturalWidth; c.height = img.naturalHeight;
          c.getContext('2d').drawImage(img, 0, 0);
          out.push({data: c.toDataURL('image/jpeg', 0.92), txt: txt});
        } catch (e) {
          out.push({data: '', txt: txt, err: String(e)});
        }
      });
      return JSON.stringify(out);
    })()""")
    try:
        return json.loads(raw)
    except Exception:
        return []


def collect_group(grupo, base_url, chat_hash, max_items=90, min_dim=600, scroll_passes=45):
    """Abre o chat em aba nova, rola o historico e salva pares jpg+txt unicos."""
    os.makedirs(os.path.join(OUT_DIR, grupo), exist_ok=True)
    idx = _load_index()
    key = 'coleta2/' + grupo
    seen = set(idx.get(key, []))
    saved = 0

    url = base_url + chat_hash if not chat_hash.startswith('#') else base_url + chat_hash
    try:
        new_tab(url)
    except Exception as e:
        print('new_tab err:', e)
        return 0
    time.sleep(6)

    # garante que o chat abriu (titulo com hash ou pagina de chat)
    try:
        ensure_real_tab()
    except Exception:
        pass
    time.sleep(2)

    total_scroll = 0
    while len(seen) < max_items and total_scroll < scroll_passes:
        items = capture_bubbles()
        for it in items:
            if not it.get('data') or not it.get('txt'):
                continue
            txt = it['txt']
            if len(txt) < 15:
                continue
            h = hashlib.md5(txt.encode('utf-8', 'ignore')).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            try:
                b64 = it['data'].split(',', 1)[1]
                jpg_bytes = base64.b64decode(b64)
            except Exception:
                continue
            n = len(seen)
            base = 'prompt_%03d' % n
            with open(os.path.join(OUT_DIR, grupo, base + '.jpg'), 'wb') as f:
                f.write(jpg_bytes)
            with open(os.path.join(OUT_DIR, grupo, base + '.txt'), 'w', encoding='utf-8') as f:
                f.write(txt)
            saved += 1
        if _scroll_up():
            total_scroll += 1
        time.sleep(0.5)

    idx[key] = sorted(seen)
    _save_index(idx)
    print('grupo %s: novos=%d (total no grupo=%d)' % (grupo, saved, len(seen)))
    return saved
