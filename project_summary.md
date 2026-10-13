# Stock Market Project Summary

This workspace contains the six NSE stock CSV files and the completed SQLite analysis pipeline.
The database is built in stock_market.db and the SQL logic is captured in stock_market_analysis.sql.

## Key outputs
- Task 1: Bajaj trading history checks out at about 889 days from 2015-01-01 to 2018-07-31.
- Task 5: Bajaj 20-day and 50-day moving averages were created as bajaj1.
- Task 7: Golden cross signal table bajaj2 was created with Buy, Sell and Hold outputs.
- Task 10: All six stocks were stacked and analysed in one result set.
- Task 11: Long-run percentage changes were computed across the full sample.
- Task 12: Worst single-day moves were identified and used to investigate the data trap.
- Task 13: The TCS and Infosys cliffs were adjusted and the overall return profile was recomputed.

## Files in the workspace
- stock_market_project.py builds the database and validates the project logic.
- stock_market_analysis.sql contains the core SQL queries used for the assignment.
- stock_market.db stores the cleaned stock tables in SQLite.
