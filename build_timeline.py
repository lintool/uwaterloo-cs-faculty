"""Build the standalone faculty timeline from CSV using only Python's standard library."""
import argparse
import base64
import csv
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLORS = {
    'grey': '#bcbec0', 'light_grey': '#dcddde', 'yellow': '#ffe681',
    'purple': '#d0b7cf', 'light_purple': '#e7d9e9',
    'blue_grey': '#b1c0c9', 'green': '#b3d99f',
}


def read_faculty(path, cutoff):
    faculty = {}
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['name', 'start', 'end', 'color']:
            raise ValueError('Expected CSV columns: name,start,end,color')
        for line, row in enumerate(reader, 2):
            name = row['name'].strip()
            try:
                start = float(row['start'])
                end = float(row['end']) if row['end'].strip() else None
            except (ValueError, AttributeError) as error:
                raise ValueError(f'Row {line}: invalid year') from error
            if not name or row['color'] not in COLORS:
                raise ValueError(f'Row {line}: missing name or unknown colour')
            stop = cutoff if end is None else end
            if not all(math.isfinite(v) for v in (start, stop)) or start > stop or stop > cutoff:
                raise ValueError(f'Row {line}: years must satisfy start <= end <= {cutoff:g}')
            segments = faculty.setdefault(name, [])
            if segments and (segments[-1]['end'] is None or segments[-1]['end'] > start):
                raise ValueError(f'Row {line}: overlapping or out-of-order segments for {name}')
            segments.append({'start': start, 'end': end, 'color': row['color']})
    if not faculty:
        raise ValueError('CSV contains no faculty segments')
    return faculty


def read_headshots(path, faculty):
    photos = {name: [] for name in faculty}
    if path is None:
        return photos
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['name', 'year', 'headshot', 'width', 'height']:
            raise ValueError('Expected headshot columns: name,year,headshot,width,height')
        for line, row in enumerate(reader, 2):
            if row['name'] not in faculty:
                raise ValueError(f'Headshots row {line}: unknown faculty {row["name"]}')
            year, width, height = (float(row[k]) for k in ('year', 'width', 'height'))
            if not all(math.isfinite(v) for v in (year, width, height)) or min(width,height) <= 0:
                raise ValueError(f'Headshots row {line}: invalid placement or dimensions')
            asset = path.parent/row['headshot']
            mime = {'.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png'}.get(asset.suffix.lower())
            if mime is None:
                raise ValueError(f'Headshots row {line}: expected JPEG or PNG asset')
            uri = f'data:{mime};base64,'+base64.b64encode(asset.read_bytes()).decode('ascii')
            photos[row['name']].append({'year':year,'width':width,'height':height,'asset':row['headshot'],'uri':uri})
    return photos


