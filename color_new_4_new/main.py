# main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import os
from datetime import datetime

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
        self.last_algorithm_run = None  # لتخزين معلومات التشغيل الأخير
        self.last_algorithm_name = None
        
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
        
        # زر تحميل التقرير (مخفي في البداية)
        self.download_btn = ttk.Button(action_frame, text="DOWNLOAD REPORT", 
                                      command=self.download_report,
                                      state=tk.DISABLED)  # مخفي حتى يتم تنفيذ خوارزمية
        self.download_btn.pack(fill=tk.X, pady=2)
        
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
            self.max_gen.insert(0, "10")
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
                message = f"Loaded graph from: {file_path}\n"
                message += f"Nodes: {self.current_graph.number_of_nodes()}, "
                message += f"Edges: {self.current_graph.number_of_edges()}\n"
                self.results_text.insert(tk.END, message)
                # طباعة نفس الرسالة في الـ Terminal
                print("=" * 60)
                print("LOADED GRAPH INFORMATION:")
                print(f"File: {file_path}")
                print(f"Number of nodes: {self.current_graph.number_of_nodes()}")
                print(f"Number of edges: {self.current_graph.number_of_edges()}")
                print("=" * 60)
            except Exception as e:
                error_msg = f"Failed to load graph: {e}"
                messagebox.showerror("Error", error_msg)
                print(f"ERROR: {error_msg}")
    
    def create_custom_graph(self):
        # Create a dialog for custom graph input
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Custom Graph")
        dialog.geometry("400x300")
        dialog.configure(bg='#141e30')
        
        ttk.Label(dialog, text="Number of vertices:").pack(pady=5)
        vertices_entry = ttk.Entry(dialog)
        vertices_entry.pack(pady=5)
        
        # إضافة تذكير بأن الترقيم يبدأ من صفر
        info_label = ttk.Label(dialog, text="Note: Vertices are numbered starting from 0", 
                              foreground="yellow", font=('Arial', 9))
        info_label.pack(pady=5)
        
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
                        # التحقق من أن الأرقام صحيحة وفي النطاق الصحيح
                        if u < 0 or v < 0:
                            raise ValueError("Vertex numbers must be non-negative (starting from 0)")
                        if u >= num_vertices or v >= num_vertices:
                            raise ValueError(f"Vertex numbers must be less than {num_vertices} (0 to {num_vertices-1})")
                        edges.append((u, v))
                
                self.current_graph = create_custom_graph(edges, num_vertices)
                self.current_coloring = None
                self.update_graph_info()
                self.graph_canvas.draw_graph(self.current_graph, title="Custom Graph")
                self.results_text.delete(1.0, tk.END)
                success_msg = "Created custom graph\n"
                success_msg += f"Vertices: 0 to {num_vertices-1}\n"
                success_msg += f"Edges: {len(edges)}\n"
                self.results_text.insert(tk.END, success_msg)
                
                # طباعة نفس الرسالة في الـ Terminal
                print("=" * 60)
                print("CUSTOM GRAPH CREATED:")
                print(f"Number of vertices: {num_vertices} (0 to {num_vertices-1})")
                print(f"Number of edges: {len(edges)}")
                if edges:
                    print("Edges list:")
                    for i, (u, v) in enumerate(edges):
                        print(f"  Edge {i+1}: {u} - {v}")
                print("=" * 60)
                
                dialog.destroy()
                
            except ValueError as ve:
                messagebox.showerror("Error", f"Invalid input: {ve}")
                print(f"ERROR creating custom graph: {ve}")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
                print(f"ERROR creating custom graph: {e}")
        
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
            print("WARNING: Please load a graph first!")
            return
        
        # إخفاء زر التحميل أثناء التشغيل
        self.download_btn.config(state=tk.DISABLED)
        
        self.progress.start()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Running solver...\n")
        
        # طباعة في الـ Terminal
        print("\n" + "=" * 60)
        print("STARTING SOLVER...")
        print(f"Algorithm: {self.algo_var.get().upper()}")
        print(f"Graph: {self.current_graph.number_of_nodes()} nodes, {self.current_graph.number_of_edges()} edges")
        print("=" * 60 + "\n")
        
        # تخزين اسم الخوارزمية الحالية
        self.last_algorithm_name = self.algo_var.get()
        
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
            print(f"ERROR during solver execution: {e}")
        finally:
            self.root.after(0, lambda: self.progress.stop())
    
    def _run_backtracking(self):
        max_try = int(self.max_colors.get())
        time_limit = float(self.time_limit.get())
        use_mrv = self.use_mrv.get()
        
        # طباعة المعلمات في الـ Terminal
        print("BACKTRACKING ALGORITHM PARAMETERS:")
        print(f"  Max colors to try: {max_try}")
        print(f"  Time limit: {time_limit} seconds")
        print(f"  Use MRV heuristic: {use_mrv}")
        print("-" * 40)
        
        k, colors, t = try_min_colors(
            self.current_graph, 
            max_try=max_try, 
            use_mrv=use_mrv, 
            time_limit=time_limit
        )
        
        # تخزين نتائج التشغيل الأخير للتقرير
        self.last_algorithm_run = {
            'algorithm': 'Backtracking Search',
            'parameters': {
                'max_colors': max_try,
                'time_limit': time_limit,
                'use_mrv': use_mrv
            },
            'result': {
                'k': k,
                'colors': colors,
                'time': t,
                'success': k is not None
            },
            'graph_info': {
                'nodes': self.current_graph.number_of_nodes(),
                'edges': self.current_graph.number_of_edges()
            }
        }
        
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
            
            # تمكين زر تحميل التقرير
            self.download_btn.config(state=tk.NORMAL)
            
            # طباعة النتائج في الـ Terminal
            print("\n" + "=" * 60)
            print("BACKTRACKING RESULTS:")
            print(f"SUCCESS: Graph is {k}-colorable")
            print(f"Chromatic Number: {k}")
            print(f"Computation Time: {t:.2f} seconds")
            print("\nColoring Assignment:")
            for node, color in sorted(colors.items()):
                print(f"  Node {node} → Color {color}")
            print("=" * 60)
        else:
            self.results_text.insert(tk.END, "FAILED: No valid coloring found within constraints\n")
            self.graph_canvas.draw_graph(self.current_graph, title="No Solution Found")
            
            self.last_results['backtracking'] = {
                'success': False,
                'colors': None,
                'time': t,
                'conflicts': 'N/A'
            }
            
            # تمكين زر تحميل التقرير حتى في حالة الفشل
            self.download_btn.config(state=tk.NORMAL)
            
            # طباعة النتائج في الـ Terminal
            print("\n" + "=" * 60)
            print("BACKTRACKING RESULTS:")
            print("FAILED: No valid coloring found within constraints")
            print(f"Computation Time: {t:.2f} seconds")
            print("=" * 60)
    
    def _run_cultural(self):
        pop_size = int(self.pop_size.get())
        max_gen = int(self.max_gen.get())
        mutation_rate = float(self.mutation_rate.get())
        max_k = int(self.max_k.get())
        
        # طباعة المعلمات في الـ Terminal
        print("CULTURAL ALGORITHM PARAMETERS:")
        print(f"  Population size: {pop_size}")
        print(f"  Max generations: {max_gen}")
        print(f"  Mutation rate: {mutation_rate}")
        print(f"  Max colors to try: {max_k}")
        print("-" * 40)
        
        def progress_callback(gen, conflicts, colors_used):
            # تحديث الـ GUI
            self.root.after(0, lambda: self.results_text.insert(
                tk.END, f"Generation {gen}: Conflicts={conflicts}, Colors={colors_used}\n"
            ))
            self.results_text.see(tk.END)
            
            # طباعة في الـ Terminal
            print(f"Generation {gen}: Conflicts={conflicts}, Colors={colors_used}")
        
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
        
        # تخزين نتائج التشغيل الأخير للتقرير
        self.last_algorithm_run = {
            'algorithm': 'Cultural Algorithm',
            'parameters': {
                'population_size': pop_size,
                'max_generations': max_gen,
                'mutation_rate': mutation_rate,
                'max_k': max_k
            },
            'result': {
                'k': k,
                'colors': coloring_dict if success else {},  # تخزين القاموس مباشرة
                'coloring': coloring_list,  # الاحتفاظ بالقائمة للتوافق
                'time': total_time,
                'success': success
            },
            'graph_info': {
                'nodes': self.current_graph.number_of_nodes(),
                'edges': self.current_graph.number_of_edges()
            }
        }
        
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
            
            # تمكين زر تحميل التقرير
            self.download_btn.config(state=tk.NORMAL)
            
            # طباعة النتائج في الـ Terminal
            print("\n" + "=" * 60)
            print("CULTURAL ALGORITHM RESULTS:")
            print(f"SUCCESS: Valid coloring found!")
            print(f"Chromatic Number: {k}")
            print(f"Total Computation Time: {total_time:.2f} seconds")
            print("\nColoring Assignment:")
            for i, color in enumerate(coloring):
                print(f"  Node {i} → Color {color}")
            print("=" * 60)
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
            
            # تمكين زر تحميل التقرير حتى في حالة الفشل
            self.download_btn.config(state=tk.NORMAL)
            
            # طباعة النتائج في الـ Terminal
            print("\n" + "=" * 60)
            print("CULTURAL ALGORITHM RESULTS:")
            print(f"FAILED: No valid coloring found with k ≤ {self.max_k.get()}")
            print(f"Total Computation Time: {total_time:.2f} seconds")
            print("=" * 60)
    
    def compare_algorithms(self):
        if not self.current_graph:
            messagebox.showwarning("Warning", "Please load a graph first!")
            print("WARNING: Please load a graph first for comparison!")
            return
        
        # طباعة في الـ Terminal
        print("\n" + "=" * 60)
        print("OPENING ALGORITHM COMPARISON WINDOW...")
        print("=" * 60)
        
        # Pass current graph and results to compare window
        CompareWindow(self.root, self.current_graph, self.last_results)
    
    def download_report(self):
        """تحميل تقرير بصيغة PNG"""
        if not self.last_algorithm_run:
            messagebox.showwarning("Warning", "No algorithm has been run yet!")
            return
        
        # اختيار مكان حفظ الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"graph_coloring_report_{timestamp}.png"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                self._create_report_image(file_path)
                messagebox.showinfo("Success", f"Report saved successfully!\n{file_path}")
                print(f"Report saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {e}")
                print(f"ERROR saving report: {e}")
    
    def _create_report_image(self, file_path):
        """إنشاء صورة التقرير"""
        # إنشاء شكل مع 4 رسوم بيانية
        fig = plt.figure(figsize=(15, 12), facecolor='#141e30')
        
        # الرسم البياني 1: معلومات الخوارزمية والنتائج
        ax1 = fig.add_subplot(221)
        ax1.set_facecolor('#141e30')
        ax1.axis('off')
        
        info_text = f"GRAPH COLORING REPORT\n"
        info_text += "=" * 40 + "\n\n"
        info_text += f"Algorithm: {self.last_algorithm_run['algorithm']}\n"
        info_text += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        info_text += f"GRAPH INFORMATION:\n"
        info_text += f"  Nodes: {self.last_algorithm_run['graph_info']['nodes']}\n"
        info_text += f"  Edges: {self.last_algorithm_run['graph_info']['edges']}\n\n"
        
        info_text += "PARAMETERS:\n"
        for key, value in self.last_algorithm_run['parameters'].items():
            info_text += f"  {key.replace('_', ' ').title()}: {value}\n"
        
        info_text += "\nRESULTS:\n"
        if self.last_algorithm_run['result']['success']:
            info_text += f"  Status: SUCCESS\n"
            info_text += f"  Chromatic Number: {self.last_algorithm_run['result']['k']}\n"
            info_text += f"  Computation Time: {self.last_algorithm_run['result']['time']:.2f} seconds\n"
            
            # إضافة توزيع الألوان للرسم البياني
            coloring_data = None
            
            # البحث عن بيانات التلوين في أي من المفاتيح
            if 'colors' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['colors']:
                coloring_data = self.last_algorithm_run['result']['colors']
            elif 'coloring' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['coloring']:
                # تحويل القائمة إلى قاموس
                coloring_list = self.last_algorithm_run['result']['coloring']
                if coloring_list:
                    coloring_data = {i: coloring_list[i] for i in range(len(coloring_list))}
            
            if coloring_data:
                color_counts = {}
                for node, color in coloring_data.items():
                    color_counts[color] = color_counts.get(color, 0) + 1
                
                info_text += "\nCOLOR DISTRIBUTION:\n"
                for color, count in sorted(color_counts.items()):
                    info_text += f"  Color {color}: {count} nodes\n"
            else:
                info_text += "\nCOLOR DISTRIBUTION:\n"
                info_text += f"  No color distribution data available\n"
        else:
            info_text += "  Status: FAILED\n"
            info_text += f"  Reason: No valid coloring found\n"
            info_text += f"  Computation Time: {self.last_algorithm_run['result']['time']:.2f} seconds\n"
        
        ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
                fontfamily='monospace', fontsize=9, va='top', color='white',
                bbox=dict(boxstyle='round', facecolor='#2a3f5f', alpha=0.8))
        
        # الرسم البياني 2: توزيع الألوان (إذا وجد حل)
        ax2 = fig.add_subplot(222)
        ax2.set_facecolor('#141e30')
        ax2.tick_params(colors='white')
        ax2.xaxis.label.set_color('white')
        ax2.yaxis.label.set_color('white')
        ax2.title.set_color('white')
        
        if self.last_algorithm_run['result']['success']:
            # البحث عن بيانات التلوين في أي من المفاتيح
            coloring_data = None
            
            if 'colors' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['colors']:
                coloring_data = self.last_algorithm_run['result']['colors']
            elif 'coloring' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['coloring']:
                # تحويل القائمة إلى قاموس
                coloring_list = self.last_algorithm_run['result']['coloring']
                if coloring_list:
                    coloring_data = {i: coloring_list[i] for i in range(len(coloring_list))}
            
            if coloring_data and len(coloring_data) > 0:
                color_counts = {}
                for node, color in coloring_data.items():
                    color_counts[color] = color_counts.get(color, 0) + 1
                
                colors_list = list(color_counts.keys())
                counts_list = list(color_counts.values())
                
                # استخدام ألوان مختلفة للأعمدة
                colors_bars = plt.cm.tab20(range(len(colors_list)))
                bars = ax2.bar(range(len(colors_list)), counts_list, color=colors_bars, alpha=0.7)
                ax2.set_xlabel('Color Number', color='white', fontweight='bold')
                ax2.set_ylabel('Number of Nodes', color='white', fontweight='bold')
                ax2.set_title('Color Distribution', color='white', fontweight='bold', fontsize=12)
                ax2.set_xticks(range(len(colors_list)))
                ax2.set_xticklabels(colors_list, color='white')
                
                # إضافة القيم فوق الأعمدة
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{counts_list[i]}', ha='center', va='bottom', 
                            color='white', fontweight='bold', fontsize=10)
                
                # إضافة شبكة خلفية
                ax2.grid(True, alpha=0.3, color='gray')
            else:
                ax2.text(0.5, 0.5, 'No coloring data available\nfor visualization',
                        ha='center', va='center', transform=ax2.transAxes, 
                        color='white', fontsize=11, fontweight='bold')
                ax2.set_title('Color Distribution', color='white', fontweight='bold', fontsize=12)
        else:
            ax2.text(0.5, 0.5, 'No valid coloring found\nAlgorithm failed to find solution',
                    ha='center', va='center', transform=ax2.transAxes, 
                    color='white', fontsize=11, fontweight='bold')
            ax2.set_title('Color Distribution', color='white', fontweight='bold', fontsize=12)
        
        # الرسم البياني 3: أداء الخوارزمية
        ax3 = fig.add_subplot(223)
        ax3.set_facecolor('#141e30')
        ax3.tick_params(colors='white')
        ax3.xaxis.label.set_color('white')
        ax3.yaxis.label.set_color('white')
        ax3.title.set_color('white')
        
        algorithm_name = self.last_algorithm_run['algorithm']
        time_taken = self.last_algorithm_run['result']['time']
        success_rate = 1.0 if self.last_algorithm_run['result']['success'] else 0.0
        
        metrics = ['Time (s)', 'Success']
        values = [time_taken, success_rate]
        
        bars = ax3.bar(metrics, values, 
                      color=['#3f5e96', '#14a37f' if success_rate > 0 else '#e74c3c'],
                      alpha=0.7, width=0.6)
        ax3.set_title(f'{algorithm_name.upper()} Performance', 
                     color='white', fontweight='bold', fontsize=12)
        ax3.set_ylabel('Value', color='white', fontweight='bold')
        ax3.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1.2)
        
        # إضافة القيم فوق الأعمدة
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if i == 0:
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{values[i]:.2f}s', ha='center', va='bottom', 
                        color='white', fontweight='bold', fontsize=10)
            else:
                status_text = "SUCCESS" if values[i] > 0 else "FAILED"
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        status_text, ha='center', va='bottom', 
                        color='white', fontweight='bold', fontsize=10)
        
        # إضافة شبكة خلفية
        ax3.grid(True, alpha=0.3, color='gray')
        
        # الرسم البياني 4: ملخص
        ax4 = fig.add_subplot(224)
        ax4.set_facecolor('#141e30')
        ax4.axis('off')
        
        summary_text = "PERFORMANCE SUMMARY\n"
        summary_text += "=" * 30 + "\n\n"
        
        if self.last_algorithm_run['result']['success']:
            summary_text += "✓ SUCCESSFUL EXECUTION\n\n"
            summary_text += f"Chromatic Number Found: {self.last_algorithm_run['result']['k']}\n"
            
            # حساب عدد الألوان المستخدمة
            coloring_data = None
            if 'colors' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['colors']:
                coloring_data = self.last_algorithm_run['result']['colors']
            elif 'coloring' in self.last_algorithm_run['result'] and self.last_algorithm_run['result']['coloring']:
                coloring_list = self.last_algorithm_run['result']['coloring']
                if coloring_list:
                    coloring_data = {i: coloring_list[i] for i in range(len(coloring_list))}
            
            if coloring_data:
                unique_colors = len(set(coloring_data.values()))
                summary_text += f"Total Colors Used: {unique_colors}\n"
        else:
            summary_text += "✗ EXECUTION FAILED\n\n"
            summary_text += "No valid coloring found within\n"
            summary_text += "the given constraints.\n"
        
        summary_text += f"\nExecution Time: {self.last_algorithm_run['result']['time']:.2f} seconds\n"
        
        # تقييم كفاءة الخوارزمية
        if time_taken < 5:
            efficiency = "HIGH"
            efficiency_color = "#14a37f"
        elif time_taken < 15:
            efficiency = "MEDIUM"
            efficiency_color = "#f39c12"
        else:
            efficiency = "LOW"
            efficiency_color = "#e74c3c"
        
        summary_text += f"\nAlgorithm Efficiency: {efficiency}\n"
        
        ax4.text(0.5, 0.5, summary_text, transform=ax4.transAxes,
                ha='center', va='center', fontfamily='monospace', fontsize=10,
                color='white', bbox=dict(boxstyle='round', facecolor='#2a3f5f', alpha=0.8))
        
        plt.suptitle(f"Graph Coloring Report - {self.last_algorithm_run['algorithm']}", 
                    fontsize=16, fontweight='bold', color='white')
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # حفظ الصورة
        plt.savefig(file_path, facecolor='#141e30', dpi=150, bbox_inches='tight')
        plt.close()
    
    def clear_all(self):
        self.current_graph = None
        self.current_coloring = None
        self.last_results = {}
        self.last_algorithm_run = None
        self.update_graph_info()
        self.graph_canvas.clear()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Ready...\n")
        self.download_btn.config(state=tk.DISABLED)  # تعطيل زر التحميل
        
        # طباعة في الـ Terminal
        print("\n" + "=" * 60)
        print("CLEARED ALL DATA")
        print("Ready for new graph...")
        print("=" * 60)

if __name__ == "__main__":
    plt.rcParams['font.size'] = 9
    root = tk.Tk()
    app = GraphColoringApp(root)
    
    # طباعة رسالة بدء التشغيل في الـ Terminal
    print("\n" + "=" * 60)
    print("GRAPH COLORING PROBLEM SOLVER")
    print("Application Started Successfully!")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Load a dataset or create a custom graph")
    print("2. Select algorithm and parameters")
    print("3. Click RUN SOLVER to start coloring")
    print("4. After algorithm finishes, use DOWNLOAD REPORT to save results")
    print("5. All messages will appear both in GUI and Terminal")
    print("=" * 60 + "\n")
    
    root.mainloop()