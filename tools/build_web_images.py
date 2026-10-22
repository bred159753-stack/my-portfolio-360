#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生網頁顯示用的壓縮圖（WebP），並把路徑與寬高寫回 portfolio_data.json。

用法（在專案根目錄 my-portfolio-360 執行）：
    pip install pillow
    python tools/build_web_images.py

每次新增或替換作品圖後再跑一次即可；已轉好且原圖沒變的會自動略過。

規則：
- 原圖不動，壓縮圖放在原圖旁的 web/ 資料夾，例如
  assets/angle_90_0/01/A/CG (1).png  ->  assets/angle_90_0/01/A/web/CG (1).webp
- 最長邊縮到 MAX_EDGE（較小的圖維持原尺寸），保留透明度。
- 每個圖片項目會寫入：
    "web":    壓縮圖路徑（網頁實際顯示用）
    "width" / "height": 壓縮圖尺寸（讓網頁不必先下載圖片就能排版）
  "src" 保持指向原圖，管理工具 code_artifact.html 不受影響。
- 影片項目不處理。
"""
import argparse
import json
import os
import sys

from PIL import Image

MAX_EDGE = 2560
QUALITY = 82
IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')
DATA_FILES = [
    'assets/angle_0_0/portfolio_data.json',
    'assets/angle_90_0/portfolio_data.json',
]


def web_path_for(src):
    d, name = os.path.split(src)
    base = os.path.splitext(name)[0]
    return f'{d}/web/{base}.webp'


def convert(root, out, src, stats):
    src_fs = os.path.join(root, src)
    if not os.path.isfile(src_fs):
        print(f'  [找不到原圖] {src}')
        return None

    web = web_path_for(src)
    web_out = os.path.join(out, web)
    if os.path.isfile(web_out) and os.path.getmtime(web_out) >= os.path.getmtime(src_fs):
        with Image.open(web_out) as im:
            stats['skipped'] += 1
            return web, im.width, im.height

    with Image.open(src_fs) as im:
        im.load()
        has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
        im = im.convert('RGBA' if has_alpha else 'RGB')
        if has_alpha and im.getchannel('A').getextrema() == (255, 255):
            im = im.convert('RGB')  # 實際沒有透明區域就不存 alpha，檔案更小
        scale = min(1.0, MAX_EDGE / max(im.width, im.height))
        if scale < 1.0:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        os.makedirs(os.path.dirname(web_out), exist_ok=True)
        im.save(web_out, 'WEBP', quality=QUALITY, method=6)
        stats['converted'] += 1
        stats['before'] += os.path.getsize(src_fs)
        stats['after'] += os.path.getsize(web_out)
        return web, im.width, im.height


def walk_items(node, fn):
    if isinstance(node, dict):
        if isinstance(node.get('src'), str):
            fn(node)
        for v in node.values():
            walk_items(v, fn)
    elif isinstance(node, list):
        for v in node:
            walk_items(v, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.', help='專案根目錄（讀取原圖與 json）')
    ap.add_argument('--out', default=None, help='輸出目錄（預設同 root）')
    args = ap.parse_args()
    root = args.root
    out = args.out or root
    stats = {'converted': 0, 'skipped': 0, 'before': 0, 'after': 0}

    for rel in DATA_FILES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        print(f'處理 {rel}')
        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        def handle(item):
            src = item['src']
            if item.get('type') == 'video' or not src.lower().endswith(IMG_EXT):
                return
            res = convert(root, out, src, stats)
            if res:
                item['web'], item['width'], item['height'] = res

        walk_items(data, handle)
        out_path = os.path.join(out, rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    mb = lambda b: b / 1024 / 1024
    print(f"完成：新轉 {stats['converted']} 張、略過 {stats['skipped']} 張")
    if stats['converted']:
        print(f"新轉的圖 {mb(stats['before']):.1f} MB -> {mb(stats['after']):.1f} MB")


if __name__ == '__main__':
    sys.exit(main())
