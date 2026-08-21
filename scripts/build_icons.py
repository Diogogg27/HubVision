# -*- coding: utf-8 -*-
"""Gera favicon.ico + PNGs (16/32/64), apple-touch-icon e android-chrome a partir das marcas em icons/."""
import os
from PIL import Image

BASE = r"P:\LandingPage-PromptHub"
ICONS = os.path.join(BASE, "icons")

FAV_SRC = os.path.join(ICONS, "favicon", "Ativo 28ARQUIVO.png")      # 65x63
APPLE_SRC = os.path.join(ICONS, "apple", "Ativo 24ARQUIVO.png")      # 181x179
ANDROID_SRC = os.path.join(ICONS, "android", "Ativo 22ARQUIVO.png")  # 516x507


def square(img):
    """Centraliza a imagem num canvas quadrado transparente."""
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def save_png(img, path, size):
    img.resize((size, size), Image.LANCZOS).save(path, "PNG")


def main():
    fav = square(Image.open(FAV_SRC).convert("RGBA"))
    apple = square(Image.open(APPLE_SRC).convert("RGBA"))
    android = square(Image.open(ANDROID_SRC).convert("RGBA"))

    # favicon.ico multi-tamanho (16, 32, 48)
    ico_path = os.path.join(ICONS, "favicon", "favicon.ico")
    fav.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("criado:", ico_path)

    # PNGs referenciados no HTML / JSON-LD
    save_png(fav, os.path.join(ICONS, "favicon", "favicon_16x16.png"), 16)
    save_png(fav, os.path.join(ICONS, "favicon", "favicon_32x32.png"), 32)
    save_png(fav, os.path.join(ICONS, "favicon", "favicon_64x64.png"), 64)
    print("criados: favicon_16x16/32x32/64x64.png")

    # apple-touch-icon 180x180
    save_png(apple, os.path.join(ICONS, "apple", "apple-touch-icon-180x180.png"), 180)
    print("criado: apple-touch-icon-180x180.png")

    # android-chrome 192/512
    save_png(android, os.path.join(ICONS, "android", "android-chrome-192x192.png"), 192)
    save_png(android, os.path.join(ICONS, "android", "android-chrome-512x512.png"), 512)
    print("criados: android-chrome-192x192/512x512.png")


if __name__ == "__main__":
    main()
