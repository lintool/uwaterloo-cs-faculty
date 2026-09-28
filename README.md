# Waterloo faculty timeline

Open `index.html` directly in a modern browser. It is a standalone file containing the SVG chart, faculty data, styling, and JavaScript. No backend, internet connection, installation, or adjacent files are required to view it.

## Update the visualization

Edit `faculty.csv`, then run:

```sh
python3 build_timeline.py
```

Only Python's standard library is required. The generator reads `faculty.csv`, `headshots.csv`, the referenced headshot assets, and `timeline.template.html` and writes `index.html`. It does not read the Illustrator file or extracted chart artwork. Editing the CSV changes the actual chart geometry, labels, colours, search results, and segment details after rebuilding. The generated HTML embeds a snapshot of the CSV; it does not fetch files when opened.

CSV columns are `name,start,end,color`. Each row draws one segment. Faculty appear from left to right in order of their first CSV occurrence. Each faculty member's segments must be chronological and non-overlapping. Names may contain Unicode and quoted commas. Supported colour names and their hex values are documented in `faculty-extraction-notes.md` and defined in `COLORS` in the generator.

A blank end extends to the display cutoff, which defaults to 2026. To change it:

```sh
python3 build_timeline.py --cutoff 2027
```

The generator also supports `--csv`, `--headshots`, `--template`, and `--output`. Empty data, unknown colours, invalid dates, overlapping segments, and dates beyond the cutoff are rejected. Integer and decimal years are supported. Rows with equal start and end years appear as two-point ticks to retain their presence without inventing a full year of duration.

## Layout and interaction

The chart retains the original design's vertical bars, rotated names, five-year gridlines, colour palette, and historical department labels. Earlier years are at the bottom. All faculty geometry is calculated from the CSV using 28.8 points per year and equally spaced columns. The historical department labels are static contextual annotations.

The CSV contains approximate dates rather than precise source geometry, so this is a reconstruction rather than an exact reproduction of the Illustrator artwork. Portraits come from the separately extracted headshot assets. Labels use browser serif fonts, not embedded font outlines.

The page fills the browser window, with controls and explanations above the chart. The initial view fits the whole chart within both the available width and height, without page scrolling. Zoomed exploration scrolls inside the chart viewport. Use zoom and scrolling to read details. Search highlights matches; press Enter or choose Next to zoom to a result. Previous cycles backward. Select a faculty bar, or activate it with the keyboard, to see every segment's dates and colour. Fit / reset restores the initial view.

## Validation

```sh
python3 -B -m unittest test_build_timeline.py
node test_timeline_interactions.mjs
```

Tests build in isolated folders with no Illustrator file and with third-party Python packages disabled. They check that changes to CSV dates, colours, and faculty entries change the SVG, preserve gaps and same-year segments, and reject invalid input.

The Node interaction checks simulate DOM events to cover search, selection, zoom/reset, and resize behavior. They guard against pointer focus scrolling before a click and unwanted recentering when selection details appear. These are script-level regressions, not full browser layout tests.

The full-build regression copies only the generator, template, CSVs, and assets into an isolated folder and verifies byte-for-byte equality with the checked-in `index.html`. This checks that the same visual output can be reproduced without the Illustrator source or extraction tools. After changing inputs, regenerate `index.html` before running this test.

## Headshots

`assets/headshots/` contains all 285 portraits found in the Illustrator source, covering 180 faculty. Multiple historical portraits are retained. The other 69 faculty have no source portrait; coloured photo placeholders are not treated as portraits. Files are JPEG images converted to RGB at the original pixel dimensions, with quality 95.

`headshots.csv` contains `name,year,headshot,width,height`. The generator joins on the exact faculty name. Each row places one image, and multiple rows per name are supported. `headshot` is a path relative to this CSV. `year` is the approximate timeline position of the image centre, not a verified photography date. Width and height are display dimensions in chart points. Positions can extend slightly beyond the year axis; the chart margin expands to keep these images visible.

The build embeds all referenced images as data URLs, so `index.html` is still self-contained. Headshots are optional when no default CSV exists; a supplied CSV with an unknown faculty name, missing asset, or invalid dimensions fails the build rather than silently dropping an image.

`extract_headshots.py` is the one-time extraction utility and requires `pymupdf`, `pdfplumber`, and the original `.ai` source. It matches embedded images to the nearest labelled faculty column and writes the image assets and CSV. Ordinary visualization rebuilds never run this extraction and do not require these packages or the Illustrator file.
