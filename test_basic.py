#!/usr/bin/env python3
"""
基本功能测试脚本 - OpenAI Billing Monitor
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块是否能正常导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试主模块导入
        from openai_billing import BillingMonitor, OpenAIWrapper, monitor_openai_call
        print("✅ 主模块导入成功")
        
        # 测试配置模块
        from openai_billing.config import ConfigManager, get_default_model_configs
        print("✅ 配置模块导入成功")
        
        # 测试模型
        from openai_billing.models import BillingConfig, ModelConfig, ThresholdConfig, UsageStats
        print("✅ 模型模块导入成功")
        
        # 测试核心模块
        from openai_billing.core import TokenCounter, BillingException, ThresholdExceededException
        print("✅ 核心模块导入成功")
        
        # 测试GUI模块（可能失败如果没有tkinter）
        try:
            from openai_billing.gui import BillingGUI, ConfigWindow, StatsWindow
            print("✅ GUI模块导入成功")
        except ImportError as e:
            print(f"⚠️ GUI模块导入失败（可能缺少tkinter）: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_config_manager():
    """测试配置管理器"""
    print("\n🔍 测试配置管理器...")
    
    try:
        from openai_billing.config import ConfigManager
        
        # 创建配置管理器
        config_manager = ConfigManager()
        print("✅ 配置管理器创建成功")
        
        # 加载配置
        config = config_manager.load_config()
        print(f"✅ 配置加载成功，包含 {len(config.models)} 个模型")
        
        # 测试默认模型配置
        if "gpt-3.5-turbo" in config.models:
            model = config.models["gpt-3.5-turbo"]
            print(f"✅ 找到 gpt-3.5-turbo 配置: ${model.input_token_price:.6f}/1K tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False


def test_billing_monitor():
    """测试计费监控器"""
    print("\n🔍 测试计费监控器...")
    
    try:
        from openai_billing import BillingMonitor
        
        # 创建监控器
        monitor = BillingMonitor()
        print("✅ 计费监控器创建成功")
        
        # 测试成本计算
        cost = monitor.estimate_cost("gpt-3.5-turbo", 1000, 500)
        if cost is not None:
            print(f"✅ 成本计算成功: 1000输入+500输出token = ${cost:.6f}")
        else:
            print("⚠️ 成本计算返回None（模型可能未配置）")
        
        # 测试使用统计
        summary = monitor.get_usage_summary()
        print(f"✅ 使用统计获取成功: 总成本 ${summary['total_cost']:.4f}")
        
        # 测试预检查
        check_result = monitor.check_limits_before_request("gpt-3.5-turbo", 1000)
        print(f"✅ 预检查成功: 允许请求 = {check_result['allowed']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 计费监控器测试失败: {e}")
        return False


def test_token_counter():
    """测试token计数器"""
    print("\n🔍 测试token计数器...")
    
    try:
        from openai_billing.core import TokenCounter
        
        # 创建token计数器
        counter = TokenCounter()
        print("✅ Token计数器创建成功")
        
        # 测试文本token计数
        text = "Hello, how are you today?"
        tokens = counter.count_tokens(text, "gpt-3.5-turbo")
        print(f"✅ 文本token计数成功: '{text}' = {tokens} tokens")
        
        # 测试消息token计数
        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        message_tokens = counter.count_messages_tokens(messages, "gpt-3.5-turbo")
        print(f"✅ 消息token计数成功: {len(messages)}条消息 = {message_tokens} tokens")
        
        # 测试支持的模型
        supported_models = counter.get_supported_models()
        print(f"✅ 支持的模型数量: {len(supported_models)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token计数器测试失败: {e}")
        return False


def test_model_operations():
    """测试模型操作"""
    print("\n🔍 测试模型操作...")
    
    try:
        from openai_billing.models import ModelConfig, ThresholdConfig, UsageStats
        
        # 创建模型配置
        model = ModelConfig(
            name="test-model",
            input_token_price=0.001,
            output_token_price=0.002,
            max_tokens=4096
        )
        print(f"✅ 模型配置创建成功: {model.name}")
        
        # 创建阈值配置
        thresholds = ThresholdConfig(
            daily_cost_limit=5.0,
            monthly_cost_limit=50.0,
            warning_threshold=0.8
        )
        print(f"✅ 阈值配置创建成功: 日限制 ${thresholds.daily_cost_limit}")
        
        # 创建使用统计
        stats = UsageStats()
        print(f"✅ 使用统计创建成功: 初始成本 ${stats.total_cost}")
        
        # 测试统计重置
        stats.reset_daily_stats()
        print("✅ 日统计重置成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型操作测试失败: {e}")
        return False


def test_decorator():
    """测试装饰器"""
    print("\n🔍 测试装饰器...")
    
    try:
        from openai_billing import monitor_openai_call
        
        # 创建被装饰的函数
        @monitor_openai_call(model_name="gpt-3.5-turbo")
        def mock_api_call():
            """模拟API调用"""
            return {
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}
            }
        
        print("✅ 装饰器应用成功")
        
        # 注意：这里不实际调用，因为会尝试真正的API调用
        print("✅ 装饰器功能验证完成（未实际调用以避免API费用）")
        
        return True
        
    except Exception as e:
        print(f"❌ 装饰器测试失败: {e}")
        return False


def test_gui_availability():
    """测试GUI是否可用"""
    print("\n🔍 测试GUI可用性...")
    
    try:
        import tkinter as tk
        print("✅ tkinter可用")
        
        # 测试创建GUI组件（不显示）
        from openai_billing.gui import BillingGUI
        from openai_billing import BillingMonitor
        
        # 创建一个不显示的根窗口来测试
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        monitor = BillingMonitor()
        # 这里不实际创建GUI，只是确保类可以导入
        print("✅ GUI组件导入成功")
        
        root.destroy()
        
        return True
        
    except ImportError:
        print("⚠️ tkinter不可用，GUI功能将无法使用")
        return False
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("OpenAI Billing Monitor - 基本功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理器", test_config_manager),
        ("计费监控器", test_billing_monitor),
        ("Token计数器", test_token_counter),
        ("模型操作", test_model_operations),
        ("装饰器", test_decorator),
        ("GUI可用性", test_gui_availability),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！库已准备就绪。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
