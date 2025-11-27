import sys
from pathlib import Path

# Add project root to Python path
root = Path(__file__).resolve().parents[4]  # Go up 3 levels from voronoi_neighbors.py
sys.path.insert(0, str(root))

from src.plan2data.Voronoi_polygons_functions import neighboring_rooms_voronoi

path = "src/validation/Floorplan/neighboring rooms/Simple Floorplan/04_Simple.pdf"
output = neighboring_rooms_voronoi(path)
print(output)