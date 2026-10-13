-- Stock Market SQL Analysis
-- SQLite version of the student guide tasks.

-- Task 1: How much history do we have?
SELECT COUNT(*) AS trading_days,
       MIN(date) AS first_day,
       MAX(date) AS last_day
FROM bajaj_auto;

-- Task 2: Eicher's five best closes
SELECT date, close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5;

-- Task 3: TCS, year by year
SELECT strftime('%Y', date) AS year,
       ROUND(AVG(close_price), 2) AS avg_close
FROM tcs
GROUP BY year
ORDER BY year;

-- Task 4: Find the holes
SELECT 'bajaj_auto' AS stock, date FROM bajaj_auto WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'eicher_motors' AS stock, date FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'hero_motocorp' AS stock, date FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'infosys' AS stock, date FROM infosys WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tcs' AS stock, date FROM tcs WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tvs_motors' AS stock, date FROM tvs_motors WHERE deliverable_qty IS NULL;

-- Task 5: Bajaj moving averages
DROP TABLE IF EXISTS bajaj1;
CREATE TABLE bajaj1 AS
WITH ranked AS (
    SELECT date,
           close_price,
           ROW_NUMBER() OVER (ORDER BY date) AS rn,
           AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg20_raw,
           AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS avg50_raw
    FROM bajaj_auto
)
SELECT date,
       close_price,
       CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END AS ma20,
       CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END AS ma50
FROM ranked;

-- Task 6: Master table
DROP TABLE IF EXISTS master_table;
CREATE TABLE master_table AS
SELECT b.date,
       b.close_price AS bajaj,
       t.close_price AS tcs,
       tv.close_price AS tvs,
       i.close_price AS infosys,
       e.close_price AS eicher,
       h.close_price AS hero
FROM bajaj_auto b
JOIN tcs t ON t.date = b.date
JOIN tvs_motors tv ON tv.date = b.date
JOIN infosys i ON i.date = b.date
JOIN eicher_motors e ON e.date = b.date
JOIN hero_motocorp h ON h.date = b.date;

-- Task 7: Golden cross signals
DROP TABLE IF EXISTS bajaj2;
CREATE TABLE bajaj2 AS
WITH t AS (
    SELECT date,
           close_price,
           ma20,
           ma50,
           LAG(ma20) OVER (ORDER BY date) AS prev_ma20,
           LAG(ma50) OVER (ORDER BY date) AS prev_ma50
    FROM bajaj1
)
SELECT date,
       close_price,
       CASE
           WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
           WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
           WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
           ELSE 'Hold'
       END AS signal
FROM t;

-- Task 8: How often did it trigger?
SELECT signal, COUNT(*) AS num_days
FROM bajaj2
GROUP BY signal
ORDER BY signal;

-- Task 9: Signal on a given day
SELECT signal
FROM bajaj2
WHERE date = '2018-06-21';

-- Task 10: All six stocks in one query
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys
    UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs
    UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
),
ma AS (
    SELECT stock,
           date,
           close_price,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) AS rn,
           AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg20_raw,
           AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS avg50_raw
    FROM prices
),
lagged AS (
    SELECT stock,
           date,
           close_price,
           CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END AS ma20,
           CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END AS ma50,
           LAG(CASE WHEN rn >= 20 THEN ROUND(avg20_raw, 2) END) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
           LAG(CASE WHEN rn >= 50 THEN ROUND(avg50_raw, 2) END) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT stock,
           date,
           close_price,
           CASE
               WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
               WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
               WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
               ELSE 'Hold'
           END AS signal
    FROM lagged
),
latest AS (
    SELECT stock, date, signal,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
    FROM sig
    WHERE signal <> 'Hold'
)
SELECT s.stock,
       SUM(CASE WHEN s.signal = 'Buy' THEN 1 ELSE 0 END) AS buys,
       SUM(CASE WHEN s.signal = 'Sell' THEN 1 ELSE 0 END) AS sells,
       MAX(CASE WHEN l.rn = 1 THEN l.date END) AS last_signal_date,
       MAX(CASE WHEN l.rn = 1 THEN l.signal END) AS last_signal
FROM sig s
LEFT JOIN latest l ON l.stock = s.stock AND l.rn = 1
GROUP BY s.stock
ORDER BY s.stock;

-- Task 11: Who went up?
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys
    UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs
    UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
),
ends AS (
    SELECT stock, MIN(date) AS first_date, MAX(date) AS last_date FROM prices GROUP BY stock
),
first_last AS (
    SELECT e.stock,
           MAX(CASE WHEN p.date = e.first_date THEN p.close_price END) AS first_close,
           MAX(CASE WHEN p.date = e.last_date THEN p.close_price END) AS last_close
    FROM ends e
    JOIN prices p ON p.stock = e.stock
    GROUP BY e.stock
)
SELECT stock,
       first_close,
       last_close,
       ROUND(100.0 * (last_close - first_close) / first_close, 1) AS pct_change
FROM first_last
ORDER BY pct_change DESC;

-- Task 12: The data trap
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL SELECT 'Infosys' AS stock, date, close_price FROM infosys
    UNION ALL SELECT 'TCS' AS stock, date, close_price FROM tcs
    UNION ALL SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
),
moves AS (
    SELECT stock,
           date,
           close_price,
           100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY date) - 1) AS pct_move
    FROM prices
),
ranked AS (
    SELECT stock, date, close_price, pct_move,
           ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn
    FROM moves
    WHERE pct_move IS NOT NULL
)
SELECT stock, date, close_price, ROUND(pct_move, 1) AS pct_move
FROM ranked
WHERE rn = 1
ORDER BY pct_move ASC;

-- Task 13: Fix the price cliff for TCS and Infosys
WITH adjusted AS (
    SELECT 'TCS' AS stock, date,
           CASE WHEN date < '2018-05-31' THEN close_price / 2 ELSE close_price END AS adj_close
    FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, date,
           CASE WHEN date < '2015-06-15' THEN close_price / 2 ELSE close_price END AS adj_close
    FROM infosys
),
with_bounds AS (
    SELECT stock, date, adj_close,
           MIN(date) OVER (PARTITION BY stock) AS first_date,
           MAX(date) OVER (PARTITION BY stock) AS last_date
    FROM adjusted
),
first_last AS (
    SELECT stock,
           MAX(CASE WHEN date = first_date THEN adj_close END) AS first_close,
           MAX(CASE WHEN date = last_date THEN adj_close END) AS last_close
    FROM with_bounds
    GROUP BY stock
)
SELECT stock,
       ROUND(100.0 * (last_close / first_close - 1), 1) AS adjusted_pct_change
FROM first_last
ORDER BY stock;
