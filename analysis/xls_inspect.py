import openpyxl
from openpyxl.utils import get_column_letter

wb = openpyxl.load_workbook("reagen.xlsx", data_only=False)
print("=== SHEET NAMES ===")
for i, s in enumerate(wb.sheetnames):
    ws = wb[s]
    print(f"{i}: '{s}'  dims={ws.dimensions}  max_row={ws.max_row} max_col={ws.max_column}")

print("\n\n=== PER SHEET OVERVIEW (first ~12 rows, all cols) ===")
for s in wb.sheetnames:
    ws = wb[s]
    print(f"\n\n############## SHEET: '{s}' (rows={ws.max_row}, cols={ws.max_column}) ##############")
    maxr = min(ws.max_row, 14)
    maxc = min(ws.max_column, 45)
    for r in range(1, maxr+1):
        rowvals = []
        for c in range(1, maxc+1):
            cell = ws.cell(row=r, column=c)
            v = cell.value
            if v is not None:
                rowvals.append(f"{get_column_letter(c)}{r}={repr(v)}")
        if rowvals:
            print(" | ".join(rowvals))
