import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
from algorithms.backtracking import try_min_colors
from algorithms.cultural import find_chromatic_number
from algorithms.graph_utils import load_edgelist

class CompareWindow:
    def __init__(self, parent, graph, last_results=None):
        self.parent = parent
        self.graph = graph
        self.last_results = last_results or {}
        self.results = {}
        self.setup_window()
        
    def setup_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Algorithm Comparison")
        self.window.geometry("900x700")
        self.window.configure(bg='#141e30')
        
        # Configure style for dark theme with hover effects
        style = ttk.Style()
        style.configure('TFrame', background='#141e30')
        style.configure('TLabel', background='#141e30', foreground='white')
        style.configure('TButton', background='#3f5e96', foreground='white')
        style.configure('TProgressbar', background='#3f5e96')
        
        # Configure hover effects for buttons
        style.map('TButton',
                 background=[('active', '#3f5e96')],
                 foreground=[('active', '#ffd700')])  # تغيير لون النص إلى ذهبي عند Hover
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # إزالة زر Run Full Comparison وإبقاء Use Existing Results فقط
        if self.last_results:
            ttk.Button(control_frame, text="Use Existing Results", 
                      command=self.use_existing_results).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(control_frame, text="No results available. Run algorithms first.", 
                     foreground='white').pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready to compare existing results")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Results frame
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text results with dark theme
        self.results_text = tk.Text(results_frame, height=15, 
                                   bg='#2a3f5f', fg='white',
                                   insertbackground='white')
        self.results_text.pack(fill=tk.BOTH, pady=5)
        
        # Plot frame
        plot_frame = ttk.Frame(results_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_plots(plot_frame)
        
        # Auto-load existing results if available
        if self.last_results:
            self.window.after(100, self.use_existing_results)
        
    def setup_plots(self, parent):
        # Create matplotlib figures with dark theme
        self.fig = Figure(figsize=(10, 8), facecolor='#141e30')
        
        self.ax1 = self.fig.add_subplot(221)
        self.ax2 = self.fig.add_subplot(222)
        self.ax3 = self.fig.add_subplot(223)
        self.ax4 = self.fig.add_subplot(224)
        
        # Set dark background for all subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#141e30')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def use_existing_results(self):
        """Use results that are already available from main window"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Loading existing results...\n")
        
        if not self.last_results:
            self.results_text.insert(tk.END, "No existing results found. Please run algorithms first.\n")
            return
        
        # Convert last_results to the format expected by this window
        for algo, result in self.last_results.items():
            self.results[algo] = {
                'success': result['success'],
                'colors': result['colors'],
                'time': result['time'],
                'conflicts': result.get('conflicts', 0),
                'method': 'Backtracking Search' if algo == 'backtracking' else 'Cultural Algorithm'
            }
            
        self._update_display()
        self.status_label.config(text="Comparison completed")
    
    def _update_display(self):
        """Update the display with current results"""
        # Update text results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "\n" + "="*60 + "\n")
        self.results_text.insert(tk.END, "COMPARISON RESULTS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")
        
        for algo, result in self.results.items():
            self.results_text.insert(tk.END, f"{result['method']}:\n")
            self.results_text.insert(tk.END, f"  Success: {result['success']}\n")
            self.results_text.insert(tk.END, f"  Colors: {result['colors']}\n")
            self.results_text.insert(tk.END, f"  Time: {result['time']:.4f}s\n")
            if 'conflicts' in result:
                self.results_text.insert(tk.END, f"  Conflicts: {result['conflicts']}\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Update plots
        self._update_plots()
        
    def _update_plots(self):
        # Clear plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Set dark theme for cleared plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#141e30')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
        
        if not self.results:
            return
            
        # Plot 1: Time comparison
        algorithms = [self.results[algo]['method'] for algo in self.results]
        times = [self.results[algo]['time'] for algo in self.results]
        
        bars1 = self.ax1.bar(algorithms, times, color=['#3f5e96', '#14a37f'], alpha=0.7)
        self.ax1.set_title('Computation Time Comparison')
        self.ax1.set_ylabel('Time (seconds)')
        
        # Add value labels on bars
        for bar, time_val in zip(bars1, times):
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                         f'{time_val:.4f}s', ha='center', va='bottom', color='white')
        
        # Plot 2: Colors comparison (only for successful runs)
        colors_data = []
        valid_algorithms = []
        for algo in self.results:
            if self.results[algo]['success'] and isinstance(self.results[algo]['colors'], int):
                colors_data.append(self.results[algo]['colors'])
                valid_algorithms.append(self.results[algo]['method'])
        
        if colors_data:
            bars2 = self.ax2.bar(valid_algorithms, colors_data, color=['#3f5e96', '#14a37f'], alpha=0.7)
            self.ax2.set_title('Solution Quality (Colors Used)')
            self.ax2.set_ylabel('Number of Colors')
            
            # Add value labels on bars
            for bar, color_val in zip(bars2, colors_data):
                height = bar.get_height()
                self.ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                             f'{color_val}', ha='center', va='bottom', color='white')
        else:
            self.ax2.text(0.5, 0.5, 'No successful runs', 
                         ha='center', va='center', transform=self.ax2.transAxes, color='white')
            self.ax2.set_title('Solution Quality (Colors Used)')
        
        # Plot 3: Success comparison
        success_rates = [1 if self.results[algo]['success'] else 0 for algo in self.results]
        algorithms_names = [self.results[algo]['method'] for algo in self.results]
        
        bars3 = self.ax3.bar(algorithms_names, success_rates, 
                            color=['#14a37f' if rate else '#e74c3c' for rate in success_rates],
                            alpha=0.7)
        self.ax3.set_title('Solution Found')
        self.ax3.set_ylabel('Success (1=Yes, 0=No)')
        self.ax3.set_ylim(0, 1.2)
        
        # Add value labels on bars
        for bar, success in zip(bars3, success_rates):
            height = bar.get_height()
            status = "SUCCESS" if success else "FAILED"
            self.ax3.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                         status, ha='center', va='bottom', fontweight='bold', color='white')
        
        # Plot 4: Performance summary
        self.ax4.axis('off')
        summary_text = "Performance Summary:\n\n"
        for algo in self.results:
            result = self.results[algo]
            status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
            summary_text += f"{result['method']}:\n"
            summary_text += f"  Status: {status}\n"
            summary_text += f"  Colors: {result['colors']}\n"
            summary_text += f"  Time: {result['time']:.4f}s\n\n"
        
        self.ax4.text(0.1, 0.9, summary_text, transform=self.ax4.transAxes,
                     fontfamily='monospace', fontsize=10, va='top', color='white')
        
        self.fig.tight_layout()
        self.canvas.draw()