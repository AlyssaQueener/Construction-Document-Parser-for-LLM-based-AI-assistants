import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import numpy as np

def draw_bounding_boxes(file_path, figsize=(10, 8)):
    """
    Draw bounding boxes from JSON file containing rooms with bbox coordinates.
    
    Args:
        file_path: Path to the JSON file containing room data
        figsize: Tuple for figure size (width, height)
    """
    
    # Read and parse JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Color palette for different room types
    colors = plt.cm.Set3(np.linspace(0, 1, 12))  # Use matplotlib colormap
    room_colors = {}
    color_idx = 0
    
    # Draw each room
    for room in data['rooms']:
        name = room['name']
        bbox = room['bbox']
        
        # Assign color to room type
        if name not in room_colors:
            room_colors[name] = colors[color_idx % len(colors)]
            color_idx += 1
        
        # Calculate rectangle dimensions
        x = bbox['x_min']
        y = bbox['y_min']
        width = bbox['x_max'] - bbox['x_min']
        height = bbox['y_max'] - bbox['y_min']
        
        # Create rectangle patch
        rect = patches.Rectangle(
            (x, y), width, height,
            linewidth=2,
            edgecolor=room_colors[name],
            facecolor=room_colors[name],
            alpha=0.3
        )
        
        # Add rectangle to plot
        ax.add_patch(rect)
        
        # Add room name as text
        ax.text(
            x + width/2, y + height/2,
            name,
            ha='center', va='center',
            fontsize=10,
            fontweight='bold',
            color='black'
        )
    
    # Set plot properties
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Room Bounding Boxes')
    ax.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = [patches.Patch(color=color, label=name) 
                      for name, color in room_colors.items()]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.show()

# Example usage:
if __name__ == "__main__":
    # Draw bounding boxes from a local JSON file
    draw_bounding_boxes('room_detection_results5.json')
    
    # Or with a different path
    # draw_bounding_boxes('/path/to/your/rooms.json')