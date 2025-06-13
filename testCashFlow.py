import clevercsv
import json
import pandas as pd

def find_sub_dataframe_of_income(table_rows):
    start_of_income_rows=0
    start_of_row_with_timeseries=0
    column_position_of_timeseries_start=0
    end_of_income_rows=0
    for k, row in enumerate(table_rows):
        for e, element in enumerate(row):
            if element == 'Income' or element == 'INCOME' or element == 'income':
                start_of_income_rows = k
            if element == 'Jan':
                start_of_row_with_timeseries = k
                column_position_of_timeseries_start = e
                break
            if element == 'TOTAL' or element == 'total' or element=='Total':
                end_of_income_rows = k
    df_income = pd.DataFrame(table_rows[start_of_row_with_timeseries+1:end_of_income_rows], columns=table_rows[start_of_row_with_timeseries ])
    return df_income

rows = clevercsv.read_table('examples/FinancialDocuments/cashflow.csv')

print(type(rows))
cleaned_rows = []
for row in rows:
    for element in row:
        if element != '':
            cleaned_rows.append(row)
            break
print(cleaned_rows)
print(len(cleaned_rows))
print(len(cleaned_rows[0]))
df2 = pd.DataFrame(cleaned_rows[1:], columns=cleaned_rows[0])  
df_income= find_sub_dataframe_of_income(rows)
#print(df2.axes)
#df_income.to_json('testBoQ3.json','table')


#print(rows)
df = clevercsv.read_dataframe('examples/FinancialDocuments/cashflow.csv')
df_cleaned = df.dropna(axis=1, how='all').dropna(axis=0, how='all')

df_cleaned.to_json('testBoQ3.json','table')
#print("Data Frame: ")
#print(df2)

print(df.columns.size)
#a = clevercsv.read_dicts('examples/FinancialDocuments/cashflow.csv')
#print("Dicts: ")
#print(a)


    #cleaned_rows[1:], columns=cleaned_rows[0]



