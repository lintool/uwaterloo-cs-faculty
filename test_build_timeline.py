"""Tests that CSV edits drive the actual SVG, without Illustrator or third-party packages."""
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NS = {'s': 'http://www.w3.org/2000/svg'}


class BuildTest(unittest.TestCase):
    def setUp(self):
        (ROOT/'tmp').mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=ROOT/'tmp')
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        for name in ['build_timeline.py', 'timeline.template.html']:
            shutil.copy(ROOT/name, self.work/name)

    def generate(self, rows):
        with (self.work/'faculty.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['name', 'start', 'end', 'color'])
            writer.writerows(rows)
        result = subprocess.run([sys.executable, '-S', str(self.work/'build_timeline.py')], capture_output=True, text=True)
        return result

    def output(self):
        text = (self.work/'index.html').read_text()
        svg = ET.fromstring(re.search(r'<svg id="artwork".*?</svg>',text,re.S).group())
        data = json.loads(re.search(r'<script id="faculty-data" type="application/json">(.*?)</script>',text,re.S).group(1))
        return text, svg, data

    def test_csv_edits_change_svg_without_illustrator(self):
        rows = [['A & <B>',2000,2010,'grey'], ['A & <B>',2010,'','yellow'], ['Other',2015,2016,'purple']]
        self.assertEqual(self.generate(rows).returncode,0)
        text, svg, data = self.output()
        bars = svg.findall('.//s:rect[@class="segment"]',NS)
        self.assertEqual(len(bars),3)
        self.assertAlmostEqual(float(bars[0].get('height')),288)
        self.assertEqual(bars[1].get('fill'),'#ffe681')
        self.assertEqual(svg.findall('s:g',NS)[0].get('data-faculty'),'A & <B>')
        self.assertIn('2 faculty',text)
        self.assertIn('3 colour segments',text)
        rows[0][2]=2005
        rows[1][1]=2005
        rows[1][3]='green'
        rows.append(['New person',2025,'','blue_grey'])
        self.assertEqual(self.generate(rows).returncode,0)
        text, svg, updated = self.output()
        bars = svg.findall('.//s:rect[@class="segment"]',NS)
        self.assertAlmostEqual(float(bars[0].get('height')),144)
        self.assertEqual(bars[1].get('fill'),'#b3d99f')
        self.assertEqual(len(bars),4)
        self.assertGreater(updated['width'],data['width'])
        self.assertEqual(updated['faculty'][-1]['name'],'New person')

    def test_gap_and_equal_year_are_preserved(self):
        self.assertEqual(self.generate([['X',2010,2017,'grey'],['X',2023,'','grey'],['Y',2026,2026,'purple']]).returncode,0)
        _, svg, _ = self.output()
        bars=svg.findall('.//s:rect[@class="segment"]',NS)
        self.assertGreater(float(bars[0].get('y')),float(bars[1].get('y'))+float(bars[1].get('height')))
        self.assertEqual(float(bars[2].get('height')),2)

    def test_invalid_input_rejected(self):
        for rows in ([['X',2000,1999,'grey']], [['X',2000,'','unknown']], [['X',2000,2010,'grey'],['X',2005,'','grey']]):
            with self.subTest(rows=rows):
                self.assertNotEqual(self.generate(rows).returncode,0)

    def test_real_data(self):
        with (ROOT/'faculty.csv').open() as stream:
            rows=list(csv.reader(stream))[1:]
        self.assertEqual(self.generate(rows).returncode,0)
        _, svg, data=self.output()
        self.assertEqual(len(svg.findall('.//s:rect[@class="segment"]',NS)),len(rows))
        self.assertEqual(len(data['faculty']),len({r[0] for r in rows}))

    def test_headshots_join_by_name_and_embed(self):
        asset = self.work/'assets'/'headshots'/'sample.jpg'
        asset.parent.mkdir(parents=True)
        shutil.copy(ROOT/'assets/headshots/donald-cowan-01.jpg',asset)
        with (self.work/'headshots.csv').open('w',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(['name','year','headshot','width','height'])
            writer.writerows([['A',2001,'assets/headshots/sample.jpg',28,40],['A',2010,'assets/headshots/sample.jpg',28,40]])
        self.assertEqual(self.generate([['B',1990,'','grey'],['A',2000,'','yellow']]).returncode,0)
        text,svg,data=self.output()
        groups=svg.findall('s:g',NS)
        self.assertEqual(len(groups[0].findall('s:image',NS)),0)
        images=groups[1].findall('s:image',NS)
        self.assertEqual(len(images),2)
        self.assertEqual(data['headshotCount'],2)
        self.assertTrue(images[0].get('{http://www.w3.org/1999/xlink}href').startswith('data:image/jpeg;base64,'))
        self.assertGreater(float(images[0].get('y')),float(images[1].get('y')))
        asset.unlink()
        self.assertNotEqual(self.generate([['A',2000,'','grey']]).returncode,0)

    def test_headshot_catalog(self):
        with (ROOT/'faculty.csv').open() as stream:
            names={r['name'] for r in csv.DictReader(stream)}
        with (ROOT/'headshots.csv').open() as stream:
            photos=list(csv.DictReader(stream))
        self.assertEqual(len(photos),285)
        self.assertEqual(len({p['name'] for p in photos}),180)
        self.assertTrue(all(p['name'] in names for p in photos))
        self.assertEqual(len({p['headshot'] for p in photos}),len(photos))
        self.assertTrue(all((ROOT/p['headshot']).is_file() for p in photos))

    def test_full_build_without_illustrator_matches_current_visualization(self):
        # Copy only the documented build inputs, not extraction tools or artwork.
        for name in ['faculty.csv', 'headshots.csv']:
            shutil.copy(ROOT/name,self.work/name)
        shutil.copytree(ROOT/'assets',self.work/'assets')
        self.assertFalse(list(self.work.glob('*.ai')))
        result = subprocess.run(
            [sys.executable,'-I','-S',str(self.work/'build_timeline.py')],
            cwd=self.work,capture_output=True,text=True,
        )
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.work/'index.html').read_bytes(),(ROOT/'index.html').read_bytes())
        _,svg,data=self.output()
        self.assertEqual(len(svg.findall('.//s:image',NS)),285)
        self.assertEqual(data['segmentCount'],300)


if __name__ == '__main__':
    unittest.main()
