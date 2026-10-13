from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent
for f in sorted(root.glob('*.csv')):
    df = pd.read_csv(f)
    print(f.name)
    print(df.columns.tolist())
    print(df.head(2).to_dict(orient='records'))
    print()
