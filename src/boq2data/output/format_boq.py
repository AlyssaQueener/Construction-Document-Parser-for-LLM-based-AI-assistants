from typing import Any
from typing import Dict
from typing import OrderedDict as OrderedDictType

def format_boq(result: Dict[str, Any]):
    phases = init_phases(result)
    stuructured_result = structure_result(result, phases)
    print("Phases:")
    print(phases)
    
def init_phases(result: Dict[str, Any]):
    amount_phases = len(result.get("amounts"))
    phases = {}
    text = "Phase {count}"
    for i in range(0, amount_phases-1):
        phase_data = {
            "total amount": result["amounts"][i],
            "name": text.format(count=i + 1)
        }
        phases[i] = phase_data
    return phases

