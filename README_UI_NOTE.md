# UI reference and ownership

The address preparation screen follows the supplied 1536 × 1024 reference image.
Existing Streamlit components, data processing, API lookup, shared address storage,
and Excel output functions remain in use.

- ui_style.py: shared app chrome, sidebar, results and half-year screen styles.
- ui_compact.py: shared native layout/header/uploader styles for both work modes.
- ui_components.py: isolated filter and address-workflow HTML/CSS/JS.
- local_economy_report.py: injects the common theme once for both modes; historical mode1_style.py is no longer injected.
- mode1_prepare.py: maintains existing state keys and publishes changed filter values with a rerun so controls cannot repaint the preceding selection.

Default threshold remains 500,000 won. The existing nonlinear 0–10,000,000 slider
and unrestricted direct amount entry are retained; direct entry opens below the
four preset buttons. Counts use the existing dataset calculations.
Before upload, the workflow shows a waiting state with disabled action buttons.
The native sidebar still opens for half-year reporting and seat release.

## Validation (2026-09-04)

Python 3.12 / Streamlit 1.63.0 / Microsoft Edge (Playwright):

- Real upload of two synthetic XLSX files; 4 rows combined, duplicate businesses counted once in API targets and separately in unresolved contract totals.
- Preset amount, keyboard slider, manual/automatic region, and direct amount above 10 million synchronize across reruns.
- Native manual-editor trigger and Excel download; generated XLSX reopens.
- Help disclosure and sidebar navigation to half-year reporting.
- 1536 × 1024 desktop: three primary buttons share their top coordinate and 49 px height. No horizontal overflow at widths 1536, 1024, 768 and 390.
- AppTest with external API/shared storage mocked: API lookup once per business, previous-address bulk load, manual apply and duplicate-row propagation.
- No browser page errors or Streamlit exceptions in browser checks.

Real credentialed API responses and shared GitHub writes were not exercised.
Uploader styling targets Streamlit data-testid attributes; review its appearance
when upgrading Streamlit because native uploader markup can change.


## Half-year reporting / shared sidebar (2026-09-04)

- The sidebar remains visible, with shared blue navigation. On narrow screens it
  appears above the content instead of covering it or disappearing.
- The half-year screen uses the common theme and mode2_style.py for its input /
  generation conditions / three-step workflow / sheet previews / result summary.
- Existing single-XLSX upload and automatic generation remain supported. The
  generation button rebuilds using the current report information. No invented
  multi-file merge or requirement for four input sheets has been introduced.
- Four editable fields are in the main content, not the sidebar: year, half,
  period start and end. Institution and region come from the uploaded file.
- report_info.py infers the most frequent contract year and the majority half
  (January–June versus July–December, by record count). The explicit reporting
  period in the review title takes precedence over minimum/maximum contract dates.
  January–July can therefore remain a first-half report ending July 31.
- Ties, missing dates and multiple years require user confirmation. An inverted
  period prevents download. A new file resets only the report-specific defaults;
  edits persist across regeneration and menu navigation.
- Edited information changes the four A1 report headings and exported filename.
  It never filters records or changes classifications, amounts or aggregation.
- Existing excel_reports.py, core_logic.py, address_api.py, manual_address_store.py,
  mode1_prepare.py and mode1_address.py are unchanged in this update.

Validation: `python -m unittest discover -s tests -v` (3 tests). A real generated
4-sheet workbook was compared cell-by-cell before/after report-label changes:
non-title values, styles and merged ranges were preserved. AppTest verified
editing/regeneration/navigation/invalid periods/reset. Browser tests verified
real upload, title/filename synchronization, date edits, generation, download,
review detail, matching 49px buttons and no horizontal overflow at widths 1536,
1024, 768 and 390. Downloaded XLSX files were reopened and all four titles checked.
