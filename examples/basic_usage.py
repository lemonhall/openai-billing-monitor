"""
基本使用示例 - OpenAI Billing Monitor
"""

import os
import openai
from openai_billing import monitor_openai_call, OpenAIWrapper, BillingMonitor


def example_1_decorator():
    """示例1: 使用装饰器监控"""
    print("=== 示例1: 装饰器方式 ===")
    
    # 使用装饰器包装函数
    @monitor_openai_call(model_name="gpt-3.5-turbo")
    def chat_completion(messages):
        client = openai.OpenAI()
        return client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100
        )
    
    try:
        # 调用被监控的函数
        response = chat_completion([
            {"role": "user", "content": "Hello! How are you?"}
        ])
        print(f"Response: {response.choices[0].message.content}")
        
        # 查看使用统计
        monitor = BillingMonitor()
        summary = monitor.get_usage_summary()
        print(f"Total cost so far: ${summary['total_cost']:.4f}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_2_wrapper():
    """示例2: 使用包装器"""
    print("\n=== 示例2: 包装器方式 ===")
    
    try:
        # 创建包装的客户端
        client = OpenAIWrapper(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 正常使用，自动监控
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What's the weather like?"}
            ],
            max_tokens=50
        )
        
        print(f"Response: {response.choices[0].message.content}")
        
        # 查看使用统计
        summary = client.get_usage_summary()
        print(f"Daily cost: ${summary['daily_cost']:.4f}")
        print(f"Monthly cost: ${summary['monthly_cost']:.4f}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_3_manual_monitoring():
    """示例3: 手动监控"""
    print("\n=== 示例3: 手动监控 ===")
    
    try:
        # 创建监控器
        monitor = BillingMonitor()
        
        # 正常的OpenAI调用
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Tell me a joke"}
            ],
            max_tokens=100
        )
        
        # 手动跟踪使用
        usage_info = monitor.track_openai_response(
            response.model_dump(),
            "gpt-3.5-turbo"
        )
        
        print(f"Response: {response.choices[0].message.content}")
        print(f"This call cost: ${usage_info['cost']:.4f}")
        print(f"Input tokens: {usage_info['input_tokens']}")
        print(f"Output tokens: {usage_info['output_tokens']}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_4_configuration():
    """示例4: 配置管理"""
    print("\n=== 示例4: 配置管理 ===")
    
    try:
        from openai_billing.models import ThresholdConfig, ModelConfig
        
        monitor = BillingMonitor()
        
        # 设置阈值
        thresholds = ThresholdConfig(
            daily_cost_limit=5.0,       # $5 per day
            monthly_cost_limit=50.0,    # $50 per month
            warning_threshold=0.8       # 80% warning
        )
        monitor.config_manager.update_thresholds(thresholds)
        print("Updated thresholds")
        
        # 添加自定义模型
        custom_model = ModelConfig(
            name="my-custom-model",
            input_token_price=0.001,
            output_token_price=0.002,
            max_tokens=4096
        )
        monitor.config_manager.add_model_config(custom_model)
        print("Added custom model configuration")
        
        # 查看当前配置
        config = monitor.config
        print(f"Monitoring enabled: {config.enabled}")
        print(f"Models configured: {len(config.models)}")
        print(f"Daily cost limit: ${config.thresholds.daily_cost_limit}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_5_pre_check():
    """示例5: 预检查功能"""
    print("\n=== 示例5: 预检查功能 ===")
    
    try:
        monitor = BillingMonitor()
        
        # 检查请求是否会超限
        model_name = "gpt-3.5-turbo"
        estimated_tokens = 1000
        
        check_result = monitor.check_limits_before_request(model_name, estimated_tokens)
        
        print(f"Request allowed: {check_result['allowed']}")
        print(f"Estimated cost: ${check_result['estimated_cost']:.4f}")
        
        if check_result['allowed']:
            print("✅ Request can proceed")
        else:
            print("❌ Request blocked due to limits")
            for warning in check_result.get('warnings', []):
                print(f"  - {warning['message']}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_6_callbacks():
    """示例6: 回调函数"""
    print("\n=== 示例6: 回调函数 ===")
    
    try:
        monitor = BillingMonitor()
        
        # 设置回调函数
        def on_warning(warning_type, usage_info):
            print(f"⚠️  WARNING: {warning_type}")
            print(f"   Current daily cost: ${usage_info['daily_cost']:.4f}")
        
        def on_exceeded(exceeded_type, usage_info):
            print(f"🚫 LIMIT EXCEEDED: {exceeded_type}")
            print(f"   Blocking further requests")
        
        def on_usage_update(usage_info):
            print(f"📊 Usage update: +${usage_info['cost']:.4f}")
        
        # 注册回调
        monitor.on_threshold_warning = on_warning
        monitor.on_threshold_exceeded = on_exceeded
        monitor.on_usage_update = on_usage_update
        
        print("Callbacks registered. Try making some API calls to see them in action.")
        
    except Exception as e:
        print(f"Error: {e}")


def example_7_context_managers():
    """示例7: 上下文管理器"""
    print("\n=== 示例7: 上下文管理器 ===")
    
    try:
        from openai_billing.core.wrapper import temporary_monitoring, disable_monitoring
        
        client = openai.OpenAI()
        
        # 临时启用监控
        with temporary_monitoring():
            print("📊 Monitoring temporarily enabled")
            # API calls here will be monitored
        
        # 临时禁用监控
        with disable_monitoring():
            print("🚫 Monitoring temporarily disabled")
            # API calls here will NOT be monitored
        
        print("Context managers demo completed")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """运行所有示例"""
    print("OpenAI Billing Monitor - 使用示例")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
        print("某些示例可能无法正常运行")
        print()
    
    # 运行示例（注释掉需要API调用的部分以避免实际费用）
    example_4_configuration()  # 配置示例，不需要API调用
    example_5_pre_check()      # 预检查示例，不需要API调用
    example_6_callbacks()      # 回调示例，不需要API调用
    example_7_context_managers()  # 上下文管理器示例
    
    print("\n" + "=" * 50)
    print("示例完成!")
    print("\n取消注释其他示例来测试API调用功能")
    print("（注意：这将产生实际的API费用）")
    
    # 如果想测试实际的API调用，取消下面的注释：
    # example_1_decorator()
    # example_2_wrapper()
    # example_3_manual_monitoring()


if __name__ == "__main__":
    main()
