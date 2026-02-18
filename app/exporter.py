import pandas as pd
from pathlib import Path

def export_results(rows: list) -> Path:
    df = pd.DataFrame(rows)
    output = Path("data/output/ats_results.xlsx")
    output.parent.mkdir(exist_ok=True)
    df.to_excel(output, index=False)
    return output
