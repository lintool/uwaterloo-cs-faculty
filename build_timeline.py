"""Build a self-contained SVG timeline. Requires pymupdf and pdfplumber."""
import base64
import collections
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pdfplumber
import pymupdf

ROOT = Path(__file__).resolve().parent
SOURCE = next(ROOT.glob('*.ai'))
SCRATCH = ROOT.parent / 'tmp' / 'faculty-extraction'
SCRATCH.mkdir(parents=True, exist_ok=True)
doc = pymupdf.open(SOURCE)
page = doc[0]
svg = page.get_svg_image(text_as_path=True)
# Keep original vectors and clipping, but resize portrait assets for browser use.
# Process the SVG images independently, preserving their coordinate systems.
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
root = ET.fromstring(svg)
href = '{http://www.w3.org/1999/xlink}href'
portraits = 0
for el in root.iter('{http://www.w3.org/2000/svg}image'):
    key = href if href in el.attrib else 'href'
    uri = el.get(key, '')
    if not uri.startswith('data:image/'):
        continue
    pix = pymupdf.Pixmap(base64.b64decode(uri.split(',', 1)[1]))
    if pix.colorspace and pix.colorspace.n != 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    while max(pix.width, pix.height) > 384:
        pix.shrink(1)
    # Retain transparency where needed; compress opaque photographic assets.
    fmt = 'png' if pix.alpha else 'jpeg'
    image_bytes = pix.tobytes(fmt, jpg_quality=86)
    el.set(key, f'data:image/{fmt};base64,' + base64.b64encode(image_bytes).decode())
    portraits += 1
root.set('id', 'artwork')
root.set('aria-hidden', 'true')
root.set('focusable', 'false')
root.set('width', '100%')
root.set('height', '100%')
svg = ET.tostring(root, encoding='unicode')
(SCRATCH / 'timeline-artwork.svg').write_text(svg)

with pdfplumber.open(SOURCE) as pdf:
    p = pdf.pages[0]
    grouped = collections.defaultdict(list)
    for c in p.chars:
        if not c['upright']:
            grouped[round(c['x0'], 1)].append(c)
    geometry = {}
    for x, chars in sorted(grouped.items()):
        name = ''.join(c['text'] for c in sorted(chars, key=lambda c: c['top']))
        name = ' '.join(name.split()).replace('WesG raham', 'Wes Graham')
        geometry[name] = {'x': x - 3, 'labelY': min(c['top'] for c in chars)}
    shapes = p.rects + p.curves
    for shape in shapes:
        if not 15.5 <= shape['width'] <= 18.2:
            continue
        name = min(geometry, key=lambda n: abs(geometry[n]['x'] + 9 - (shape['x0'] + shape['x1']) / 2))
        g = geometry[name]
        g['top'] = min(g.get('top', shape['top']), shape['top'])
        g['bottom'] = max(g.get('bottom', shape['bottom']), shape['bottom'])

faculty = {}
with (ROOT / 'faculty.csv').open(newline='', encoding='utf8') as f:
    for row in csv.DictReader(f):
        name = row.pop('name')
        person = faculty.setdefault(name, {'name': name, **geometry[name], 'intervals': []})
        person['intervals'].append({k: int(v) if v else None for k, v in row.items()})
assert len(faculty) == len(geometry) == 249
payload = {'width': page.rect.width, 'height': page.rect.height, 'faculty': list(faculty.values())}
template = (ROOT / 'timeline.template.html').read_text()
html = template.replace('<!--ARTWORK-->', svg).replace('/*FACULTY_DATA*/null', json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c'))
(ROOT / 'index.html').write_text(html, encoding='utf8')
print(f'Built index.html: {len(html.encode()) / 1024 / 1024:.2f} MB; {len(faculty)} faculty; {portraits} embedded portraits.')