def make_chart(faculty, cutoff, photos):
    first = math.floor(min(s['start'] for segments in faculty.values() for s in segments))
    top, bottom, left, step, bar_width, year_scale = 70, 40, 340, 27, 18, 28.8
    all_photos = [photo for group in photos.values() for photo in group]
    top = max([top]+[(p['year']-cutoff)*year_scale+p['height']/2+12 for p in all_photos])
    bottom = max([bottom]+[(first-p['year'])*year_scale+p['height']/2+12 for p in all_photos])
    height = top + max(1, cutoff-first)*year_scale + bottom
    width = left + len(faculty)*step + 100
    y = lambda year: top + (cutoff-year)*year_scale
    svg = [f'<svg id="artwork" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width:g} {height:g}" width="100%" height="100%" role="img" aria-labelledby="chart-title chart-desc">',
           '<title id="chart-title">Waterloo faculty timeline</title>',
           '<desc id="chart-desc">Bars generated from faculty.csv. Each colour segment is a CSV row. Earlier years appear at the bottom. Faculty follow their first appearance in the CSV.</desc>',
           '<rect width="100%" height="100%" fill="white"/>']
    ticks = sorted({first, *range(math.ceil(first/5)*5, math.floor(cutoff/5)*5+1, 5)})
    for year in ticks:
        yy = y(year)
        svg.append(f'<path d="M 260 {yy:g} H {width-40:g}" stroke="#444" stroke-width="0.8"/>')
        for xx, anchor in ((252, 'end'), (width-35, 'start')):
            svg.append(f'<text x="{xx:g}" y="{yy+5:g}" text-anchor="{anchor}" font-family="Georgia,serif" font-size="16">{year}</text>')
    for year, lines in [(1967, ['Applied Analysis and', 'Computer Science']),
                        (1975, ['Computer Science']), (2002, ['School of', 'Computer Science']),
                        (2005, ['David R. Cheriton', 'School of', 'Computer Science'])]:
        if first <= year <= cutoff:
            for j, text in enumerate(reversed(lines)):
                svg.append(f'<text x="42" y="{y(year)-8-j*18:g}" font-family="Georgia,serif" font-size="17">{text}</text>')
    payload = {'width': width, 'height': height, 'firstYear': first, 'cutoff': cutoff,
               'segmentCount': sum(map(len, faculty.values())), 'headshotCount': len(all_photos), 'colors': COLORS, 'faculty': []}
    for i, (name, segments) in enumerate(faculty.items()):
        x = left+i*step
        svg.append(f'<g data-faculty="{html.escape(name, quote=True)}">')
        for seg in segments:
            yy = y(cutoff if seg['end'] is None else seg['end'])
            actual_height = y(seg['start'])-yy
            h = max(2, actual_height)
            if actual_height == 0:
                yy -= 1
            svg.append(f'<rect class="segment" x="{x:g}" y="{yy:g}" width="{bar_width}" height="{h:g}" fill="{COLORS[seg["color"]]}" data-start="{seg["start"]:g}" data-end="{seg["end"] if seg["end"] is not None else ""}" data-color="{seg["color"]}"/>')
        recent = segments[0]['start'] > cutoff-8
        label_end = y(segments[0]['start']) + (8 if recent else -7)
        nearby = [p for p in photos[name] if abs(p['year']-segments[0]['start']) < 3]
        if nearby:
            if recent:
                label_end = max(label_end,max(y(p['year'])+p['height']/2+6 for p in nearby))
            else:
                label_end = min(label_end,min(y(p['year'])-p['height']/2-6 for p in nearby))
        anchor = 'start' if recent else 'end'
        label_top = label_end if recent else max(0,label_end-len(name)*7)
        label_bottom = label_end+len(name)*7 if recent else label_end
        svg.append(f'<text transform="translate({x+13:g} {label_end:g}) rotate(90)" text-anchor="{anchor}" font-family="Georgia,serif" font-size="12" fill="#222">{html.escape(name)}</text>')
        for photo in photos[name]:
            svg.append(f'<image class="headshot" x="{x+bar_width/2-photo["width"]/2:g}" y="{y(photo["year"])-photo["height"]/2:g}" width="{photo["width"]:g}" height="{photo["height"]:g}" preserveAspectRatio="none" data-asset="{html.escape(photo["asset"],quote=True)}" xlink:href="{photo["uri"]}"><title>{html.escape(name)} headshot</title></image>')
        svg.append('</g>')
        payload['faculty'].append({'name': name, 'x': x-3,
            'top': min([label_top]+[y(cutoff if s['end'] is None else s['end']) for s in segments]+[y(p['year'])-p['height']/2 for p in photos[name]]),
            'bottom': max([y(segments[0]['start']),label_bottom]+[y(p['year'])+p['height']/2 for p in photos[name]]), 'labelY': label_top,
            'intervals': segments})
    svg.append('</svg>')
    return ''.join(svg), payload


def build(csv_path, template_path, output_path, cutoff=2026, headshots_path=None):
    if not math.isfinite(cutoff):
        raise ValueError('Cutoff must be a finite year')
    faculty = read_faculty(csv_path, cutoff)
    svg, data = make_chart(faculty, cutoff, read_headshots(headshots_path, faculty))
    template = template_path.read_text(encoding='utf8')
    replacements = {
        '<!--ARTWORK-->': svg,
        '/*FACULTY_DATA*/null': json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'),
        '{{FACULTY_COUNT}}': str(len(faculty)), '{{SEGMENT_COUNT}}': str(data['segmentCount']),
        '{{FIRST_YEAR}}': str(data['firstYear']), '{{CUTOFF}}': f'{cutoff:g}',
        '{{ASPECT_RATIO}}': f'{data["width"]}/{data["height"]}',
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    output_path.write_text(template, encoding='utf8')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT/'faculty.csv')
    parser.add_argument('--template', type=Path, default=ROOT/'timeline.template.html')
    parser.add_argument('--output', type=Path, default=ROOT/'index.html')
    parser.add_argument('--cutoff', type=float, default=2026, help='Year used for blank ends (default: 2026)')
    parser.add_argument('--headshots', type=Path, default=ROOT/'headshots.csv' if (ROOT/'headshots.csv').exists() else None, help='Optional headshot CSV (defaults to headshots.csv when present)')
    args = parser.parse_args()
    data = build(args.csv, args.template, args.output, args.cutoff, args.headshots)
    print(f'Built {args.output}: {len(data["faculty"])} faculty, {data["segmentCount"]} CSV segments.')
