import openpyxl
from openpyxl.utils import get_column_letter

def ftext(v):
    # unwrap ArrayFormula
    try:
        from openpyxl.worksheet.formula import ArrayFormula
        if isinstance(v, ArrayFormula):
            return "ARR:" + str(v.text)
    except Exception:
        pass
    return v

wbf = openpyxl.load_workbook("reagen.xlsx", data_only=False)
wbv = openpyxl.load_workbook("reagen.xlsx", data_only=True)

print("========= JULI2026: full formula map for row 4 (Ca 15-3) =========")
ws = wbf['Juli2026']
for c in range(1, 67):
    v = ws.cell(row=4, column=c).value
    if v is not None:
        print(f"{get_column_letter(c)}4 = {ftext(v)}")

print("\n========= JULI2026 header rows 1,2,3 columns AM..BN (39..66) =========")
for r in [1,2,3]:
    for c in range(39, 67):
        v = ws.cell(row=r, column=c).value
        if v is not None:
            print(f"{get_column_letter(c)}{r} = {ftext(v)}")

print("\n========= JULI2026 row4 AT..BN extra cols formulas =========")
for c in range(46, 67):
    v = ws.cell(row=4, column=c).value
    if v is not None:
        print(f"{get_column_letter(c)}4 = {ftext(v)}")

print("\n========= AZ column meaning: check rows 4-14 col AZ(52), AS-AZ =========")
for r in range(3, 15):
    parts=[]
    for c in range(44, 60):
        v = ws.cell(row=r, column=c).value
        if v is not None:
            parts.append(f"{get_column_letter(c)}{r}={ftext(v)}")
    if parts: print(" | ".join(parts))
