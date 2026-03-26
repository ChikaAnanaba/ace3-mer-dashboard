# ACE3 Programme Report Generator

Automated quarterly reporting system for the ACE3 programme.
HSCL · Kebbi, Sokoto & Zamfara · 37 Facilities

## Setup (one time)

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Browser opens automatically at http://localhost:8501

## Files in this folder

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `ace3_engine.py` | Core indicator engine (do not edit) |
| `prep_engine.py` | PrEP indicator extension |
| `assembler.py` | Combines engine results + PrEP + targets |
| `targets.py` | Targets loader + MER comparison rules |
| `excel_export.py` | Generates ACE3_Data_Report.xlsx |
| `html_reports.py` | Generates dashboard, narrative, talking points |
| `requirements.txt` | Python dependencies |

## Upload files each quarter

### Static (upload once, reused every quarter)
- **Targets** — facility-level annual targets (TARGET.csv or .xlsx)
- **VL Eligible** — patient-level VL eligibility flags (.xlsx)

### Quarterly (upload each period)
- RADET, HTS, PMTCT HTS, PMTCT Maternal, TB, AHD, PrEP

## Outputs (4 files downloaded per run)

1. `dashboard.html` — full visual dashboard, all charts, KPIs, state breakdowns
2. `narrative_report.html` — formal programme narrative, all numbers auto-written
3. `talking_points.html` — achievements, concerns, Q-on-Q, below-target, actions
4. `ACE3_Data_Report.xlsx` — single DATA_INPUT sheet, all indicators auto-populated

## Quarter modes

| Mode | Files needed | What you get |
|------|-------------|--------------|
| Q1 | Q1 files only | Q1 results vs annual targets |
| Q2 | Q2 files only | Q2 results vs annual targets |
| Semi-Annual | Q1 + Q2 files | Combined + Q1 vs Q2 comparison |
| Q3 | Q3 files | Q3 results (upload when available) |
| Annual | Q4 files | Full year (upload at Q4) |

## Notes

- No mention of any donor or funder in any output
- All outputs are self-contained HTML — open in any browser, print to PDF
- Data never leaves your computer — app runs fully locally
- Source: LAMIS+ / DHIS2
