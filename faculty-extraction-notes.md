# Faculty timeline extraction

`faculty.csv` contains 249 faculty members and 250 appointment intervals, in the chart's left-to-right order. Michael Liu has two rows because the chart explicitly labels appointments in 2010–2017 and 2023–present.

Source: `2025 CS time line chart 50% -- increased canvas size (February 2026 update).ai`, embedded PDF chart. Names and bar geometry were extracted directly from its vector objects and checked against rendered portions of the chart. No external employment records were consulted.

- Columns: `name,start,end,extension_start,extension_end`. Dates are approximate integer years inferred from the chart, not verified appointment dates.
- A blank `end` means the main bar continues to the chart's present (February 2026), not necessarily the present day.
- `end` uses the visible main coloured bar. Lighter grey/purple extensions above the main bar are recorded separately in `extension_start` and `extension_end`, interpreted as later affiliation. The chart contains no text legend confirming that interpretation. Both extension fields blank means no later lighter extension is drawn. An extension start with a blank extension end means the extension reaches the chart's 2026 cutoff. Extension starts use the same year-rounding rule as main-bar ends so adjoining intervals agree.
- Yellow sections are retained as part of continuous service. Red photo placeholders are excluded from date measurements.
- The first cohort starts at 1967, the chart's baseline. Pale extensions below that baseline do not establish actual earlier appointment years.
- The vertical scale is 28.8 PDF points per year, with 1967 at y=53.008. Small drawing offsets within 0.15 years for starts or 0.10 years for ends are snapped to the nearest year. Other fractional positions use the calendar year containing the endpoint. Dates close to a year boundary should be treated as approximate; for example, the Santhoshini Velusamy bar starts near 2025.88 and is recorded as 2026.
- Original name spellings and abbreviations are preserved, including “Jeffery Shallit,” “Faheim Bacchus,” and “Keshav.” The text extraction artifact “WesG raham” is normalized to the visibly printed “Wes Graham.”

Validation: all 249 rotated faculty-name labels matched to bar shapes; all intervals have a start no later than their end; 114 intervals have blank ends; Michael Liu's two intervals match the explicit chart annotation.
