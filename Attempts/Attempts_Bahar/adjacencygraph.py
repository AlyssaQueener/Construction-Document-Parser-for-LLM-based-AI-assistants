import json
import networkx as nx
import matplotlib.pyplot as plt

def load_json(filepath):
    """Load JSON file containing room adjacencies."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return {}

def create_adjacency_graph(adjacency_data):
    """Create a graph from room adjacency data."""
    G = nx.Graph()
    adjacencies = adjacency_data.get("adjacencies", {})
    
    for room, neighbors in adjacencies.items():
        for neighbor in neighbors:
            G.add_edge(room, neighbor)
    
    return G

def plot_graph(G, title="Room Adjacency Graph"):
    """Plot the room adjacency graph."""
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, edge_color='gray')
    plt.title(title)
    plt.show()

# --- Example Usage ---
if __name__ == "__main__":
    # Replace this with the path to your JSON file from Mistral
    input_file = "room_adjacency_results_b1.json"

    data = load_json(input_file)
    graph = create_adjacency_graph(data)
    plot_graph(graph)
