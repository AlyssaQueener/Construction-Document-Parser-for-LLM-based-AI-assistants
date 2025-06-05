from typing import Any
from typing import Dict
from typing import OrderedDict as OrderedDictType

def format_boq(result: Dict[str, Any]):
    phases = init_phases(result)
    structured_result = structure_result(result, phases)
    print("Structured Result")
    print(structured_result)
    return structured_result
    
def init_phases(result: Dict[str, Any]):
    amount_phases = len(result.get("amounts"))
    phases = {}
    text = "Phase {count}"
    for i in range(0, amount_phases):
        phase_data = {
            "total amount": result["amounts"][i],
            "name": text.format(count=i + 1)
        }
        phases[i] = phase_data
    return phases


def structure_result(result: Dict[str, Any], phases: Dict[str, Any]):
    item_no = result.get("item_no")
    description = result.get("description")
    unit = result.get("unit")
    quantity = result.get("qty")
    rate = result.get("rate")
    amount = result.get("amount")
    k=0
    first_item = {
            "item_no": 1,
            "description" : description[0],
            "unit" : unit [0],
            "quantity": quantity[0],
            "rate": rate[0],
            "amount": amount[0]
        }
    for i in range(0, len(phases)):
        start = True
        items = {}
        for j in range(k, len(item_no)):
            item = {
                    "item_no": item_no[j],
                    "description" : description[j],
                    "unit" : unit [j],
                    "quantity": quantity[j],
                    "rate": rate[j],
                    "amount": amount[j]
                }
            if (item_no[j]=='1' and start == True):
                items[j] = first_item
            if (item_no[j] != '1'):
                items[j] = item
                start = False
            if (item_no[j]== '1' and start == False):
                first_item = item
                phases[i]["items"] = items
                k=j
                break
    return phases



