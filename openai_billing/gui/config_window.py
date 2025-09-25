"""
Configuration window for the billing monitor GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from ..core.billing_monitor import BillingMonitor
from ..models.billing_models import ModelConfig, ThresholdConfig
from ..config.default_configs import get_available_models


class ConfigWindow:
    """Configuration window for managing billing settings."""
    
    def __init__(self, parent: tk.Tk, billing_monitor: BillingMonitor):
        self.parent = parent
        self.billing_monitor = billing_monitor
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Billing Configuration")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Variables
        self.setup_variables()
        
        # Create widgets
        self.create_widgets()
        self.setup_layout()
        
        # Load current configuration
        self.load_configuration()
        
        # Center window
        self.center_window()
    
    def setup_variables(self):
        """Setup tkinter variables."""
        # General settings
        self.enabled_var = tk.BooleanVar()
        self.auto_save_var = tk.BooleanVar()
        
        # Threshold variables
        self.daily_cost_limit_var = tk.DoubleVar()
        self.monthly_cost_limit_var = tk.DoubleVar()
        self.daily_token_limit_var = tk.IntVar()
        self.monthly_token_limit_var = tk.IntVar()
        self.warning_threshold_var = tk.DoubleVar()
        
        # Enable/disable threshold variables
        self.daily_cost_enabled_var = tk.BooleanVar()
        self.monthly_cost_enabled_var = tk.BooleanVar()
        self.daily_token_enabled_var = tk.BooleanVar()
        self.monthly_token_enabled_var = tk.BooleanVar()
    
    def create_widgets(self):
        """Create all widgets."""
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        
        # General settings tab
        self.general_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.general_frame, text="General")
        
        # General settings
        ttk.Label(self.general_frame, text="General Settings", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Checkbutton(
            self.general_frame, 
            text="Enable billing monitoring", 
            variable=self.enabled_var
        ).pack(anchor='w', pady=2)
        
        ttk.Checkbutton(
            self.general_frame, 
            text="Auto-save configuration", 
            variable=self.auto_save_var
        ).pack(anchor='w', pady=2)
        
        # Thresholds tab
        self.thresholds_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.thresholds_frame, text="Thresholds")
        
        self.create_thresholds_widgets()
        
        # Models tab
        self.models_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.models_frame, text="Models")
        
        self.create_models_widgets()
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.window, padding="10")
        
        ttk.Button(
            self.buttons_frame, 
            text="Save", 
            command=self.save_configuration
        ).pack(side='right', padx=(5, 0))
        
        ttk.Button(
            self.buttons_frame, 
            text="Cancel", 
            command=self.window.destroy
        ).pack(side='right')
        
        ttk.Button(
            self.buttons_frame, 
            text="Reset to Defaults", 
            command=self.reset_to_defaults
        ).pack(side='left')
    
    def create_thresholds_widgets(self):
        """Create threshold configuration widgets."""
        
        ttk.Label(self.thresholds_frame, text="Usage Limits", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Daily cost limit
        daily_cost_frame = ttk.Frame(self.thresholds_frame)
        daily_cost_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(
            daily_cost_frame, 
            text="Daily cost limit ($):", 
            variable=self.daily_cost_enabled_var,
            command=self.toggle_daily_cost_limit
        ).pack(side='left')
        
        self.daily_cost_entry = ttk.Entry(
            daily_cost_frame, 
            textvariable=self.daily_cost_limit_var,
            width=10
        )
        self.daily_cost_entry.pack(side='right')
        
        # Monthly cost limit
        monthly_cost_frame = ttk.Frame(self.thresholds_frame)
        monthly_cost_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(
            monthly_cost_frame, 
            text="Monthly cost limit ($):", 
            variable=self.monthly_cost_enabled_var,
            command=self.toggle_monthly_cost_limit
        ).pack(side='left')
        
        self.monthly_cost_entry = ttk.Entry(
            monthly_cost_frame, 
            textvariable=self.monthly_cost_limit_var,
            width=10
        )
        self.monthly_cost_entry.pack(side='right')
        
        # Daily token limit
        daily_token_frame = ttk.Frame(self.thresholds_frame)
        daily_token_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(
            daily_token_frame, 
            text="Daily token limit:", 
            variable=self.daily_token_enabled_var,
            command=self.toggle_daily_token_limit
        ).pack(side='left')
        
        self.daily_token_entry = ttk.Entry(
            daily_token_frame, 
            textvariable=self.daily_token_limit_var,
            width=10
        )
        self.daily_token_entry.pack(side='right')
        
        # Monthly token limit
        monthly_token_frame = ttk.Frame(self.thresholds_frame)
        monthly_token_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(
            monthly_token_frame, 
            text="Monthly token limit:", 
            variable=self.monthly_token_enabled_var,
            command=self.toggle_monthly_token_limit
        ).pack(side='left')
        
        self.monthly_token_entry = ttk.Entry(
            monthly_token_frame, 
            textvariable=self.monthly_token_limit_var,
            width=10
        )
        self.monthly_token_entry.pack(side='right')
        
        # Warning threshold
        warning_frame = ttk.Frame(self.thresholds_frame)
        warning_frame.pack(fill='x', pady=5)
        
        ttk.Label(warning_frame, text="Warning threshold (%):").pack(side='left')
        
        ttk.Entry(
            warning_frame, 
            textvariable=self.warning_threshold_var,
            width=10
        ).pack(side='right')
    
    def create_models_widgets(self):
        """Create model configuration widgets."""
        
        ttk.Label(self.models_frame, text="Model Configurations", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Models list frame
        models_list_frame = ttk.Frame(self.models_frame)
        models_list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Treeview for models
        self.models_tree = ttk.Treeview(
            models_list_frame, 
            columns=('input_price', 'output_price', 'max_tokens'),
            show='tree headings',
            height=10
        )
        
        self.models_tree.heading('#0', text='Model Name')
        self.models_tree.heading('input_price', text='Input Price ($)')
        self.models_tree.heading('output_price', text='Output Price ($)')
        self.models_tree.heading('max_tokens', text='Max Tokens')
        
        self.models_tree.column('#0', width=150)
        self.models_tree.column('input_price', width=100)
        self.models_tree.column('output_price', width=100)
        self.models_tree.column('max_tokens', width=100)
        
        # Scrollbar for treeview
        models_scrollbar = ttk.Scrollbar(models_list_frame, orient='vertical', command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=models_scrollbar.set)
        
        self.models_tree.pack(side='left', fill='both', expand=True)
        models_scrollbar.pack(side='right', fill='y')
        
        # Buttons for model management
        models_buttons_frame = ttk.Frame(self.models_frame)
        models_buttons_frame.pack(fill='x')
        
        ttk.Button(
            models_buttons_frame, 
            text="Add Model", 
            command=self.add_model
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            models_buttons_frame, 
            text="Edit Model", 
            command=self.edit_model
        ).pack(side='left', padx=5)
        
        ttk.Button(
            models_buttons_frame, 
            text="Remove Model", 
            command=self.remove_model
        ).pack(side='left', padx=5)
        
        ttk.Button(
            models_buttons_frame, 
            text="Load Defaults", 
            command=self.load_default_models
        ).pack(side='right')
    
    def setup_layout(self):
        """Setup widget layout."""
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.buttons_frame.pack(fill='x', side='bottom')
    
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
    
    def load_configuration(self):
        """Load current configuration into the form."""
        config = self.billing_monitor.config
        
        # General settings
        self.enabled_var.set(config.enabled)
        self.auto_save_var.set(config.auto_save)
        
        # Thresholds
        thresholds = config.thresholds
        
        if thresholds.daily_cost_limit is not None:
            self.daily_cost_enabled_var.set(True)
            self.daily_cost_limit_var.set(thresholds.daily_cost_limit)
        else:
            self.daily_cost_enabled_var.set(False)
            self.daily_cost_limit_var.set(10.0)
        
        if thresholds.monthly_cost_limit is not None:
            self.monthly_cost_enabled_var.set(True)
            self.monthly_cost_limit_var.set(thresholds.monthly_cost_limit)
        else:
            self.monthly_cost_enabled_var.set(False)
            self.monthly_cost_limit_var.set(100.0)
        
        if thresholds.daily_token_limit is not None:
            self.daily_token_enabled_var.set(True)
            self.daily_token_limit_var.set(thresholds.daily_token_limit)
        else:
            self.daily_token_enabled_var.set(False)
            self.daily_token_limit_var.set(1000000)
        
        if thresholds.monthly_token_limit is not None:
            self.monthly_token_enabled_var.set(True)
            self.monthly_token_limit_var.set(thresholds.monthly_token_limit)
        else:
            self.monthly_token_enabled_var.set(False)
            self.monthly_token_limit_var.set(10000000)
        
        self.warning_threshold_var.set(thresholds.warning_threshold * 100)  # Convert to percentage
        
        # Update entry states
        self.toggle_daily_cost_limit()
        self.toggle_monthly_cost_limit()
        self.toggle_daily_token_limit()
        self.toggle_monthly_token_limit()
        
        # Load models
        self.load_models()
    
    def load_models(self):
        """Load models into the treeview."""
        # Clear existing items
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Add models
        for name, model_config in self.billing_monitor.config.models.items():
            self.models_tree.insert(
                '', 'end',
                text=name,
                values=(
                    f"{model_config.input_token_price:.6f}",
                    f"{model_config.output_token_price:.6f}",
                    model_config.max_tokens or "N/A"
                )
            )
    
    def toggle_daily_cost_limit(self):
        """Toggle daily cost limit entry."""
        if self.daily_cost_enabled_var.get():
            self.daily_cost_entry.config(state='normal')
        else:
            self.daily_cost_entry.config(state='disabled')
    
    def toggle_monthly_cost_limit(self):
        """Toggle monthly cost limit entry."""
        if self.monthly_cost_enabled_var.get():
            self.monthly_cost_entry.config(state='normal')
        else:
            self.monthly_cost_entry.config(state='disabled')
    
    def toggle_daily_token_limit(self):
        """Toggle daily token limit entry."""
        if self.daily_token_enabled_var.get():
            self.daily_token_entry.config(state='normal')
        else:
            self.daily_token_entry.config(state='disabled')
    
    def toggle_monthly_token_limit(self):
        """Toggle monthly token limit entry."""
        if self.monthly_token_enabled_var.get():
            self.monthly_token_entry.config(state='normal')
        else:
            self.monthly_token_entry.config(state='disabled')
    
    def add_model(self):
        """Add a new model configuration."""
        dialog = ModelConfigDialog(self.window, "Add Model")
        if dialog.result:
            model_config = dialog.result
            self.billing_monitor.config.add_model_config(model_config)
            self.load_models()
    
    def edit_model(self):
        """Edit selected model configuration."""
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model to edit.")
            return
        
        item = selection[0]
        model_name = self.models_tree.item(item, 'text')
        model_config = self.billing_monitor.config.get_model_config(model_name)
        
        if model_config:
            dialog = ModelConfigDialog(self.window, "Edit Model", model_config)
            if dialog.result:
                updated_config = dialog.result
                self.billing_monitor.config.add_model_config(updated_config)
                self.load_models()
    
    def remove_model(self):
        """Remove selected model configuration."""
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a model to remove.")
            return
        
        item = selection[0]
        model_name = self.models_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm Removal", f"Remove model '{model_name}' configuration?"):
            if model_name in self.billing_monitor.config.models:
                del self.billing_monitor.config.models[model_name]
                self.load_models()
    
    def load_default_models(self):
        """Load default model configurations."""
        if messagebox.askyesno("Confirm Load", "Load default model configurations? This will overwrite existing configurations."):
            from ..config.default_configs import get_default_model_configs
            default_configs = get_default_model_configs()
            self.billing_monitor.config.models.update(default_configs)
            self.load_models()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            # Reset to default values
            self.enabled_var.set(True)
            self.auto_save_var.set(True)
            
            self.daily_cost_enabled_var.set(True)
            self.daily_cost_limit_var.set(10.0)
            
            self.monthly_cost_enabled_var.set(True)
            self.monthly_cost_limit_var.set(100.0)
            
            self.daily_token_enabled_var.set(True)
            self.daily_token_limit_var.set(1000000)
            
            self.monthly_token_enabled_var.set(True)
            self.monthly_token_limit_var.set(10000000)
            
            self.warning_threshold_var.set(80.0)
            
            # Update entry states
            self.toggle_daily_cost_limit()
            self.toggle_monthly_cost_limit()
            self.toggle_daily_token_limit()
            self.toggle_monthly_token_limit()
    
    def save_configuration(self):
        """Save the configuration."""
        try:
            # Update general settings
            self.billing_monitor.config.enabled = self.enabled_var.get()
            self.billing_monitor.config.auto_save = self.auto_save_var.get()
            
            # Update thresholds
            thresholds = ThresholdConfig(
                daily_cost_limit=self.daily_cost_limit_var.get() if self.daily_cost_enabled_var.get() else None,
                monthly_cost_limit=self.monthly_cost_limit_var.get() if self.monthly_cost_enabled_var.get() else None,
                daily_token_limit=self.daily_token_limit_var.get() if self.daily_token_enabled_var.get() else None,
                monthly_token_limit=self.monthly_token_limit_var.get() if self.monthly_token_enabled_var.get() else None,
                warning_threshold=self.warning_threshold_var.get() / 100  # Convert from percentage
            )
            
            self.billing_monitor.config.thresholds = thresholds
            
            # Save configuration
            self.billing_monitor.config_manager.save_config(self.billing_monitor.config)
            
            messagebox.showinfo("Success", "Configuration saved successfully.")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")


class ModelConfigDialog:
    """Dialog for adding/editing model configurations."""
    
    def __init__(self, parent: tk.Toplevel, title: str, model_config: Optional[ModelConfig] = None):
        self.parent = parent
        self.model_config = model_config
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.name_var = tk.StringVar()
        self.input_price_var = tk.DoubleVar()
        self.output_price_var = tk.DoubleVar()
        self.max_tokens_var = tk.IntVar()
        self.max_tokens_enabled_var = tk.BooleanVar()
        
        # Create widgets
        self.create_widgets()
        
        # Load existing data if editing
        if model_config:
            self.load_model_config()
        
        # Center dialog
        self.center_dialog()
    
    def create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Model name
        ttk.Label(main_frame, text="Model Name:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Input token price
        ttk.Label(main_frame, text="Input Token Price ($/1000):").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.input_price_var, width=30).grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Output token price
        ttk.Label(main_frame, text="Output Token Price ($/1000):").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(main_frame, textvariable=self.output_price_var, width=30).grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Max tokens
        ttk.Checkbutton(
            main_frame, 
            text="Max Tokens:", 
            variable=self.max_tokens_enabled_var,
            command=self.toggle_max_tokens
        ).grid(row=3, column=0, sticky='w', pady=5)
        
        self.max_tokens_entry = ttk.Entry(main_frame, textvariable=self.max_tokens_var, width=30)
        self.max_tokens_entry.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Save", command=self.save).pack(side='right', padx=(5, 0))
        ttk.Button(buttons_frame, text="Cancel", command=self.dialog.destroy).pack(side='right')
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def toggle_max_tokens(self):
        """Toggle max tokens entry."""
        if self.max_tokens_enabled_var.get():
            self.max_tokens_entry.config(state='normal')
        else:
            self.max_tokens_entry.config(state='disabled')
    
    def load_model_config(self):
        """Load existing model configuration."""
        if self.model_config:
            self.name_var.set(self.model_config.name)
            self.input_price_var.set(self.model_config.input_token_price)
            self.output_price_var.set(self.model_config.output_token_price)
            
            if self.model_config.max_tokens is not None:
                self.max_tokens_enabled_var.set(True)
                self.max_tokens_var.set(self.model_config.max_tokens)
            else:
                self.max_tokens_enabled_var.set(False)
            
            self.toggle_max_tokens()
    
    def center_dialog(self):
        """Center the dialog on the parent."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def save(self):
        """Save the model configuration."""
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Model name is required.")
                return
            
            input_price = self.input_price_var.get()
            output_price = self.output_price_var.get()
            
            if input_price < 0 or output_price < 0:
                messagebox.showerror("Error", "Prices cannot be negative.")
                return
            
            max_tokens = None
            if self.max_tokens_enabled_var.get():
                max_tokens = self.max_tokens_var.get()
                if max_tokens <= 0:
                    messagebox.showerror("Error", "Max tokens must be positive.")
                    return
            
            self.result = ModelConfig(
                name=name,
                input_token_price=input_price,
                output_token_price=output_price,
                max_tokens=max_tokens
            )
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model configuration: {e}")
