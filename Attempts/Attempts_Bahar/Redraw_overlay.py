import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import numpy as np

def draw_bounding_boxes(rooms_file_path, doors_file_path=None, figsize=(10, 8)):
    """
    Draw bounding boxes from JSON files containing rooms and doors with bbox coordinates.
    
    Args:
        rooms_file_path: Path to the JSON file containing room data
        doors_file_path: Path to the JSON file containing door data (optional)
        figsize: Tuple for figure size (width, height)
    """
    
    # Read and parse rooms JSON file
    with open(rooms_file_path, 'r') as f:
        rooms_data = json.load(f)
    
    # Read and parse doors JSON file if provided
    doors_data = None
    if doors_file_path:
        try:
            with open(doors_file_path, 'r') as f:
                doors_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Door file {doors_file_path} not found. Drawing only rooms.")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Color palette for different room types
    room_colors = plt.cm.Set3(np.linspace(0, 1, 12))  # Use matplotlib colormap
    room_color_map = {}
    color_idx = 0
    
    # Draw each room
    for room in rooms_data['rooms']:
        name = room['name']
        bbox = room['bbox']
        
        # Assign color to room type
        if name not in room_color_map:
            room_color_map[name] = room_colors[color_idx % len(room_colors)]
            color_idx += 1
        
        # Calculate rectangle dimensions
        x = bbox['x_min']
        y = bbox['y_min']
        width = bbox['x_max'] - bbox['x_min']
        height = bbox['y_max'] - bbox['y_min']
        
        # Create rectangle patch for room
        rect = patches.Rectangle(
            (x, y), width, height,
            linewidth=2,
            edgecolor=room_color_map[name],
            facecolor=room_color_map[name],
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
    
    # Draw doors if door data is provided
    if doors_data and 'doors' in doors_data:
        door_color = 'red'  # Fixed color for all doors
        
        for door in doors_data['doors']:
            bbox = door['bbox']
            template = door.get('template', 'door')
            
            # Calculate rectangle dimensions
            x = bbox['x_min']
            y = bbox['y_min']
            width = bbox['x_max'] - bbox['x_min']
            height = bbox['y_max'] - bbox['y_min']
            
            # Create rectangle patch for door
            door_rect = patches.Rectangle(
                (x, y), width, height,
                linewidth=3,
                edgecolor=door_color,
                facecolor=door_color,
                alpha=0.7
            )
            
            # Add rectangle to plot
            ax.add_patch(door_rect)
            
            # Add door label (optional, might be too small)
            if width > 0.05 and height > 0.05:  # Only add text if door is large enough
                ax.text(
                    x + width/2, y + height/2,
                    'D',
                    ha='center', va='center',
                    fontsize=8,
                    fontweight='bold',
                    color='white'
                )
    
    # Set plot properties
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Room and Door Bounding Boxes')
    ax.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = [patches.Patch(color=color, label=name) 
                      for name, color in room_color_map.items()]
    
    # Add door legend if doors were drawn
    if doors_data and 'doors' in doors_data:
        legend_elements.append(patches.Patch(color='red', label='Doors'))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.show()

def draw_with_image_overlay(rooms_file_path, doors_file_path=None, image_path=None, figsize=(12, 10)):
    """
    Draw bounding boxes with optional floor plan image overlay.
    
    Args:
        rooms_file_path: Path to the JSON file containing room data
        doors_file_path: Path to the JSON file containing door data (optional)
        image_path: Path to the floor plan image (optional)
        figsize: Tuple for figure size (width, height)
    """
    
    # Read and parse rooms JSON file
    with open(rooms_file_path, 'r') as f:
        rooms_data = json.load(f)
    
    # Read and parse doors JSON file if provided
    doors_data = None
    if doors_file_path:
        try:
            with open(doors_file_path, 'r') as f:
                doors_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Door file {doors_file_path} not found. Drawing only rooms.")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Load and display image if provided
    if image_path:
        import matplotlib.image as mpimg
        try:
            img = mpimg.imread(image_path)
            ax.imshow(img, extent=[0, 1, 0, 1], alpha=0.5)
        except FileNotFoundError:
            print(f"Warning: Image file {image_path} not found. Drawing without image overlay.")
    
    # Color palette for different room types
    room_colors = plt.cm.Set3(np.linspace(0, 1, 12))
    room_color_map = {}
    color_idx = 0
    
    # Draw each room
    for room in rooms_data['rooms']:
        name = room['name']
        bbox = room['bbox']
        
        # Assign color to room type
        if name not in room_color_map:
            room_color_map[name] = room_colors[color_idx % len(room_colors)]
            color_idx += 1
        
        # Calculate rectangle dimensions
        x = bbox['x_min']
        y = bbox['y_min']
        width = bbox['x_max'] - bbox['x_min']
        height = bbox['y_max'] - bbox['y_min']
        
        # Create rectangle patch for room
        rect = patches.Rectangle(
            (x, y), width, height,
            linewidth=2,
            edgecolor=room_color_map[name],
            facecolor='none',  # Transparent fill when overlaying on image
            alpha=0.8
        )
        
        # Add rectangle to plot
        ax.add_patch(rect)
        
        # Add room name as text with background
        ax.text(
            x + width/2, y + height/2,
            name,
            ha='center', va='center',
            fontsize=10,
            fontweight='bold',
            color='black',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )
    
    # Draw doors if door data is provided
    if doors_data and 'doors' in doors_data:
        door_color = 'red'
        
        for door in doors_data['doors']:
            bbox = door['bbox']
            
            # Calculate rectangle dimensions
            x = bbox['x_min']
            y = bbox['y_min']
            width = bbox['x_max'] - bbox['x_min']
            height = bbox['y_max'] - bbox['y_min']
            
            # Create rectangle patch for door
            door_rect = patches.Rectangle(
                (x, y), width, height,
                linewidth=3,
                edgecolor=door_color,
                facecolor=door_color,
                alpha=0.8
            )
            
            # Add rectangle to plot
            ax.add_patch(door_rect)
    
    # Set plot properties
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title('Room and Door Detection Results')
    ax.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = [patches.Patch(color=color, label=name) 
                      for name, color in room_color_map.items()]
    
    # Add door legend if doors were drawn
    if doors_data and 'doors' in doors_data:
        legend_elements.append(patches.Patch(color='red', label='Doors'))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    plt.show()

def print_detection_stats(rooms_file_path, doors_file_path=None):
    """
    Print statistics about detected rooms and doors.
    """
    # Read rooms data
    with open(rooms_file_path, 'r') as f:
        rooms_data = json.load(f)
    
    print(f"=== Detection Statistics ===")
    print(f"Total rooms detected: {len(rooms_data['rooms'])}")
    
    # Count room types
    room_types = {}
    for room in rooms_data['rooms']:
        name = room['name']
        room_types[name] = room_types.get(name, 0) + 1
    
    print("Room types:")
    for room_type, count in room_types.items():
        print(f"  - {room_type}: {count}")
    
    # Read doors data if provided
    if doors_file_path:
        try:
            with open(doors_file_path, 'r') as f:
                doors_data = json.load(f)
            
            print(f"Total doors detected: {len(doors_data['doors'])}")
            
            # Count door templates
            door_templates = {}
            for door in doors_data['doors']:
                template = door.get('template', 'unknown')
                door_templates[template] = door_templates.get(template, 0) + 1
            
            print("Door templates:")
            for template, count in door_templates.items():
                print(f"  - {template}: {count}")
                
        except FileNotFoundError:
            print(f"Door file {doors_file_path} not found.")

# Example usage:
if __name__ == "__main__":
    # Basic usage with rooms and doors
    draw_bounding_boxes('room_detection_results_b1.json', 'door_detection_results_b1.json')

    # With image overlay (uncomment to use)
    # draw_with_image_overlay('room_detection_results2.json', 'door_locations.json', 'test4.png')
    
    # Print detection statistics
    print_detection_stats('room_detection_results_b1.json', 'door_detection_results_b1.json')

    # Or with only rooms
    # draw_bounding_boxes('room_detection_results5.json')