"""
Main GUI application for OpenAI billing monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional

from ..core.billing_monitor import BillingMonitor
from ..config.manager import ConfigManager
from .config_window import ConfigWindow
from .stats_window import StatsWindow


class BillingGUI:
    """Main GUI application for billing monitoring."""
    
    def __init__(self, billing_monitor: Optional[BillingMonitor] = None):
        self.billing_monitor = billing_monitor or BillingMonitor()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("OpenAI Billing Monitor")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Variables
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = tk.IntVar(value=5)  # seconds
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        self.setup_bindings()
        
        # Start auto-refresh
        self.refresh_thread = None
        self.refresh_running = False
        self.start_auto_refresh()
        
        # Initial data load
        self.refresh_data()
    
    def setup_styles(self):
        """Setup ttk styles."""
        style = ttk.Style()
        
        # Configure styles for better appearance
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9))
        style.configure('Warning.TLabel', foreground='orange', font=('Arial', 9, 'bold'))
        style.configure('Error.TLabel', foreground='red', font=('Arial', 9, 'bold'))
        style.configure('Success.TLabel', foreground='green', font=('Arial', 9, 'bold'))
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="OpenAI Billing Monitor", 
            style='Title.TLabel'
        )
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="10")
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Monitoring: Enabled", 
            style='Success.TLabel'
        )
        
        self.last_update_label = ttk.Label(
            self.status_frame, 
            text="Last update: Never", 
            style='Status.TLabel'
        )
        
        # Quick stats frame
        self.quick_stats_frame = ttk.LabelFrame(self.main_frame, text="Quick Stats", padding="10")
        
        # Create stats labels
        self.stats_labels = {}
        stats_items = [
            ("total_cost", "Total Cost"),
            ("daily_cost", "Daily Cost"), 
            ("monthly_cost", "Monthly Cost"),
            ("total_requests", "Total Requests"),
            ("daily_tokens", "Daily Tokens"),
            ("monthly_tokens", "Monthly Tokens")
        ]
        
        for i, (key, label) in enumerate(stats_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(self.quick_stats_frame, text=f"{label}:", style='Header.TLabel').grid(
                row=row, column=col*2, sticky='w', padx=(0, 5), pady=2
            )
            
            self.stats_labels[key] = ttk.Label(
                self.quick_stats_frame, text="$0.00", style='Status.TLabel'
            )
            self.stats_labels[key].grid(
                row=row, column=col*2+1, sticky='w', padx=(0, 20), pady=2
            )
        
        # Progress bars frame
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="Usage Limits", padding="10")
        
        # Daily progress
        ttk.Label(self.progress_frame, text="Daily Usage:", style='Header.TLabel').grid(
            row=0, column=0, sticky='w', pady=(0, 5)
        )
        
        self.daily_cost_progress = ttk.Progressbar(
            self.progress_frame, mode='determinate', length=200
        )
        self.daily_cost_progress.grid(row=0, column=1, sticky='ew', padx=(10, 5), pady=(0, 5))
        
        self.daily_cost_label = ttk.Label(
            self.progress_frame, text="0%", style='Status.TLabel'
        )
        self.daily_cost_label.grid(row=0, column=2, sticky='w', padx=(5, 0), pady=(0, 5))
        
        # Monthly progress
        ttk.Label(self.progress_frame, text="Monthly Usage:", style='Header.TLabel').grid(
            row=1, column=0, sticky='w', pady=5
        )
        
        self.monthly_cost_progress = ttk.Progressbar(
            self.progress_frame, mode='determinate', length=200
        )
        self.monthly_cost_progress.grid(row=1, column=1, sticky='ew', padx=(10, 5), pady=5)
        
        self.monthly_cost_label = ttk.Label(
            self.progress_frame, text="0%", style='Status.TLabel'
        )
        self.monthly_cost_label.grid(row=1, column=2, sticky='w', padx=(5, 0), pady=5)
        
        # Configure progress frame column weights
        self.progress_frame.columnconfigure(1, weight=1)
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.main_frame)
        
        self.config_button = ttk.Button(
            self.buttons_frame, text="Configuration", command=self.open_config
        )
        
        self.stats_button = ttk.Button(
            self.buttons_frame, text="Detailed Stats", command=self.open_stats
        )
        
        self.reset_button = ttk.Button(
            self.buttons_frame, text="Reset Stats", command=self.reset_stats
        )
        
        self.refresh_button = ttk.Button(
            self.buttons_frame, text="Refresh", command=self.refresh_data
        )
        
        # Settings frame
        self.settings_frame = ttk.LabelFrame(self.main_frame, text="Settings", padding="10")
        
        self.auto_refresh_check = ttk.Checkbutton(
            self.settings_frame, 
            text="Auto-refresh", 
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        )
        
        ttk.Label(self.settings_frame, text="Refresh interval (seconds):").grid(
            row=0, column=1, sticky='w', padx=(20, 5)
        )
        
        self.refresh_interval_spin = ttk.Spinbox(
            self.settings_frame, 
            from_=1, to=60, 
            width=5, 
            textvariable=self.refresh_interval
        )
        
        # Menu bar
        self.create_menu()
    
    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Configuration", command=self.export_config)
        file_menu.add_command(label="Import Configuration", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Configuration", command=self.open_config)
        view_menu.add_command(label="Detailed Statistics", command=self.open_stats)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh", command=self.refresh_data)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reset Daily Stats", command=lambda: self.reset_stats("daily"))
        tools_menu.add_command(label="Reset Monthly Stats", command=lambda: self.reset_stats("monthly"))
        tools_menu.add_command(label="Reset All Stats", command=lambda: self.reset_stats("all"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_layout(self):
        """Setup widget layout."""
        self.main_frame.pack(fill='both', expand=True)
        
        # Title
        self.title_label.pack(pady=(0, 20))
        
        # Status frame
        self.status_frame.pack(fill='x', pady=(0, 10))
        self.status_label.pack(anchor='w')
        self.last_update_label.pack(anchor='w')
        
        # Quick stats frame
        self.quick_stats_frame.pack(fill='x', pady=(0, 10))
        
        # Progress frame
        self.progress_frame.pack(fill='x', pady=(0, 10))
        
        # Buttons frame
        self.buttons_frame.pack(fill='x', pady=(0, 10))
        self.config_button.pack(side='left', padx=(0, 5))
        self.stats_button.pack(side='left', padx=5)
        self.reset_button.pack(side='left', padx=5)
        self.refresh_button.pack(side='right')
        
        # Settings frame
        self.settings_frame.pack(fill='x')
        self.auto_refresh_check.grid(row=0, column=0, sticky='w')
        self.refresh_interval_spin.grid(row=0, column=2, sticky='w')
    
    def setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def refresh_data(self):
        """Refresh all data from billing monitor."""
        try:
            # Update status
            if self.billing_monitor.is_enabled():
                self.status_label.config(text="Monitoring: Enabled", style='Success.TLabel')
            else:
                self.status_label.config(text="Monitoring: Disabled", style='Warning.TLabel')
            
            self.last_update_label.config(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            
            # Get usage summary
            summary = self.billing_monitor.get_usage_summary()
            
            # Update stats labels
            self.stats_labels["total_cost"].config(text=f"${summary.get('total_cost', 0):.4f}")
            self.stats_labels["daily_cost"].config(text=f"${summary.get('daily_cost', 0):.4f}")
            self.stats_labels["monthly_cost"].config(text=f"${summary.get('monthly_cost', 0):.4f}")
            self.stats_labels["total_requests"].config(text=f"{summary.get('total_requests', 0):,}")
            
            # Calculate token totals
            daily_tokens = summary.get('daily_input_tokens', 0) + summary.get('daily_output_tokens', 0)
            monthly_tokens = summary.get('monthly_input_tokens', 0) + summary.get('monthly_output_tokens', 0)
            
            self.stats_labels["daily_tokens"].config(text=f"{daily_tokens:,}")
            self.stats_labels["monthly_tokens"].config(text=f"{monthly_tokens:,}")
            
            # Update progress bars
            self.update_progress_bars(summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")
    
    def update_progress_bars(self, summary):
        """Update progress bars with current usage."""
        
        # Daily cost progress
        daily_limit = summary.get('daily_cost_limit')
        if daily_limit and daily_limit > 0:
            daily_percent = min((summary.get('daily_cost', 0) / daily_limit) * 100, 100)
            self.daily_cost_progress['value'] = daily_percent
            self.daily_cost_label.config(text=f"{daily_percent:.1f}%")
            
            # Change color based on usage
            if daily_percent >= 100:
                self.daily_cost_label.config(style='Error.TLabel')
            elif daily_percent >= 80:
                self.daily_cost_label.config(style='Warning.TLabel')
            else:
                self.daily_cost_label.config(style='Success.TLabel')
        else:
            self.daily_cost_progress['value'] = 0
            self.daily_cost_label.config(text="No limit", style='Status.TLabel')
        
        # Monthly cost progress
        monthly_limit = summary.get('monthly_cost_limit')
        if monthly_limit and monthly_limit > 0:
            monthly_percent = min((summary.get('monthly_cost', 0) / monthly_limit) * 100, 100)
            self.monthly_cost_progress['value'] = monthly_percent
            self.monthly_cost_label.config(text=f"{monthly_percent:.1f}%")
            
            # Change color based on usage
            if monthly_percent >= 100:
                self.monthly_cost_label.config(style='Error.TLabel')
            elif monthly_percent >= 80:
                self.monthly_cost_label.config(style='Warning.TLabel')
            else:
                self.monthly_cost_label.config(style='Success.TLabel')
        else:
            self.monthly_cost_progress['value'] = 0
            self.monthly_cost_label.config(text="No limit", style='Status.TLabel')
    
    def start_auto_refresh(self):
        """Start auto-refresh thread."""
        if self.auto_refresh.get() and not self.refresh_running:
            self.refresh_running = True
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Stop auto-refresh thread."""
        self.refresh_running = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1)
    
    def _auto_refresh_loop(self):
        """Auto-refresh loop running in background thread."""
        while self.refresh_running and self.auto_refresh.get():
            time.sleep(self.refresh_interval.get())
            if self.refresh_running:
                # Schedule refresh in main thread
                self.root.after(0, self.refresh_data)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off."""
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def open_config(self):
        """Open configuration window."""
        ConfigWindow(self.root, self.billing_monitor)
    
    def open_stats(self):
        """Open detailed statistics window."""
        StatsWindow(self.root, self.billing_monitor)
    
    def reset_stats(self, reset_type="all"):
        """Reset usage statistics."""
        if reset_type == "all":
            message = "Are you sure you want to reset all usage statistics?"
        elif reset_type == "daily":
            message = "Are you sure you want to reset daily usage statistics?"
        elif reset_type == "monthly":
            message = "Are you sure you want to reset monthly usage statistics?"
        else:
            message = "Are you sure you want to reset usage statistics?"
        
        if messagebox.askyesno("Confirm Reset", message):
            try:
                self.billing_monitor.reset_usage_stats(reset_type)
                messagebox.showinfo("Success", f"Successfully reset {reset_type} statistics.")
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset statistics: {e}")
    
    def export_config(self):
        """Export configuration to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.billing_monitor.config_manager.export_config(filename)
                messagebox.showinfo("Success", f"Configuration exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export configuration: {e}")
    
    def import_config(self):
        """Import configuration from file."""
        filename = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if messagebox.askyesno("Confirm Import", 
                                 "Importing will overwrite current configuration. Continue?"):
                try:
                    # This would need to be implemented in ConfigManager
                    messagebox.showinfo("Info", "Import functionality not yet implemented.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to import configuration: {e}")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """OpenAI Billing Monitor v0.1.0

A Python library for monitoring and controlling OpenAI API costs.

Features:
• Token usage monitoring
• Cost calculation and threshold management
• Low-invasive integration with OpenAI API
• GUI for configuration and monitoring

© 2024 - MIT License"""
        
        messagebox.showinfo("About", about_text)
    
    def on_closing(self):
        """Handle window closing."""
        self.stop_auto_refresh()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    app = BillingGUI()
    app.run()


if __name__ == "__main__":
    main()
