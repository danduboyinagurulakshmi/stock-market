# Stock Market Analysis

SQLite analysis of six NSE stock price datasets, based on the accompanying student guide. The project includes the source CSVs, SQL queries, a populated SQLite database, and PDF/text reference materials.

## Run the analysis

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the analysis script from any working directory:

```bash
python stock_market_project.py
```

The script reads the CSV files beside itself and rebuilds `stock_market.db`. The SQL statements are also available in [stock_market_analysis.sql](stock_market_analysis.sql).

## Project contents

- `*.csv` — source data for Bajaj Auto, Eicher Motors, Hero Motocorp, Infosys, TCS, and TVS Motors.
- `stock_market_project.py` — loads the source data into SQLite and runs the analysis.
- `stock_market_analysis.sql` — SQL equivalents of the guide's analysis tasks.
- `stock_market.db` — generated SQLite database.
- `SQL_Stock_Market_Analysis_Student_Guide.pdf` and `guide_text.txt` — source guide and extracted text.
- `stock_market_summary.pdf` and `project_summary.md` — project results and summary.
- `extract_pdf.py`, `extract_pdf_all.py`, and `inspect_csvs.py` — helper scripts.
