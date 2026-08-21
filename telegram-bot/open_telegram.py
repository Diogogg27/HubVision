import sys
sys.path.insert(0, r'P:\LandingPage-PromptHub\telegram-bot')

try:
    from browser_use import *
    
    # Navigate to Telegram Web
    new_tab("https://web.telegram.org")
    import time
    time.sleep(5)
    
    # Get page info
    info = page_info()
    print("Pagina carregada:", info)
    
except Exception as e:
    print(f"Erro: {e}")
    print("Browser Use nao disponivel. Use o metodo manual.")
