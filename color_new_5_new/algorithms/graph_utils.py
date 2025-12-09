import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import json
from typing import Optional

def load_edgelist(path: str) -> nx.Graph:
    """Load graph from various file formats"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    G = nx.Graph()
    edges = []
    
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c') or line.startswith('#'):
                continue
            
            parts = line.split()
            
            # DIMACS format
            if parts[0] == 'p' and len(parts) >= 3:
                num_nodes = int(parts[2])
                G.add_nodes_from(range(num_nodes))
                continue
            elif parts[0] == 'e' and len(parts) >= 3:
                u, v = int(parts[1]), int(parts[2])
                # Convert to 0-based indexing if needed
                u = u - 1 if u > 0 else u
                v = v - 1 if v > 0 else v
                edges.append((u, v))
            # Simple edge list format
            elif len(parts) >= 2:
                try:
                    u, v = int(parts[0]), int(parts[1])
                    edges.append((u, v))
                except ValueError:
                    continue
    
    if edges:
        G.add_edges_from(edges)
    
    # Ensure all nodes are present
    all_nodes = set()
    for u, v in edges:
        all_nodes.add(u)
        all_nodes.add(v)
    
    for node in all_nodes:
        if node not in G:
            G.add_node(node)
    
    return G

def create_custom_graph(edges: list, num_vertices: int) -> nx.Graph:
    """Create graph from custom edges"""
    G = nx.Graph()
    G.add_nodes_from(range(num_vertices))
    G.add_edges_from(edges)
    return G

def calculate_conflicts(G: nx.Graph, coloring: dict) -> int:
    """Calculate number of coloring conflicts"""
    conflicts = 0
    for u, v in G.edges():
        if coloring.get(u) == coloring.get(v):
            conflicts += 1
    return conflicts

def get_available_datasets() -> list:
    """Get list of available dataset files"""
    datasets_dir = Path("datasets")
    if not datasets_dir.exists():
        return []
    return [f for f in datasets_dir.glob("*") if f.is_file() and f.suffix in ['.col', '.edgelist']]