"""
GUI使用示例 - OpenAI Billing Monitor
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time

from openai_billing import BillingMonitor
from openai_billing.gui import BillingGUI
from openai_billing.models import ModelConfig, ThresholdConfig


def setup_demo_data():
    """设置演示数据"""
    monitor = BillingMonitor()
    
    # 添加一些模拟使用数据
    # 注意：这只是为了演示，实际使用中数据来自真实的API调用
    
    # 模拟一些使用
    monitor.config.usage_stats.total_cost = 15.75
    monitor.config.usage_stats.daily_cost = 2.30
    monitor.config.usage_stats.monthly_cost = 8.90
    monitor.config.usage_stats.total_requests = 45
    monitor.config.usage_stats.request_count = 45  # 保持同步
    monitor.config.usage_stats.daily_requests = 12
    monitor.config.usage_stats.monthly_requests = 28
    monitor.config.usage_stats.total_input_tokens = 12500
    monitor.config.usage_stats.total_output_tokens = 8300
    monitor.config.usage_stats.daily_input_tokens = 1800
    monitor.config.usage_stats.daily_output_tokens = 1200
    monitor.config.usage_stats.monthly_input_tokens = 5200
    monitor.config.usage_stats.monthly_output_tokens = 3400
    
    # 设置一些阈值用于演示
    thresholds = ThresholdConfig(
        daily_cost_limit=5.0,
        monthly_cost_limit=50.0,
        daily_token_limit=10000,
        monthly_token_limit=100000,
        warning_threshold=0.8
    )
    
    monitor.config.thresholds = thresholds
    
    # 保存配置
    monitor.config_manager.save_config(monitor.config)
    
    return monitor


def create_demo_window():
    """创建演示窗口"""
    
    def start_gui():
        """启动主GUI"""
        try:
            # 设置演示数据
            monitor = setup_demo_data()
            
            # 创建并运行GUI
            app = BillingGUI(monitor)
            app.run()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动GUI时出错: {e}")
    
    def start_gui_with_simulation():
        """启动GUI并模拟使用数据更新"""
        try:
            monitor = setup_demo_data()
            
            # 创建GUI
            app = BillingGUI(monitor)
            
            # 启动模拟数据更新线程
            def simulate_usage():
                """模拟使用数据变化"""
                import random
                
                while True:
                    time.sleep(10)  # 每10秒更新一次
                    
                    # 模拟新的API调用
                    cost_increase = random.uniform(0.01, 0.05)
                    token_increase = random.randint(50, 200)
                    
                    app.billing_monitor.config.usage_stats.daily_cost += cost_increase
                    app.billing_monitor.config.usage_stats.monthly_cost += cost_increase
                    app.billing_monitor.config.usage_stats.total_cost += cost_increase
                    
                    app.billing_monitor.config.usage_stats.daily_input_tokens += token_increase
                    app.billing_monitor.config.usage_stats.monthly_input_tokens += token_increase
                    app.billing_monitor.config.usage_stats.total_input_tokens += token_increase
                    
                    app.billing_monitor.config.usage_stats.request_count += 1
                    app.billing_monitor.config.usage_stats.total_requests += 1
                    app.billing_monitor.config.usage_stats.daily_requests += 1
                    app.billing_monitor.config.usage_stats.monthly_requests += 1
                    
                    # 保存更新
                    if app.billing_monitor.config.auto_save:
                        app.billing_monitor.config_manager.save_config(app.billing_monitor.config)
            
            # 启动模拟线程
            simulation_thread = threading.Thread(target=simulate_usage, daemon=True)
            simulation_thread.start()
            
            # 运行GUI
            app.run()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动GUI时出错: {e}")
    
    def show_config_only():
        """只显示配置窗口"""
        try:
            from openai_billing.gui.config_window import ConfigWindow
            
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            monitor = setup_demo_data()
            config_window = ConfigWindow(root, monitor)
            
            root.mainloop()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动配置窗口时出错: {e}")
    
    def show_stats_only():
        """只显示统计窗口"""
        try:
            from openai_billing.gui.stats_window import StatsWindow
            
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            monitor = setup_demo_data()
            stats_window = StatsWindow(root, monitor)
            
            root.mainloop()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动统计窗口时出错: {e}")
    
    # 创建演示选择窗口
    demo_root = tk.Tk()
    demo_root.title("OpenAI Billing Monitor - GUI演示")
    demo_root.geometry("400x300")
    demo_root.resizable(False, False)
    
    # 标题
    title_label = tk.Label(
        demo_root, 
        text="OpenAI Billing Monitor", 
        font=("Arial", 16, "bold"),
        pady=20
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        demo_root,
        text="选择要演示的GUI组件",
        font=("Arial", 10),
        pady=10
    )
    subtitle_label.pack()
    
    # 按钮框架
    button_frame = tk.Frame(demo_root)
    button_frame.pack(expand=True, fill="both", padx=40, pady=20)
    
    # 主GUI按钮
    main_gui_btn = tk.Button(
        button_frame,
        text="🖥️ 完整GUI界面",
        font=("Arial", 11),
        command=start_gui,
        height=2,
        bg="#4CAF50",
        fg="white",
        relief="raised"
    )
    main_gui_btn.pack(fill="x", pady=5)
    
    # 模拟数据GUI按钮
    sim_gui_btn = tk.Button(
        button_frame,
        text="📊 GUI + 实时数据模拟",
        font=("Arial", 11),
        command=start_gui_with_simulation,
        height=2,
        bg="#2196F3",
        fg="white",
        relief="raised"
    )
    sim_gui_btn.pack(fill="x", pady=5)
    
    # 配置窗口按钮
    config_btn = tk.Button(
        button_frame,
        text="⚙️ 配置窗口",
        font=("Arial", 11),
        command=show_config_only,
        height=2,
        bg="#FF9800",
        fg="white",
        relief="raised"
    )
    config_btn.pack(fill="x", pady=5)
    
    # 统计窗口按钮
    stats_btn = tk.Button(
        button_frame,
        text="📈 统计窗口",
        font=("Arial", 11),
        command=show_stats_only,
        height=2,
        bg="#9C27B0",
        fg="white",
        relief="raised"
    )
    stats_btn.pack(fill="x", pady=5)
    
    # 说明文本
    info_label = tk.Label(
        demo_root,
        text="注意：这些是演示界面，使用模拟数据\n实际使用时数据来自真实的API调用",
        font=("Arial", 8),
        fg="gray",
        pady=10
    )
    info_label.pack(side="bottom")
    
    return demo_root


def main():
    """主函数"""
    print("OpenAI Billing Monitor - GUI演示")
    print("=" * 40)
    print("启动GUI演示窗口...")
    
    try:
        # 创建并显示演示窗口
        demo_window = create_demo_window()
        demo_window.mainloop()
        
    except Exception as e:
        print(f"启动演示时出错: {e}")
        
        # 如果GUI启动失败，尝试直接启动基本GUI
        try:
            print("尝试启动基本GUI...")
            monitor = setup_demo_data()
            app = BillingGUI(monitor)
            app.run()
        except Exception as e2:
            print(f"启动基本GUI也失败: {e2}")
            print("请检查是否正确安装了tkinter")


if __name__ == "__main__":
    main()
