import openpyxl
from openpyxl.utils import get_column_letter

wbf = openpyxl.load_workbook("reagen.xlsx", data_only=False)

for sh in ['LIS_Juli','LIS_Histori','Mapping_Test']:
    ws = wbf[sh]
    print(f"\n===== {sh} first 6 rows =====")
    for r in range(1,7):
        parts=[]
        for c in range(1, min(ws.max_column,36)+1):
            v = ws.cell(row=r,column=c).value
            if v is not None: parts.append(f"{get_column_letter(c)}{r}={repr(v)}")
        if parts: print(" | ".join(parts))

# Conditional formatting on Juli2026
ws = wbf['Juli2026']
print("\n===== Juli2026 Conditional Formatting rules =====")
try:
    for rng, rules in ws.conditional_formatting._cf_rules.items():
        print("RANGE:", rng.sqref)
        for rule in rules:
            print("   type:", rule.type, "operator:", rule.operator, "formula:", rule.formula, 
                  "dxfId:", rule.dxfId)
except Exception as e:
    print("cf err", e)

# Count reagen rows in Juli2026 (col C non-empty from row4)
cnt=0
names=[]
for r in range(4, 200):
    v = ws.cell(row=r, column=3).value
    if v: 
        cnt+=1; names.append(str(v))
    else:
        # stop after gap
        pass
print("\nJuli2026 reagen count:", cnt)
print("First 60 reagen:", names[:60])

# Aug reagen
ws2=wbf['Aug2026']
names2=[]
for r in range(4,200):
    v=ws2.cell(row=r,column=3).value
    if v: names2.append(str(v))
print("\nAug2026 reagen count:", len(names2))
