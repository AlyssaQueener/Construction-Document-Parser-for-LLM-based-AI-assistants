
import camelot
import json
import matplotlib
import pandas as pd
import json



def cam_extract(path,flav, pagenum):
    # Step 1: Read tables from the PDF
    tables = camelot.read_pdf(path, flavor=flav, pages=pagenum)
    print(f"Found {tables.n} tables")
    print(tables[0].parsing_report)
    return tables

# Sadly the results do not match the ouput maybe we have to write our own function to check for best output 
def cam_extract_accuracy(path, pagenum):
    flavours = ['stream', 'lattice','network','hybrid']
    best_accuracy = -1
    best_flavor = None
    best_tables = None

    for flavor in flavours: 
        tables = camelot.read_pdf(path, flavor=flavor, pages=pagenum)
        report = tables[0].parsing_report
        acc = report.get('accuracy', 0)
        print(flavor, acc)

        if acc > best_accuracy:
            best_accuracy = acc
            best_flavor = flavor
            best_tables = tables

    print(f"\n Best flavor: {best_flavor} with accuracy {best_accuracy}")
    return best_tables


#Step 2: Flatten tables into list of rows
def cam_stream_merge(tables):
    camelot.plot(tables[0], kind='grid').show()
    data = []
    for table in tables:
        df = table.df  #pandas DataFrame
        for _, row in df.iterrows():
            #iterate over the actual row values directly using enumerate(row)
            data.append({str(i): str(value).strip() for i, value in enumerate(row)})

    output = []
    current_row = None
    
    # for row in data:
    #     for key in row.keys:
    #         if row.get(key, "") and key!="1":  # New main row
    #             current_row = row.copy()
    #             output.append(current_row)
    #         elif row.get("1", "") and current_row:  # Continuation line
    #             current_row["1"] += " " + row["1"]
    for row in data:
        non_empty = {k: v.strip() for k, v in row.items() if v.strip()}

        # Only column "1" (second column) is filled
        if list(non_empty.keys()) == ["1"] and current_row:
            current_row["1"] += " " + non_empty["1"]
        else:
            current_row = row.copy()
            output.append(current_row)

    # Print cleaned result
    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Save the output list of dicts to a file
    # with open('output.json', 'w', encoding='utf-8') as f:
    #     json.dump(output, f, ensure_ascii=False, indent=2)
    return output

# def cam_dict(output):
#     tables = camelot.read_pdf(path, flavor='stream', pages=pages)
#     camelot.plot(tables[0], kind='grid').show()

#     # Merge all tables spanning multiple pages
#     full_df = pd.concat([t.df for t in tables], ignore_index=True)

#     # Convert merged DataFrame to list of row-dicts with index-keys
#     rows = []
#     for _, row in full_df.iterrows():
#         rows.append({str(i): str(row[i]).strip() for i in range(len(row))})

#     if not rows:
#         return []

#     # Use first row as header labels
#     headers = [rows[0][str(i)] for i in range(len(rows[0]))]

#     output = []
#     current = None
#     for row in rows[1:]:
#         if row.get("0", "").strip():  # New main row
#             current = {headers[i]: row.get(str(i), "") for i in range(len(headers))}
#             output.append(current)
#         else:
#             # Continuation line: append description field
#             if current:
#                 cont = row.get("1", "").strip()
#                 if cont:
#                     current[headers[1]] += " " + cont

#     # Save and print
#     print(json.dumps(output, indent=2, ensure_ascii=False))
#     with open('output.json', 'w', encoding='utf-8') as f:
#         json.dump(output, f, ensure_ascii=False, indent=2)

#     return output

################################



#Execution of the code 
if __name__ == "__main__":
    path = 'examples/FinancialDocuments/BOQ3.pdf'
    flav = 'hybrid'
    page_num = '1'
    tables_boq4 = cam_extract(path,flav,page_num)
    print(tables_boq4)
    tables_boq_processed = cam_stream_merge(tables_boq4)

