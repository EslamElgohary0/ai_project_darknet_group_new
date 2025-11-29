import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import networkx as nx

class GraphCanvas:
    def __init__(self, parent):
        self.parent = parent
        self.setup_canvas()
        
    def setup_canvas(self):
        # Create matplotlib figure with dark theme
        self.figure = Figure(figsize=(6, 5), dpi=100, facecolor='#141e30')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#141e30')
        
        # Create tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def draw_graph(self, G, coloring_dict=None, title="Graph", conflicts=0):
        """Draw graph with optional coloring"""
        self.ax.clear()
        self.ax.set_facecolor('#141e30')
        
        # Choose layout based on graph size
        if G.number_of_nodes() <= 20:
            pos = nx.spring_layout(G, seed=42, k=1.5, iterations=50)
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Prepare node colors
        if coloring_dict and len(coloring_dict) == G.number_of_nodes():
            nodes = list(G.nodes())
            node_colors = [coloring_dict.get(node, 0) for node in nodes]
            
            # Use a colormap
            cmap = plt.cm.tab20
            unique_colors = len(set(node_colors))
            
            # Draw colored graph
            nx.draw_networkx_nodes(G, pos, ax=self.ax, node_size=500,
                                 node_color=node_colors, cmap=cmap, 
                                 edgecolors='white', linewidths=1)
            
            # Highlight conflicting edges
            edge_colors = []
            for edge in G.edges():
                if coloring_dict.get(edge[0]) == coloring_dict.get(edge[1]):
                    edge_colors.append('red')  # Conflict
                else:
                    edge_colors.append('white')
            
            nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color=edge_colors, 
                                 width=2, alpha=0.7)
            
        else:
            # Draw uncolored graph
            nx.draw_networkx_nodes(G, pos, ax=self.ax, node_size=500,
                                 node_color='#3f5e96', edgecolors='white', 
                                 linewidths=1)
            nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color='white', 
                                 width=1, alpha=0.7)
        
        # Draw labels with white color
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=10, 
                              font_weight='bold', font_color='white')
        
        # Set title with white color
        title_text = f"{title}\n"
        if coloring_dict:
            colors_used = len(set(coloring_dict.values()))
            title_text += f"Colors: {colors_used}, Conflicts: {conflicts}"
        self.ax.set_title(title_text, fontsize=12, fontweight='bold', color='white')
        
        self.ax.axis('off')
        self.figure.tight_layout()
        self.canvas.draw()
        
    def clear(self):
        """Clear the canvas"""
        self.ax.clear()
        self.ax.set_facecolor('#141e30')
        self.ax.set_title("Graph will be displayed here", color='white')
        self.ax.axis('off')
        self.canvas.draw()