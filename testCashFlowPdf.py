import camelot


tables=camelot.read_pdf('examples/FinancialDocuments/CashFlow.pdf', pages='1,2', flavor='stream')
print(tables)
#print(tables[0].parsing_report)
print(tables[1].df)