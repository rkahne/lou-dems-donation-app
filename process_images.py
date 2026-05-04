#!/usr/bin/env python3
"""Standardize candidate photos: square-crop, resize to 400x400, save to img/processed/."""

from PIL import Image, ImageOps
import os

SRC = 'img'
DST = 'img/processed'
SIZE = 400

os.makedirs(DST, exist_ok=True)


def process(src_path, dst_path):
    img = Image.open(src_path).convert('RGBA')

    # Crop to the bounding box of non-transparent pixels
    alpha = img.split()[3]
    bbox = alpha.getbbox()
    if bbox:
        img = img.crop(bbox)

    w, h = img.size

    # Square crop: center horizontally, bias 25% from top vertically (faces sit high)
    if w < h:
        x0 = 0
        y0 = int((h - w) * 0.25)
        img = img.crop((x0, y0, w, y0 + w))
    elif w > h:
        x0 = (w - h) // 2
        img = img.crop((x0, 0, x0 + h, h))

    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img.save(dst_path, 'PNG', optimize=True)


count = 0
for fname in sorted(os.listdir(SRC)):
    if not fname.lower().endswith('.png'):
        continue
    src = os.path.join(SRC, fname)
    dst = os.path.join(DST, fname)
    try:
        process(src, dst)
        src_size = os.path.getsize(src)
        dst_size = os.path.getsize(dst)
        print(f'  {fname}: {src_size//1024}KB -> {dst_size//1024}KB')
        count += 1
    except Exception as e:
        print(f'  ERROR {fname}: {e}')

print(f'\n{count} images written to {DST}/')
