from openpyxl import load_workbook

wb = load_workbook(filename='../data.xlsx', data_only=True)

ws = wb.get_sheet_by_name('data')

for row in ws['C4':'AU18']:
    print(list(map(lambda x: x.value, row)))
