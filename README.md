# Waterloo faculty timeline

Open `index.html` directly in a modern browser. It is a standalone file: the SVG artwork, portraits, appointment data, styling, and JavaScript are embedded. No server, internet connection, installation, or adjacent files are needed to view it. The page's content security policy blocks external resources and network connections.

The initial view fits the entire Illustrator chart to the window width. Use zoom and scrolling to read details. Search highlights matching faculty; press Enter or select Next to zoom to a result. Previous cycles backward. Select a bar, or activate it with the keyboard, to see appointment and lighter-extension years. Fit / reset restores the initial view. Present means the source chart's February 2026 cutoff.

## Visual fidelity

The original PDF-compatible Illustrator file is converted directly to SVG. Gridlines, bar segments, colours, clipping, annotations, and portrait positions retain their original geometry. Font glyphs are vector outlines, so the original lettering does not depend on locally installed fonts. Chart lettering itself is not selectable text; names and dates in the search/selection layer are text and keyboard accessible. Portraits are downsampled to at most 384 pixels per side and opaque images use JPEG compression to keep the HTML reasonably small.

The embedded CSV data powers appointment details. Main service and lighter extensions remain separate. The original artwork is authoritative for the initial visual positions: editing the CSV and rebuilding updates appointment details, but does not reposition the original SVG bars. Editing the artwork requires updating the Illustrator source and rebuilding. A future data-driven renderer could derive bars from the CSV, with a corresponding loss of exact source geometry unless more precise dates are supplied.

## Rebuild

The viewer needs no dependencies. The optional build script requires Python with `pymupdf` and `pdfplumber` installed. From this directory:

```sh
python3 build_timeline.py
```

Inputs are the `.ai` file, `faculty.csv`, and `timeline.template.html`. Output is `index.html`. Temporary conversion artifacts go under the repository's `tmp/faculty-extraction/` directory. The Illustrator source and CSV are not modified.

For date interpretation and rounding, see `faculty-extraction-notes.md`.
