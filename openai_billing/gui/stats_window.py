"""
Detailed statistics window for the billing monitor GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..core.billing_monitor import BillingMonitor


class StatsWindow:
    """Detailed statistics window."""
    
    def __init__(self, parent: tk.Tk, billing_monitor: BillingMonitor):
        self.parent = parent
        self.billing_monitor = billing_monitor
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Detailed Statistics")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        # Variables
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = tk.IntVar(value=5)
        
        # Create widgets
        self.create_widgets()
        self.setup_layout()
        
        # Start auto-refresh
        self.refresh_running = False
        self.start_auto_refresh()
        
        # Initial data load
        self.refresh_data()
        
        # Center window
        self.center_window()
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all widgets."""
        
        # Main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="Detailed Usage Statistics", 
            font=('Arial', 14, 'bold')
        )
        
        # Notebook for different views
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Overview tab
        self.overview_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.overview_frame, text="Overview")
        self.create_overview_widgets()
        
        # Daily stats tab
        self.daily_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.daily_frame, text="Daily Stats")
        self.create_daily_widgets()
        
        # Monthly stats tab
        self.monthly_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.monthly_frame, text="Monthly Stats")
        self.create_monthly_widgets()
        
        # Limits tab
        self.limits_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.limits_frame, text="Limits & Progress")
        self.create_limits_widgets()
        
        # Controls frame
        self.controls_frame = ttk.Frame(self.main_frame)
        
        # Auto-refresh controls
        ttk.Checkbutton(
            self.controls_frame, 
            text="Auto-refresh", 
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        ).pack(side='left')
        
        ttk.Label(self.controls_frame, text="Interval (s):").pack(side='left', padx=(10, 5))
        
        ttk.Spinbox(
            self.controls_frame, 
            from_=1, to=60, 
            width=5, 
            textvariable=self.refresh_interval
        ).pack(side='left')
        
        # Refresh button
        ttk.Button(
            self.controls_frame, 
            text="Refresh Now", 
            command=self.refresh_data
        ).pack(side='right', padx=(10, 0))
        
        # Export button
        ttk.Button(
            self.controls_frame, 
            text="Export Data", 
            command=self.export_data
        ).pack(side='right')
    
    def create_overview_widgets(self):
        """Create overview tab widgets."""
        
        # Summary stats frame
        summary_frame = ttk.LabelFrame(self.overview_frame, text="Summary", padding="10")
        summary_frame.pack(fill='x', pady=(0, 10))
        
        # Create summary labels
        self.summary_labels = {}
        summary_items = [
            ("total_cost", "Total Cost", "$0.00"),
            ("total_requests", "Total Requests", "0"),
            ("total_input_tokens", "Total Input Tokens", "0"),
            ("total_output_tokens", "Total Output Tokens", "0"),
            ("avg_cost_per_request", "Avg Cost/Request", "$0.00"),
            ("last_request", "Last Request", "Never")
        ]
        
        for i, (key, label, default) in enumerate(summary_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(summary_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=row, column=col*2, sticky='w', padx=(0, 5), pady=3
            )
            
            self.summary_labels[key] = ttk.Label(summary_frame, text=default)
            self.summary_labels[key].grid(
                row=row, column=col*2+1, sticky='w', padx=(0, 30), pady=3
            )
        
        # Recent activity frame
        activity_frame = ttk.LabelFrame(self.overview_frame, text="Recent Activity", padding="10")
        activity_frame.pack(fill='both', expand=True)
        
        # Activity text widget with scrollbar
        activity_text_frame = ttk.Frame(activity_frame)
        activity_text_frame.pack(fill='both', expand=True)
        
        self.activity_text = tk.Text(
            activity_text_frame, 
            wrap='word', 
            height=15,
            state='disabled',
            font=('Consolas', 9)
        )
        
        activity_scrollbar = ttk.Scrollbar(
            activity_text_frame, 
            orient='vertical', 
            command=self.activity_text.yview
        )
        
        self.activity_text.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_text.pack(side='left', fill='both', expand=True)
        activity_scrollbar.pack(side='right', fill='y')
    
    def create_daily_widgets(self):
        """Create daily stats tab widgets."""
        
        # Daily stats labels
        daily_stats_frame = ttk.LabelFrame(self.daily_frame, text="Today's Usage", padding="10")
        daily_stats_frame.pack(fill='x', pady=(0, 10))
        
        self.daily_labels = {}
        daily_items = [
            ("daily_cost", "Cost", "$0.00"),
            ("daily_requests", "Requests", "0"),
            ("daily_input_tokens", "Input Tokens", "0"),
            ("daily_output_tokens", "Output Tokens", "0"),
            ("daily_total_tokens", "Total Tokens", "0"),
            ("daily_avg_cost", "Avg Cost/Request", "$0.00")
        ]
        
        for i, (key, label, default) in enumerate(daily_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(daily_stats_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=row, column=col*2, sticky='w', padx=(0, 5), pady=3
            )
            
            self.daily_labels[key] = ttk.Label(daily_stats_frame, text=default)
            self.daily_labels[key].grid(
                row=row, column=col*2+1, sticky='w', padx=(0, 30), pady=3
            )
        
        # Daily progress frame
        daily_progress_frame = ttk.LabelFrame(self.daily_frame, text="Daily Limits Progress", padding="10")
        daily_progress_frame.pack(fill='x', pady=(0, 10))
        
        # Daily cost progress
        ttk.Label(daily_progress_frame, text="Cost Limit:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5
        )
        
        self.daily_cost_progress = ttk.Progressbar(
            daily_progress_frame, mode='determinate', length=300
        )
        self.daily_cost_progress.grid(row=0, column=1, sticky='ew', padx=(10, 5), pady=5)
        
        self.daily_cost_progress_label = ttk.Label(daily_progress_frame, text="0%")
        self.daily_cost_progress_label.grid(row=0, column=2, sticky='w', padx=(5, 0), pady=5)
        
        # Daily token progress
        ttk.Label(daily_progress_frame, text="Token Limit:", font=('Arial', 9, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5
        )
        
        self.daily_token_progress = ttk.Progressbar(
            daily_progress_frame, mode='determinate', length=300
        )
        self.daily_token_progress.grid(row=1, column=1, sticky='ew', padx=(10, 5), pady=5)
        
        self.daily_token_progress_label = ttk.Label(daily_progress_frame, text="0%")
        self.daily_token_progress_label.grid(row=1, column=2, sticky='w', padx=(5, 0), pady=5)
        
        daily_progress_frame.columnconfigure(1, weight=1)
        
        # Reset button
        ttk.Button(
            self.daily_frame, 
            text="Reset Daily Stats", 
            command=lambda: self.reset_stats("daily")
        ).pack(pady=10)
    
    def create_monthly_widgets(self):
        """Create monthly stats tab widgets."""
        
        # Monthly stats labels
        monthly_stats_frame = ttk.LabelFrame(self.monthly_frame, text="This Month's Usage", padding="10")
        monthly_stats_frame.pack(fill='x', pady=(0, 10))
        
        self.monthly_labels = {}
        monthly_items = [
            ("monthly_cost", "Cost", "$0.00"),
            ("monthly_requests", "Requests", "0"),
            ("monthly_input_tokens", "Input Tokens", "0"),
            ("monthly_output_tokens", "Output Tokens", "0"),
            ("monthly_total_tokens", "Total Tokens", "0"),
            ("monthly_avg_cost", "Avg Cost/Request", "$0.00")
        ]
        
        for i, (key, label, default) in enumerate(monthly_items):
            row = i // 2
            col = i % 2
            
            ttk.Label(monthly_stats_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=row, column=col*2, sticky='w', padx=(0, 5), pady=3
            )
            
            self.monthly_labels[key] = ttk.Label(monthly_stats_frame, text=default)
            self.monthly_labels[key].grid(
                row=row, column=col*2+1, sticky='w', padx=(0, 30), pady=3
            )
        
        # Monthly progress frame
        monthly_progress_frame = ttk.LabelFrame(self.monthly_frame, text="Monthly Limits Progress", padding="10")
        monthly_progress_frame.pack(fill='x', pady=(0, 10))
        
        # Monthly cost progress
        ttk.Label(monthly_progress_frame, text="Cost Limit:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5
        )
        
        self.monthly_cost_progress = ttk.Progressbar(
            monthly_progress_frame, mode='determinate', length=300
        )
        self.monthly_cost_progress.grid(row=0, column=1, sticky='ew', padx=(10, 5), pady=5)
        
        self.monthly_cost_progress_label = ttk.Label(monthly_progress_frame, text="0%")
        self.monthly_cost_progress_label.grid(row=0, column=2, sticky='w', padx=(5, 0), pady=5)
        
        # Monthly token progress
        ttk.Label(monthly_progress_frame, text="Token Limit:", font=('Arial', 9, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5
        )
        
        self.monthly_token_progress = ttk.Progressbar(
            monthly_progress_frame, mode='determinate', length=300
        )
        self.monthly_token_progress.grid(row=1, column=1, sticky='ew', padx=(10, 5), pady=5)
        
        self.monthly_token_progress_label = ttk.Label(monthly_progress_frame, text="0%")
        self.monthly_token_progress_label.grid(row=1, column=2, sticky='w', padx=(5, 0), pady=5)
        
        monthly_progress_frame.columnconfigure(1, weight=1)
        
        # Reset button
        ttk.Button(
            self.monthly_frame, 
            text="Reset Monthly Stats", 
            command=lambda: self.reset_stats("monthly")
        ).pack(pady=10)
    
    def create_limits_widgets(self):
        """Create limits tab widgets."""
        
        # Current limits frame
        limits_info_frame = ttk.LabelFrame(self.limits_frame, text="Current Limits", padding="10")
        limits_info_frame.pack(fill='x', pady=(0, 10))
        
        self.limits_labels = {}
        limits_items = [
            ("daily_cost_limit", "Daily Cost Limit", "Not set"),
            ("monthly_cost_limit", "Monthly Cost Limit", "Not set"),
            ("daily_token_limit", "Daily Token Limit", "Not set"),
            ("monthly_token_limit", "Monthly Token Limit", "Not set"),
            ("warning_threshold", "Warning Threshold", "80%")
        ]
        
        for i, (key, label, default) in enumerate(limits_items):
            ttk.Label(limits_info_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=i, column=0, sticky='w', padx=(0, 10), pady=3
            )
            
            self.limits_labels[key] = ttk.Label(limits_info_frame, text=default)
            self.limits_labels[key].grid(row=i, column=1, sticky='w', pady=3)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.limits_frame, text="Status", padding="10")
        status_frame.pack(fill='x', pady=(0, 10))
        
        self.status_text = tk.Text(
            status_frame, 
            wrap='word', 
            height=8,
            state='disabled',
            font=('Arial', 9)
        )
        self.status_text.pack(fill='both', expand=True)
        
        # Warnings frame
        warnings_frame = ttk.LabelFrame(self.limits_frame, text="Warnings & Alerts", padding="10")
        warnings_frame.pack(fill='both', expand=True)
        
        self.warnings_text = tk.Text(
            warnings_frame, 
            wrap='word', 
            height=6,
            state='disabled',
            font=('Arial', 9)
        )
        self.warnings_text.pack(fill='both', expand=True)
    
    def setup_layout(self):
        """Setup widget layout."""
        self.main_frame.pack(fill='both', expand=True)
        self.title_label.pack(pady=(0, 10))
        self.notebook.pack(fill='both', expand=True, pady=(0, 10))
        self.controls_frame.pack(fill='x')
    
    def center_window(self):
        """Center the window on the parent."""
        self.window.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def refresh_data(self):
        """Refresh all data."""
        try:
            summary = self.billing_monitor.get_usage_summary()
            self.update_overview(summary)
            self.update_daily_stats(summary)
            self.update_monthly_stats(summary)
            self.update_limits_info(summary)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")
    
    def update_overview(self, summary: Dict[str, Any]):
        """Update overview tab."""
        
        # Update summary labels
        self.summary_labels["total_cost"].config(text=f"${summary.get('total_cost', 0):.4f}")
        self.summary_labels["total_requests"].config(text=f"{summary.get('total_requests', 0):,}")
        self.summary_labels["total_input_tokens"].config(text=f"{summary.get('total_input_tokens', 0):,}")
        self.summary_labels["total_output_tokens"].config(text=f"{summary.get('total_output_tokens', 0):,}")
        
        # Calculate average cost per request
        total_requests = summary.get('total_requests', 0)
        if total_requests > 0:
            avg_cost = summary.get('total_cost', 0) / total_requests
            self.summary_labels["avg_cost_per_request"].config(text=f"${avg_cost:.4f}")
        else:
            self.summary_labels["avg_cost_per_request"].config(text="$0.00")
        
        # Update last request time
        last_reset = summary.get('last_reset_date', '')
        if last_reset:
            try:
                last_time = datetime.fromisoformat(last_reset)
                self.summary_labels["last_request"].config(text=last_time.strftime('%Y-%m-%d %H:%M:%S'))
            except:
                self.summary_labels["last_request"].config(text="Unknown")
        else:
            self.summary_labels["last_request"].config(text="Never")
        
        # Update activity log
        self.update_activity_log()
    
    def update_daily_stats(self, summary: Dict[str, Any]):
        """Update daily stats tab."""
        
        daily_requests = summary.get('daily_requests', 0)
        daily_cost = summary.get('daily_cost', 0)
        daily_input_tokens = summary.get('daily_input_tokens', 0)
        daily_output_tokens = summary.get('daily_output_tokens', 0)
        daily_total_tokens = daily_input_tokens + daily_output_tokens
        
        self.daily_labels["daily_cost"].config(text=f"${daily_cost:.4f}")
        self.daily_labels["daily_requests"].config(text=f"{daily_requests:,}")
        self.daily_labels["daily_input_tokens"].config(text=f"{daily_input_tokens:,}")
        self.daily_labels["daily_output_tokens"].config(text=f"{daily_output_tokens:,}")
        self.daily_labels["daily_total_tokens"].config(text=f"{daily_total_tokens:,}")
        
        # Calculate average daily cost
        if daily_requests > 0:
            avg_daily_cost = daily_cost / daily_requests
            self.daily_labels["daily_avg_cost"].config(text=f"${avg_daily_cost:.4f}")
        else:
            self.daily_labels["daily_avg_cost"].config(text="$0.00")
        
        # Update daily progress bars
        self.update_daily_progress(summary)
    
    def update_monthly_stats(self, summary: Dict[str, Any]):
        """Update monthly stats tab."""
        
        monthly_requests = summary.get('monthly_requests', 0)
        monthly_cost = summary.get('monthly_cost', 0)
        monthly_input_tokens = summary.get('monthly_input_tokens', 0)
        monthly_output_tokens = summary.get('monthly_output_tokens', 0)
        monthly_total_tokens = monthly_input_tokens + monthly_output_tokens
        
        self.monthly_labels["monthly_cost"].config(text=f"${monthly_cost:.4f}")
        self.monthly_labels["monthly_requests"].config(text=f"{monthly_requests:,}")
        self.monthly_labels["monthly_input_tokens"].config(text=f"{monthly_input_tokens:,}")
        self.monthly_labels["monthly_output_tokens"].config(text=f"{monthly_output_tokens:,}")
        self.monthly_labels["monthly_total_tokens"].config(text=f"{monthly_total_tokens:,}")
        
        # Calculate average monthly cost
        if monthly_requests > 0:
            avg_monthly_cost = monthly_cost / monthly_requests
            self.monthly_labels["monthly_avg_cost"].config(text=f"${avg_monthly_cost:.4f}")
        else:
            self.monthly_labels["monthly_avg_cost"].config(text="$0.00")
        
        # Update monthly progress bars
        self.update_monthly_progress(summary)
    
    def update_limits_info(self, summary: Dict[str, Any]):
        """Update limits tab."""
        
        # Update limits labels
        daily_cost_limit = summary.get('daily_cost_limit')
        monthly_cost_limit = summary.get('monthly_cost_limit')
        daily_token_limit = summary.get('daily_token_limit')
        monthly_token_limit = summary.get('monthly_token_limit')
        
        self.limits_labels["daily_cost_limit"].config(
            text=f"${daily_cost_limit:.2f}" if daily_cost_limit else "Not set"
        )
        self.limits_labels["monthly_cost_limit"].config(
            text=f"${monthly_cost_limit:.2f}" if monthly_cost_limit else "Not set"
        )
        self.limits_labels["daily_token_limit"].config(
            text=f"{daily_token_limit:,}" if daily_token_limit else "Not set"
        )
        self.limits_labels["monthly_token_limit"].config(
            text=f"{monthly_token_limit:,}" if monthly_token_limit else "Not set"
        )
        
        # Update status
        self.update_status_text(summary)
        
        # Update warnings
        self.update_warnings_text(summary)
    
    def update_daily_progress(self, summary: Dict[str, Any]):
        """Update daily progress bars."""
        
        # Daily cost progress
        daily_cost_limit = summary.get('daily_cost_limit')
        if daily_cost_limit:
            daily_cost_percent = summary.get('daily_cost_usage_percent', 0)
            self.daily_cost_progress['value'] = min(daily_cost_percent, 100)
            self.daily_cost_progress_label.config(text=f"{daily_cost_percent:.1f}%")
        else:
            self.daily_cost_progress['value'] = 0
            self.daily_cost_progress_label.config(text="No limit")
        
        # Daily token progress
        daily_token_limit = summary.get('daily_token_limit')
        if daily_token_limit:
            daily_token_percent = summary.get('daily_token_usage_percent', 0)
            self.daily_token_progress['value'] = min(daily_token_percent, 100)
            self.daily_token_progress_label.config(text=f"{daily_token_percent:.1f}%")
        else:
            self.daily_token_progress['value'] = 0
            self.daily_token_progress_label.config(text="No limit")
    
    def update_monthly_progress(self, summary: Dict[str, Any]):
        """Update monthly progress bars."""
        
        # Monthly cost progress
        monthly_cost_limit = summary.get('monthly_cost_limit')
        if monthly_cost_limit:
            monthly_cost_percent = summary.get('monthly_cost_usage_percent', 0)
            self.monthly_cost_progress['value'] = min(monthly_cost_percent, 100)
            self.monthly_cost_progress_label.config(text=f"{monthly_cost_percent:.1f}%")
        else:
            self.monthly_cost_progress['value'] = 0
            self.monthly_cost_progress_label.config(text="No limit")
        
        # Monthly token progress
        monthly_token_limit = summary.get('monthly_token_limit')
        if monthly_token_limit:
            monthly_token_percent = summary.get('monthly_token_usage_percent', 0)
            self.monthly_token_progress['value'] = min(monthly_token_percent, 100)
            self.monthly_token_progress_label.config(text=f"{monthly_token_percent:.1f}%")
        else:
            self.monthly_token_progress['value'] = 0
            self.monthly_token_progress_label.config(text="No limit")
    
    def update_activity_log(self):
        """Update activity log."""
        self.activity_text.config(state='normal')
        self.activity_text.delete(1.0, tk.END)
        
        # This would show recent API calls if we tracked them
        activity_log = f"""Activity Log (Last 10 requests):

[{datetime.now().strftime('%H:%M:%S')}] System initialized
[{datetime.now().strftime('%H:%M:%S')}] Billing monitor enabled
[{datetime.now().strftime('%H:%M:%S')}] Configuration loaded

Note: Detailed request logging not yet implemented.
Enable request tracking in configuration to see individual API calls here."""
        
        self.activity_text.insert(1.0, activity_log)
        self.activity_text.config(state='disabled')
    
    def update_status_text(self, summary: Dict[str, Any]):
        """Update status text."""
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        
        status_info = f"""Monitoring Status: {'Enabled' if self.billing_monitor.is_enabled() else 'Disabled'}
Configuration Auto-save: {'Enabled' if self.billing_monitor.config.auto_save else 'Disabled'}

Daily Usage: {summary.get('daily_cost_usage_percent', 0):.1f}% of limit
Monthly Usage: {summary.get('monthly_cost_usage_percent', 0):.1f}% of limit

Last Daily Reset: {summary.get('last_daily_reset', 'Unknown')}
Last Monthly Reset: {summary.get('last_monthly_reset', 'Unknown')}

Total Models Configured: {len(self.billing_monitor.config.models)}"""
        
        self.status_text.insert(1.0, status_info)
        self.status_text.config(state='disabled')
    
    def update_warnings_text(self, summary: Dict[str, Any]):
        """Update warnings text."""
        self.warnings_text.config(state='normal')
        self.warnings_text.delete(1.0, tk.END)
        
        warnings_text = "Current Warnings:\n\n"
        
        # Check for warnings based on usage percentages
        daily_cost_percent = summary.get('daily_cost_usage_percent', 0)
        monthly_cost_percent = summary.get('monthly_cost_usage_percent', 0)
        daily_token_percent = summary.get('daily_token_usage_percent', 0)
        monthly_token_percent = summary.get('monthly_token_usage_percent', 0)
        
        warnings_found = False
        
        if daily_cost_percent >= 100:
            warnings_text += "🔴 CRITICAL: Daily cost limit exceeded!\n"
            warnings_found = True
        elif daily_cost_percent >= 80:
            warnings_text += "🟡 WARNING: Daily cost approaching limit\n"
            warnings_found = True
        
        if monthly_cost_percent >= 100:
            warnings_text += "🔴 CRITICAL: Monthly cost limit exceeded!\n"
            warnings_found = True
        elif monthly_cost_percent >= 80:
            warnings_text += "🟡 WARNING: Monthly cost approaching limit\n"
            warnings_found = True
        
        if daily_token_percent >= 100:
            warnings_text += "🔴 CRITICAL: Daily token limit exceeded!\n"
            warnings_found = True
        elif daily_token_percent >= 80:
            warnings_text += "🟡 WARNING: Daily tokens approaching limit\n"
            warnings_found = True
        
        if monthly_token_percent >= 100:
            warnings_text += "🔴 CRITICAL: Monthly token limit exceeded!\n"
            warnings_found = True
        elif monthly_token_percent >= 80:
            warnings_text += "🟡 WARNING: Monthly tokens approaching limit\n"
            warnings_found = True
        
        if not warnings_found:
            warnings_text += "✅ No warnings - all usage within limits"
        
        self.warnings_text.insert(1.0, warnings_text)
        self.warnings_text.config(state='disabled')
    
    def start_auto_refresh(self):
        """Start auto-refresh thread."""
        if self.auto_refresh.get() and not self.refresh_running:
            self.refresh_running = True
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Stop auto-refresh thread."""
        self.refresh_running = False
    
    def _auto_refresh_loop(self):
        """Auto-refresh loop."""
        while self.refresh_running and self.auto_refresh.get():
            time.sleep(self.refresh_interval.get())
            if self.refresh_running:
                self.window.after(0, self.refresh_data)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh."""
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def reset_stats(self, reset_type: str):
        """Reset statistics."""
        if messagebox.askyesno("Confirm Reset", f"Reset {reset_type} statistics?"):
            try:
                self.billing_monitor.reset_usage_stats(reset_type)
                messagebox.showinfo("Success", f"{reset_type.title()} statistics reset successfully.")
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset statistics: {e}")
    
    def export_data(self):
        """Export statistics data."""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.asksaveasfilename(
                title="Export Statistics",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                summary = self.billing_monitor.get_usage_summary()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
                
                messagebox.showinfo("Success", f"Statistics exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def on_closing(self):
        """Handle window closing."""
        self.stop_auto_refresh()
        self.window.destroy()
