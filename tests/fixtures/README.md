# Test fixtures

## PerformanceAnalyzerExportReport.pbix

A real Power BI Desktop file (151 KiB) used by
[test_pbix_fixture.py](../test_pbix_fixture.py) to run PBIX ingestion
end-to-end through PBIXRay with nothing mocked.

- Source: [microsoft/powerbi-desktop-samples](https://github.com/microsoft/powerbi-desktop-samples)
  (`Performance Analyzer/PerformanceAnalyzerExportReport.pbix` at commit
  `584fb00`), MIT licensed.
- Contents: 5 data tables (`EventEdges`, `EventTypes`, `Events`, `Metadata`,
  `RootActions`) from a Performance Analyzer export — per-visual timing and
  query events, including camelCase columns (`visualTitle`, `visualType`,
  `QueryText`) that exercise the fuzzy column-mapping fallback against
  real-world PBIX naming.
