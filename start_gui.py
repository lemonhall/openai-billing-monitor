#!/usr/bin/env python3
"""
快速启动OpenAI Billing Monitor GUI的脚本
"""

def main():
    """启动GUI"""
    try:
        from openai_billing.gui import main as gui_main
        print("正在启动OpenAI Billing Monitor GUI...")
        gui_main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装openai-billing-monitor:")
        print("pip install openai-billing-monitor")
    except Exception as e:
        print(f"启动GUI时出错: {e}")

if __name__ == "__main__":
    main()
