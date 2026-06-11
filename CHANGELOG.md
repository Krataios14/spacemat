# Changelog

## 0.2.0

* Bundled the complete NASA GSFC outgassing database: 13,582 ASTM E595
  test entries, fetched from the source and shipped as 384 KiB of package
  data. New `spacemat.outgassing` module with search, screen, and
  summarize. Refresh script in `scripts/fetch_nasa_outgassing.py`.
* Compliance reports crosscheck every non-metal against the full database
  and show the pass/fail split and TML/CVCM spread across all tests.
* New `spacemat.thermal` module: exact conductivity integrals, strut heat
  leak, contraction mismatch between joined materials.
* Thermal contraction curves for 304L, 301, Al-Li 2195, Inconel 718, PTFE,
  and G-10. New CONTRACTION and ELONGATION screening tokens.
* Command line interface: search, summary, screen, materials, show,
  report, info. CSV export on database commands.
* Comparison tables (`spacemat.compare`) and CSV/record export
  (`spacemat.export`).
* Dataset split into per-category files with duplicate-name detection.
* Data integrity tests, CI on Linux and Windows, py.typed marker.

## 0.1.0

* Initial release: curated materials schema, screening API with property
  tokens, Ashby-style trade plots, Markdown compliance reports.
