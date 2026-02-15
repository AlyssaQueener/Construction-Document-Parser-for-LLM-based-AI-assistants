import sys
from pathlib import Path

# Add project root to Python path
root = Path(__file__).resolve().parents[4]  # Go up 3 levels from voronoi_neighbors.py
sys.path.insert(0, str(root))

from src.plan2data.full_plan_ai import get_full_floorplan_metadata_with_ai
from src.plan2data.full_plan_ai import get_neighbouring_rooms_with_ai

path = "src/validation/Floorplan/neighboring rooms/Cluttered Floorplans/Cluttered 01.pdf"
#output = neighboring_rooms_voronoi(path)
print("starting full plan ai extraction")
#output, method, is_succesful, confidence = get_full_floorplan_metadata_with_ai(path)
output = get_neighbouring_rooms_with_ai(path)   
print(output)
print ("finished printing")