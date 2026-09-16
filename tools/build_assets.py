#!/usr/bin/env python3
"""Фото для страниц услуг: исходник → webp в трёх размерах (2400 / 1400 / 800, суффиксы «», _m, _s) плюс jpg 1200 для og:image.
Использование: python3 tools/build_assets.py <исходник.jpg> <имя> [--crop L,T,R,B в долях 0..1]
Результат в assets/img/uslugi/<имя>.webp, <имя>_m.webp, <имя>_s.webp, <имя>_og.jpg"""
import sys, os
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'img', 'uslugi')

def build(src, name, crop=None):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    if crop:
        w, h = im.size; l, t, r, b = crop
        im = im.crop((int(w*l), int(h*t), int(w*r), int(h*b)))
    os.makedirs(OUT, exist_ok=True)
    for suf, width, q in (('', 2400, 80), ('_m', 1400, 80), ('_s', 800, 78)):
        c = im.copy(); c.thumbnail((width, width*2), Image.LANCZOS)
        c.save(os.path.join(OUT, f'{name}{suf}.webp'), 'WEBP', quality=q, method=6)
    og = im.copy(); og.thumbnail((1200, 1200)); og.save(os.path.join(OUT, f'{name}_og.jpg'), 'JPEG', quality=82, optimize=True)
    print(name, im.size, [os.path.getsize(os.path.join(OUT, f'{name}{s}.webp'))//1024 for s in ('', '_m', '_s')], 'KB')

if __name__ == '__main__':
    a = sys.argv[1:]
    crop = None
    if '--crop' in a:
        i = a.index('--crop'); crop = tuple(float(x) for x in a[i+1].split(',')); del a[i:i+2]
    build(a[0], a[1], crop)
