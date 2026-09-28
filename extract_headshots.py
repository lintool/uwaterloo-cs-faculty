"""One-time asset extraction from Illustrator; requires pymupdf and pdfplumber.

The visualization generator does not use this script or the Illustrator source.
"""
import collections
import csv
import re
import unicodedata
from pathlib import Path

import pdfplumber
import pymupdf

ROOT = Path(__file__).resolve().parent


def extract():
    source = next(ROOT.glob('*.ai'))
    with pdfplumber.open(source) as pdf:
        grouped = collections.defaultdict(list)
        for char in pdf.pages[0].chars:
            if not char['upright']:
                grouped[round(char['x0'], 1)].append(char)
        labels = {}
        for x, chars in sorted(grouped.items()):
            name = ' '.join(''.join(c['text'] for c in sorted(chars, key=lambda c: c['top'])).split())
            labels[name.replace('WesG raham', 'Wes Graham')] = x+6
    doc = pymupdf.open(source)
    page = doc[0]
    photos = collections.defaultdict(list)
    for info in page.get_image_info(xrefs=True):
        rect = pymupdf.Rect(info['bbox'])
        center = (rect.x0+rect.x1)/2
        name = min(labels, key=lambda n: abs(labels[n]-center))
        if abs(labels[name]-center) > 5:
            raise ValueError(f'Ambiguous image at {rect}')
        year = 1967 + (page.rect.height-(rect.y0+rect.y1)/2-53.008)/28.8
        photos[name].append((year, rect, info['xref']))
    assets = ROOT/'assets'/'headshots'
    assets.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in labels:
        slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', name).encode('ascii','ignore').decode().lower()).strip('-')
        for number, (year, rect, xref) in enumerate(sorted(photos[name]), 1):
            path = assets/f'{slug}-{number:02d}.jpg'
            pix = pymupdf.Pixmap(doc, xref)
            if pix.colorspace and pix.colorspace.n != 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:
                pix = pymupdf.Pixmap(pix, 0)
            path.write_bytes(pix.tobytes('jpeg', jpg_quality=95))
            rows.append([name, f'{year:.4f}', path.relative_to(ROOT).as_posix(), f'{rect.width:.3f}', f'{rect.height:.3f}'])
    with (ROOT/'headshots.csv').open('w', newline='', encoding='utf8') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['name','year','headshot','width','height'])
        writer.writerows(rows)
    print(f'Extracted {len(rows)} headshots for {sum(bool(v) for v in photos.values())} faculty.')


if __name__ == '__main__':
    extract()
