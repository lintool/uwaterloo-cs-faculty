# Faculty timeline extraction

`faculty.csv` contains 300 visible colour segments for 249 faculty members. Rows follow the chart’s left-to-right faculty order, then chronological segment order within each faculty member.

Source: `2025 CS time line chart 50% -- increased canvas size (February 2026 update).ai`, embedded PDF chart. No external employment records were consulted.

- Columns: `name,start,end,color`.
- `color` is a lowercase colour name, with underscores between words. The mapping to the rendered RGB hex colours from the original PDF is retained below. These names describe appearance only, without assigning a role or employment status.
- Every visible colour change starts a new row. Yellow sections and lighter extensions are separate segments. The previous `extension_start` and `extension_end` columns have been replaced by segment rows.
- Overlapping vector bars are resolved using the original drawing order. Adjacent segments of the same colour are merged. This corrects the earlier lighter-extension boundary estimates for Wes Graham (1996, previously 1994) and John Brzozowski (1997, previously 1996).
- Portraits, red photo placeholders, gridlines, and pale decorative tails below the 1967 baseline are excluded. Portraits drawn over a bar do not split it.
- Start and end are approximate integer years, not verified appointment dates. The scale is 28.8 PDF points per year, with 1967 at y=53.008. Boundary positions within 0.10 years of an integer are snapped to that year; the first start for each faculty uses a 0.15-year tolerance. Other fractional positions use the calendar year containing the boundary. One shared boundary is converted consistently for both adjoining segments.
- A blank end means that segment reaches the chart’s 2026 cutoff, not necessarily the present day.
- A start equal to its end represents a segment shorter than the year-level resolution, not an empty source bar. This affects George Labahn’s yellow section, Mark Friedell’s appointment, and a narrow initial grey section for Nicholas Cercone.
- Michael Liu’s 2010–2017 and 2023–present bars remain separate, preserving the explicitly labelled break in service.
- Names retain the source spelling, including “Jeffery Shallit,” “Faheim Bacchus,” and “Keshav.” The extraction spacing artifact “WesG raham” is normalized to “Wes Graham.”

## Colours

| Hex | CSV colour name | Segments |
| --- | --- | ---: |
| #bcbec0 | `grey` | 221 |
| #dcddde | `light_grey` | 18 |
| #ffe681 | `yellow` | 17 |
| #d0b7cf | `purple` | 36 |
| #e7d9e9 | `light_purple` | 1 |
| #b1c0c9 | `blue_grey` | 6 |
| #b3d99f | `green` | 1 |

Validation: all 249 names matched to vector bars; 300 segments; seven colours; 129 open-ended segments; chronological, non-overlapping intervals within each faculty. The HTML viewer is generated from this segment CSV. Editing dates or colours and rerunning `python3 build_timeline.py` updates both the visible bars and their details; the generator does not read the Illustrator source.
