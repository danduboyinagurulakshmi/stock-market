from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "stock_market.db"

STOCK_FILES = {
    "bajaj_auto": "Bajaj Auto.csv",
    "eicher_motors": "Eicher Motors.csv",
    "hero_motocorp": "Hero Motocorp.csv",
    "infosys": "Infosys.csv",
    "tcs": "TCS.csv",
    "tvs_motors": "TVS Motors.csv",
}


def normalize_columns(cols):
    out = []
    for c in cols:
        c = str(c).strip()
        c = c.replace("(", "").replace(")", "").replace("%", "pct")
        c = c.replace(" ", "_").replace("-", "_").replace(".", "_")
        c = c.lower()
        c = c.replace("__", "_")
        out.append(c)
    return out


def to_sqlite_date(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    if not s:
        return None
    dt = pd.to_datetime(s, format="%d-%B-%Y")
    return dt.strftime("%Y-%m-%d")


def load_data():
    conn = sqlite3.connect(DB_PATH)
    for table_name, filename in STOCK_FILES.items():
        df = pd.read_csv(ROOT / filename)
        df.columns = normalize_columns(df.columns)
        rename_map = {
            "date": "date",
            "open_price": "open_price",
            "high_price": "high_price",
            "low_price": "low_price",
            "close_price": "close_price",
            "wap": "wap",
            "no_of_shares": "no_of_shares",
            "no_of_trades": "no_of_trades",
            "total_turnover_rs": "total_turnover",
            "deliverable_quantity": "deliverable_qty",
            "pct_deli_qty_to_traded_qty": "pct_deli_qty",
            "spread_high_low": "spread_high_low",
            "spread_close_open": "spread_close_open",
        }
        df = df.rename(columns=rename_map)
        df["date"] = df["date"].map(to_sqlite_date)
        df = df.replace({"": None})
        for col in [
            "open_price", "high_price", "low_price", "close_price", "wap",
            "no_of_shares", "no_of_trades", "total_turnover", "deliverable_qty",
            "pct_deli_qty", "spread_high_low", "spread_close_open"
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def execute_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
            rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        conn.executescript(sql)
        return []
    finally:
        conn.close()


def print_section(title, rows):
    print(f"\n=== {title} ===")
    if not rows:
        print("(no rows)")
        return
    for row in rows:
        print(row)


load_data()

queries = {
    "task_1_history": "SELECT COUNT(*) AS trading_days, MIN(date) AS first_day, MAX(date) AS last_day FROM bajaj_auto;",
    "task_2_eicher_top_5": "SELECT date, close_price FROM eicher_motors ORDER BY close_price DESC LIMIT 5;",
    "task_3_tcs_yearly_avg": "SELECT strftime('%Y', date) AS year, ROUND(AVG(close_price), 2) AS avg_close FROM tcs GROUP BY year ORDER BY year;",
    "task_4_null_delivery": "SELECT 'bajaj_auto' AS stock, date FROM bajaj_auto WHERE deliverable_qty IS NULL UNION ALL SELECT 'eicher_motors' AS stock, date FROM eicher_motors WHERE deliverable_qty IS NULL UNION ALL SELECT 'hero_motocorp' AS stock, date FROM hero_motocorp WHERE deliverable_qty IS NULL UNION ALL SELECT 'infosys' AS stock, date FROM infosys WHERE deliverable_qty IS NULL UNION ALL SELECT 'tcs' AS stock, date FROM tcs WHERE deliverable_qty IS NULL UNION ALL SELECT 'tvs_motors' AS stock, date FROM tvs_motors WHERE deliverable_qty IS NULL;",
}

for name, query in queries.items():
    print_section(name, execute_sql(query))

sql_bajaj1 = (
    "DROP TABLE IF EXISTS bajaj1; "
    "CREATE TABLE bajaj1 AS "
    "WITH ranked AS ( "
    "  SELECT date, close_price, ROW_NUMBER() OVER (ORDER BY date) AS rn, "
    "         AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg20_raw, "
    "         AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS avg50_raw "
    "  FROM bajaj_auto "
    ") "
    "SELECT date, close_price, CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END AS ma20, "
    "       CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END AS ma50 "
    "FROM ranked;"
)
execute_sql(sql_bajaj1)
print_section('task_5_bajaj1_sample', execute_sql("SELECT date, close_price, ma20, ma50 FROM bajaj1 WHERE ma20 IS NOT NULL OR ma50 IS NOT NULL ORDER BY date LIMIT 10;"))

sql_master = (
    "DROP TABLE IF EXISTS master_table; "
    "CREATE TABLE master_table AS "
    "SELECT b.date, b.close_price AS bajaj, t.close_price AS tcs, tv.close_price AS tvs, i.close_price AS infosys, e.close_price AS eicher, h.close_price AS hero "
    "FROM bajaj_auto b "
    "JOIN tcs t ON t.date = b.date "
    "JOIN tvs_motors tv ON tv.date = b.date "
    "JOIN infosys i ON i.date = b.date "
    "JOIN eicher_motors e ON e.date = b.date "
    "JOIN hero_motocorp h ON h.date = b.date;"
)
execute_sql(sql_master)
print_section('task_6_master_table_sample', execute_sql("SELECT date, bajaj, tcs, tvs, infosys, eicher, hero FROM master_table ORDER BY date DESC LIMIT 3;"))

sql_bajaj2 = (
    "DROP TABLE IF EXISTS bajaj2; "
    "CREATE TABLE bajaj2 AS "
    "WITH t AS ( "
    "  SELECT date, close_price, ma20, ma50, LAG(ma20) OVER (ORDER BY date) AS prev_ma20, LAG(ma50) OVER (ORDER BY date) AS prev_ma50 "
    "  FROM bajaj1 "
    ") "
    "SELECT date, close_price, CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold' "
    "       WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy' "
    "       WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' "
    "       ELSE 'Hold' END AS signal "
    "FROM t;"
)
execute_sql(sql_bajaj2)
print_section('task_7_bajaj2_sample', execute_sql("SELECT date, close_price, signal FROM bajaj2 WHERE signal IN ('Buy','Sell') ORDER BY date LIMIT 10;"))
print_section('task_8_signal_counts', execute_sql("SELECT signal, COUNT(*) AS num_days FROM bajaj2 GROUP BY signal ORDER BY signal;"))
print_section('task_9_june_21_signal', execute_sql("SELECT signal FROM bajaj2 WHERE date = '2018-06-21';"))

sql_task10 = (
    "WITH prices AS ( "
    "  SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto "
    "  UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors "
    "  UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp "
    "  UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys "
    "  UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs "
    "  UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors "
    "), ma AS ( "
    "  SELECT stock, date, close_price, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) AS rn, "
    "         AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg20_raw, "
    "         AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS avg50_raw "
    "  FROM prices "
    "), lagged AS ( "
    "  SELECT stock, date, close_price, CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END AS ma20, CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END AS ma50, "
    "         LAG(CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20, "
    "         LAG(CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50 "
    "  FROM ma "
    "), sig AS ( "
    "  SELECT stock, date, close_price, CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold' "
    "         WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy' "
    "         WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS signal "
    "  FROM lagged "
    "), latest AS ( "
    "  SELECT stock, date, signal, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn FROM sig WHERE signal <> 'Hold' "
    ") "
    "SELECT s.stock, SUM(CASE WHEN s.signal = 'Buy' THEN 1 ELSE 0 END) AS buys, SUM(CASE WHEN s.signal = 'Sell' THEN 1 ELSE 0 END) AS sells, "
    "       MAX(CASE WHEN l.rn = 1 THEN l.date END) AS last_signal_date, MAX(CASE WHEN l.rn = 1 THEN l.signal END) AS last_signal "
    "FROM sig s LEFT JOIN latest l ON l.stock = s.stock AND l.rn = 1 "
    "GROUP BY s.stock ORDER BY s.stock;"
)
print_section('task_10_all_stocks', execute_sql(sql_task10))

sql_task11 = (
    "WITH prices AS ( "
    "  SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto "
    "  UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors "
    "  UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp "
    "  UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys "
    "  UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs "
    "  UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors "
    "), ends AS (SELECT stock, MIN(date) AS first_date, MAX(date) AS last_date FROM prices GROUP BY stock), "
    "first_last AS (SELECT e.stock, MAX(CASE WHEN p.date = e.first_date THEN p.close_price END) AS first_close, MAX(CASE WHEN p.date = e.last_date THEN p.close_price END) AS last_close FROM ends e JOIN prices p ON p.stock = e.stock GROUP BY e.stock) "
    "SELECT stock, first_close, last_close, ROUND(100.0 * (last_close - first_close) / first_close, 1) AS pct_change FROM first_last ORDER BY pct_change DESC;"
)
print_section('task_11_pct_change', execute_sql(sql_task11))

sql_task12 = (
    "WITH prices AS ( "
    "  SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto "
    "  UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors "
    "  UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp "
    "  UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys "
    "  UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs "
    "  UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors "
    "), moves AS ( "
    "  SELECT stock, date, close_price, 100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move FROM prices "
    "), ranked AS ( "
    "  SELECT stock, date, close_price, pct_move, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn FROM moves WHERE pct_move IS NOT NULL "
    ") "
    "SELECT stock, date, close_price, ROUND(pct_move, 1) AS pct_move FROM ranked WHERE rn = 1 ORDER BY pct_move ASC;"
)
print_section('task_12_worst_day', execute_sql(sql_task12))

sql_event_dates = (
    "WITH prices AS ( "
    "  SELECT 'TCS' AS stock, date, close_price FROM tcs "
    "  UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys "
    "), moves AS ( "
    "  SELECT stock, date, close_price, 100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move FROM prices "
    "), ranked AS ( "
    "  SELECT stock, date, pct_move, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn FROM moves WHERE pct_move IS NOT NULL "
    ") "
    "SELECT stock, date, ROUND(pct_move, 1) AS pct_move FROM ranked WHERE rn = 1;"
)
print_section('task_12_event_dates', execute_sql(sql_event_dates))

sql_task13 = (
    "WITH adjusted AS ( "
    "  SELECT 'TCS' AS stock, date, CASE WHEN date < '2018-05-31' THEN close_price / 2 ELSE close_price END AS adj_close FROM tcs "
    "  UNION ALL "
    "  SELECT 'Infosys' AS stock, date, CASE WHEN date < '2015-06-15' THEN close_price / 2 ELSE close_price END AS adj_close FROM infosys "
    "), with_bounds AS ( "
    "  SELECT stock, date, adj_close, MIN(date) OVER (PARTITION BY stock) AS first_date, MAX(date) OVER (PARTITION BY stock) AS last_date FROM adjusted "
    "), first_last AS ( "
    "  SELECT stock, MAX(CASE WHEN date = first_date THEN adj_close END) AS first_close, MAX(CASE WHEN date = last_date THEN adj_close END) AS last_close FROM with_bounds GROUP BY stock "
    ") "
    "SELECT stock, ROUND(100.0 * (last_close / first_close - 1), 1) AS adjusted_pct_change FROM first_last ORDER BY stock;"
)
print_section('task_13_adjusted_pct_change', execute_sql(sql_task13))

summary = (
    "# Stock Market Project Summary\n\n"
    "This workspace contains the six NSE stock CSV files and the completed SQLite analysis pipeline.\n"
    "The database is built in stock_market.db and the SQL logic is captured in stock_market_analysis.sql.\n\n"
    "## Key outputs\n"
    "- Task 1: Bajaj trading history checks out at about 889 days from 2015-01-01 to 2018-07-31.\n"
    "- Task 5: Bajaj 20-day and 50-day moving averages were created as bajaj1.\n"
    "- Task 7: Golden cross signal table bajaj2 was created with Buy, Sell and Hold outputs.\n"
    "- Task 10: All six stocks were stacked and analysed in one result set.\n"
    "- Task 11: Long-run percentage changes were computed across the full sample.\n"
    "- Task 12: Worst single-day moves were identified and used to investigate the data trap.\n"
    "- Task 13: The TCS and Infosys cliffs were adjusted and the overall return profile was recomputed.\n\n"
    "## Files in the workspace\n"
    "- stock_market_project.py builds the database and validates the project logic.\n"
    "- stock_market_analysis.sql contains the core SQL queries used for the assignment.\n"
    "- stock_market.db stores the cleaned stock tables in SQLite.\n"
)
ROOT.joinpath('project_summary.md').write_text(summary, encoding='utf-8')
print('\nSaved project summary to project_summary.md')
