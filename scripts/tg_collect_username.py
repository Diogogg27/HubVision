# -*- coding: utf-8 -*-
"""
Navegador+coletor por username. Executado no contexto browser-use.
Navega para cada #@username, espera carregar, rola historico e chama collect_channel.
"""
import json
import time

def open_channel(username, wait=10):
    """Abre o canal por username #@xxx e aguarda o header carregar."""
    url = 'https://web.telegram.org/k/#@' + username
    try:
        goto_url(url)
    except Exception as e:
        print('goto err', username, e)
        return False
    time.sleep(wait)
    res = js("""(() => {
      const h = document.querySelector('.chat-header .peer-title, .topbar .peer-title, .right-column .peer-title');
      return JSON.stringify({hash: location.hash, title: h ? h.textContent.trim().slice(0,60) : '', bubbles: document.querySelectorAll('.bubble').length});
    })()""")
    try:
        info = json.loads(res)
    except Exception:
        info = {}
    return info


def scroll_top(passes=40, wait=0.4):
    for i in range(passes):
        try:
            js("(() => { const el = document.querySelector('.bubbles-scrollable'); if (el) el.focus(); return true; })()")
            cdp("Input.dispatchKeyEvent", type="keyDown", key="PageUp", code="PageUp", windowsVirtualKeyCode=33, nativeVirtualKeyCode=33)
            cdp("Input.dispatchKeyEvent", type="keyUp", key="PageUp", code="PageUp", windowsVirtualKeyCode=33, nativeVirtualKeyCode=33)
        except Exception:
            pass
        time.sleep(wait)


def collect_username(username, grupo, max_items=200, scroll_passes=140, wait=10):
    info = open_channel(username, wait=wait)
    print('opened', username, json.dumps(info, ensure_ascii=False)[:160])
    if not info or (info.get('hash') or '').replace('#@', '') not in (username,):
        # ainda tenta: o hash pode vir de outro formato
        pass
    scroll_top(passes=scroll_passes, wait=0.35)
    exec(open('P:/LandingPage-PromptHub/scripts/tg_collect2.py', encoding='utf-8').read())
    return collect_channel(grupo, max_items=max_items, scroll_passes=scroll_passes)