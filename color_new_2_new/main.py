# main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

from algorithms.backtracking import try_min_colors
from algorithms.cultural import find_chromatic_number
from algorithms.graph_utils import load_edgelist, create_custom_graph
from graph_canvas import GraphCanvas
from compare_window import CompareWindow

class GraphColoringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Coloring Problem Solver")
        self.root.geometry("1200x800")
        self.root.configure(bg='#141e30')
        
        self.current_graph = None
        self.current_coloring = None
        self.last_results = {}
        
        # Set theme and colors
        self.setup_theme()
        self.create_widgets()
        
    def setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background='#141e30')
        style.configure('TLabel', background='#141e30', foreground='white', font=('Arial', 10))
        
        # تنسيق الأزرار الأساسية
        style.configure('TButton', 
                       background='#3f5e96', 
                       foreground='white', 
                       font=('Arial', 10),
                       focuscolor='none')
        
        # تنسيق الأزرار عند المرور بالماوس
        style.map('TButton',
                 background=[('active', '#2a3f5f'),  # لون أغمق عند الـ hover
                           ('pressed', '#1e2f4f')],
                 foreground=[('active', 'white'),     # النص يظل أبيض
                           ('pressed', 'white')])
        
        # تنسيق Labelframe
        style.configure('TLabelframe', background='#141e30', foreground='white')
        style.configure('TLabelframe.Label', background='#141e30', foreground='white')
        
        # تنسيق RadioButton و Checkbutton
        style.configure('TRadiobutton', background='#141e30', foreground='white')
        style.configure('TCheckbutton', background='#141e30', foreground='white')
        
        # تنسيق Entry
        style.configure('TEntry', fieldbackground='#2a3f5f', foreground='white')
        
        # تنسيق Progressbar
        style.configure('TProgressbar', background='#3f5e96')
        
    def create_widgets(self):
        # Create main paned window for resizable layout
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame - controls
        left_frame = ttk.Frame(main_pane, width=300)
        main_pane.add(left_frame, weight=0)
        
        self.create_control_frame(left_frame)
        
        # Right frame - visualization and results
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)
        
        self.create_visualization_frame(right_frame)
        self.create_results_frame(right_frame)
        
    def create_control_frame(self, parent):
        # Title
        title_label = ttk.Label(parent, text="Graph Coloring Solver", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Graph Input Section
        input_frame = ttk.LabelFrame(parent, text="Graph Input", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(input_frame, text="Load Dataset", 
                  command=self.load_dataset).pack(fill=tk.X, pady=2)
        
        ttk.Button(input_frame, text="Create Custom Graph", 
                  command=self.create_custom_graph).pack(fill=tk.X, pady=2)
        
        self.graph_info = ttk.Label(input_frame, text="No graph loaded")
        self.graph_info.pack(pady=5)
        
        # Algorithm Selection
        algo_frame = ttk.LabelFrame(parent, text="Algorithm Selection", padding="10")
        algo_frame.pack(fill=tk.X, pady=5)
        
        self.algo_var = tk.StringVar(value="backtracking")
        ttk.Radiobutton(algo_frame, text="Backtracking Search", 
                       variable=self.algo_var, value="backtracking",
                       command=self.toggle_parameters).pack(anchor=tk.W)
        ttk.Radiobutton(algo_frame, text="Cultural Algorithm", 
                       variable=self.algo_var, value="cultural",
                       command=self.toggle_parameters).pack(anchor=tk.W)
        
        # Parameters Frame
        self.params_frame = ttk.LabelFrame(parent, text="Parameters", padding="10")
        self.params_frame.pack(fill=tk.X, pady=5)
        
        self.create_parameter_widgets()
        
        # Action Buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="RUN SOLVER", 
                  command=self.run_solver).pack(fill=tk.X, pady=2)
        
        ttk.Button(action_frame, text="COMPARE ALGORITHMS", 
                  command=self.compare_algorithms).pack(fill=tk.X, pady=2)
        
        ttk.Button(action_frame, text="CLEAR", 
                  command=self.clear_all).pack(fill=tk.X, pady=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
    def create_parameter_widgets(self):
        # Clear existing widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()
            
        if self.algo_var.get() == "cultural":
            # Cultural algorithm parameters
            ttk.Label(self.params_frame, text="Population Size:").pack(anchor=tk.W)
            self.pop_size = ttk.Entry(self.params_frame)
            self.pop_size.insert(0, "50")
            self.pop_size.pack(fill=tk.X, pady=2)
            
            ttk.Label(self.params_frame, text="Max Generations:").pack(anchor=tk.W)
            self.max_gen = ttk.Entry(self.params_frame)
            self.max_gen.insert(0, "100")
            self.max_gen.pack(fill=tk.X, pady=2)
            
            ttk.Label(self.params_frame, text="Mutation Rate:").pack(anchor=tk.W)
            self.mutation_rate = ttk.Entry(self.params_frame)
            self.mutation_rate.insert(0, "0.1")
            self.mutation_rate.pack(fill=tk.X, pady=2)
            
            ttk.Label(self.params_frame, text="Max Colors to Try:").pack(anchor=tk.W)
            self.max_k = ttk.Entry(self.params_frame)
            self.max_k.insert(0, "10")
            self.max_k.pack(fill=tk.X, pady=2)
        else:
            # Backtracking parameters
            ttk.Label(self.params_frame, text="Max Colors to Try:").pack(anchor=tk.W)
            self.max_colors = ttk.Entry(self.params_frame)
            self.max_colors.insert(0, "10")
            self.max_colors.pack(fill=tk.X, pady=2)
            
            ttk.Label(self.params_frame, text="Time Limit (seconds):").pack(anchor=tk.W)
            self.time_limit = ttk.Entry(self.params_frame)
            self.time_limit.insert(0, "30")
            self.time_limit.pack(fill=tk.X, pady=2)
            
            self.use_mrv = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.params_frame, text="Use MRV Heuristic", 
                           variable=self.use_mrv).pack(anchor=tk.W, pady=2)
    
    def toggle_parameters(self):
        self.create_parameter_widgets()
    
    def create_visualization_frame(self, parent):
        viz_frame = ttk.LabelFrame(parent, text="Graph Visualization", padding="10")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.graph_canvas = GraphCanvas(viz_frame)
    
    def create_results_frame(self, parent):
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, pady=5)
        
        # Configure text widget with dark theme
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, 
                                                     bg='#2a3f5f', fg='white',
                                                     insertbackground='white')
        self.results_text.pack(fill=tk.BOTH, expand=True)
    
    def load_dataset(self):
        file_path = filedialog.askopenfilename(
            initialdir="datasets",
            title="Select Graph File",
            filetypes=[("Graph files", "*.col *.edgelist"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.current_graph = load_edgelist(file_path)
                self.current_coloring = None
                self.update_graph_info()
                self.graph_canvas.draw_graph(self.current_graph, title="Loaded Graph")
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Loaded graph from: {file_path}\n")
                self.results_text.insert(tk.END, f"Nodes: {self.current_graph.number_of_nodes()}, ")
                self.results_text.insert(tk.END, f"Edges: {self.current_graph.number_of_edges()}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load graph: {e}")
    
    def create_custom_graph(self):
        # Create a dialog for custom graph input
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Custom Graph")
        dialog.geometry("400x300")
        dialog.configure(bg='#141e30')
        
        ttk.Label(dialog, text="Number of vertices:").pack(pady=5)
        vertices_entry = ttk.Entry(dialog)
        vertices_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Edges (one per line, format: u v):").pack(pady=5)
        edges_text = scrolledtext.ScrolledText(dialog, height=8, bg='#2a3f5f', fg='white')
        edges_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def create_graph():
            try:
                num_vertices = int(vertices_entry.get())
                edges_input = edges_text.get(1.0, tk.END).strip()
                edges = []
                
                for line in edges_input.split('\n'):
                    line = line.strip()
                    if line:
                        u, v = map(int, line.split())
                        edges.append((u, v))
                
                self.current_graph = create_custom_graph(edges, num_vertices)
                self.current_coloring = None
                self.update_graph_info()
                self.graph_canvas.draw_graph(self.current_graph, title="Custom Graph")
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Created custom graph\n")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        ttk.Button(dialog, text="Create Graph", command=create_graph).pack(pady=10)
    
    def update_graph_info(self):
        if self.current_graph:
            info = f"Graph: {self.current_graph.number_of_nodes()} nodes, "
            info += f"{self.current_graph.number_of_edges()} edges"
            self.graph_info.config(text=info)
        else:
            self.graph_info.config(text="No graph loaded")
    
    def run_solver(self):
        if not self.current_graph:
            messagebox.showwarning("Warning", "Please load a graph first!")
            return
        
        self.progress.start()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Running solver...\n")
        
        # Run in separate thread to keep GUI responsive
        thread = threading.Thread(target=self._run_solver_thread)
        thread.daemon = True
        thread.start()
    
    def _run_solver_thread(self):
        try:
            if self.algo_var.get() == "backtracking":
                self._run_backtracking()
            else:
                self._run_cultural()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.progress.stop())
    
    def _run_backtracking(self):
        max_try = int(self.max_colors.get())
        time_limit = float(self.time_limit.get())
        use_mrv = self.use_mrv.get()
        
        k, colors, t = try_min_colors(
            self.current_graph, 
            max_try=max_try, 
            use_mrv=use_mrv, 
            time_limit=time_limit
        )
        
        self.root.after(0, lambda: self._display_backtracking_results(k, colors, t))
    
    def _display_backtracking_results(self, k, colors, t):
        self.results_text.delete(1.0, tk.END)
        
        if k is not None:
            self.current_coloring = colors
            conflicts = 0
            
            self.results_text.insert(tk.END, "=== BACKTRACKING RESULTS ===\n\n")
            self.results_text.insert(tk.END, f"SUCCESS: Graph is {k}-colorable\n")
            self.results_text.insert(tk.END, f"Chromatic Number: {k}\n")
            self.results_text.insert(tk.END, f"Computation Time: {t:.2f} seconds\n")
            self.results_text.insert(tk.END, f"\nColoring Assignment:\n")
            
            for node, color in sorted(colors.items()):
                self.results_text.insert(tk.END, f"  Node {node} → Color {color}\n")
            
            self.graph_canvas.draw_graph(self.current_graph, colors, 
                                       f"Backtracking Solution (k={k})", conflicts)
            
            # Store results
            self.last_results['backtracking'] = {
                'success': True,
                'colors': k,
                'time': t,
                'conflicts': 0
            }
        else:
            self.results_text.insert(tk.END, "FAILED: No valid coloring found within constraints\n")
            self.graph_canvas.draw_graph(self.current_graph, title="No Solution Found")
            
            self.last_results['backtracking'] = {
                'success': False,
                'colors': None,
                'time': t,
                'conflicts': 'N/A'
            }
    
    def _run_cultural(self):
        pop_size = int(self.pop_size.get())
        max_gen = int(self.max_gen.get())
        mutation_rate = float(self.mutation_rate.get())
        max_k = int(self.max_k.get())
        
        def progress_callback(gen, conflicts, colors_used):
            self.root.after(0, lambda: self.results_text.insert(
                tk.END, f"Generation {gen}: Conflicts={conflicts}, Colors={colors_used}\n"
            ))
            self.results_text.see(tk.END)
        
        # Use find_chromatic_number like the old version
        k, coloring_dict, total_time = find_chromatic_number(
            self.current_graph,
            pop_size=pop_size,
            max_gen=max_gen,
            mutation_rate=mutation_rate,
            max_k=max_k,
            progress_callback=progress_callback
        )
        
        success = (k is not None)
        coloring_list = [coloring_dict[i] for i in range(len(coloring_dict))] if success else []
        
        self.root.after(0, lambda: self._display_cultural_results(success, coloring_list, k, 0, total_time))
    
    def _display_cultural_results(self, success, coloring, k, conflicts, total_time):
        self.results_text.insert(tk.END, "\n=== CULTURAL ALGORITHM RESULTS ===\n\n")
        
        if success:
            self.current_coloring = {i: coloring[i] for i in range(len(coloring))}
            self.results_text.insert(tk.END, f"SUCCESS: Valid coloring found!\n")
            self.results_text.insert(tk.END, f"Chromatic Number: {k}\n")
            self.results_text.insert(tk.END, f"Total Computation Time: {total_time:.2f} seconds\n")
            self.results_text.insert(tk.END, f"\nColoring Assignment:\n")
            
            for i, color in enumerate(coloring):
                self.results_text.insert(tk.END, f"  Node {i} → Color {color}\n")
            
            self.graph_canvas.draw_graph(self.current_graph, self.current_coloring,
                                       f"Cultural Algorithm Solution (k={k})", conflicts)
            
            # Store results
            self.last_results['cultural'] = {
                'success': True,
                'colors': k,
                'time': total_time,
                'conflicts': 0
            }
        else:
            self.results_text.insert(tk.END, f"FAILED: No valid coloring found with k ≤ {self.max_k.get()}\n")
            self.results_text.insert(tk.END, f"Total Computation Time: {total_time:.2f} seconds\n")
            self.graph_canvas.draw_graph(self.current_graph, title="No Solution Found")
            
            self.last_results['cultural'] = {
                'success': False,
                'colors': None,
                'time': total_time,
                'conflicts': 'N/A'
            }
    
    def compare_algorithms(self):
        if not self.current_graph:
            messagebox.showwarning("Warning", "Please load a graph first!")
            return
        
        # Pass current graph and results to compare window
        CompareWindow(self.root, self.current_graph, self.last_results)
    
    def clear_all(self):
        self.current_graph = None
        self.current_coloring = None
        self.last_results = {}
        self.update_graph_info()
        self.graph_canvas.clear()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Ready...\n")

if __name__ == "__main__":
    plt.rcParams['font.size'] = 9
    root = tk.Tk()
    app = GraphColoringApp(root)
    root.mainloop()