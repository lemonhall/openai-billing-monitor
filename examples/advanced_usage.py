"""
高级使用示例 - OpenAI Billing Monitor
"""

import os
import time
import asyncio
from typing import List, Dict, Any
import openai
from openai_billing import BillingMonitor, OpenAIWrapper, monitor_openai_call
from openai_billing.models import ModelConfig, ThresholdConfig
from openai_billing.core.exceptions import ThresholdExceededException


class ChatBot:
    """示例聊天机器人类，集成计费监控"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.client = OpenAIWrapper()
        self.conversation_history = []
        
        # 设置回调函数
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """设置监控回调"""
        def on_warning(warning_type, usage_info):
            print(f"💰 成本警告: {warning_type}")
            print(f"   当前日成本: ${usage_info['daily_cost']:.4f}")
        
        def on_exceeded(exceeded_type, usage_info):
            print(f"🚫 超出限制: {exceeded_type}")
            print(f"   停止服务以控制成本")
        
        self.client.set_threshold_callbacks(
            on_warning=on_warning,
            on_exceeded=on_exceeded
        )
    
    def chat(self, message: str) -> str:
        """聊天方法，自动监控成本"""
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                max_tokens=150
            )
            
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except ThresholdExceededException as e:
            return f"抱歉，已达到使用限制: {e}"
        except Exception as e:
            return f"发生错误: {e}"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.client.get_usage_summary()


class BatchProcessor:
    """批量处理示例，带有成本控制"""
    
    def __init__(self):
        self.monitor = BillingMonitor()
        self.client = openai.OpenAI()
    
    @monitor_openai_call()
    def process_single_item(self, text: str, model: str = "gpt-3.5-turbo") -> str:
        """处理单个项目"""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Summarize this text: {text}"}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content
    
    def process_batch(self, texts: List[str], model: str = "gpt-3.5-turbo") -> List[str]:
        """批量处理，带有成本控制"""
        results = []
        total_estimated_cost = 0
        
        for i, text in enumerate(texts):
            # 预估成本
            estimated_tokens = len(text.split()) * 1.3  # 粗略估算
            check_result = self.monitor.check_limits_before_request(model, int(estimated_tokens))
            
            if not check_result["allowed"]:
                print(f"⚠️ 第{i+1}个项目被跳过，原因: 超出限制")
                warnings = check_result.get("warnings", [])
                for warning in warnings:
                    print(f"   {warning['message']}")
                continue
            
            try:
                result = self.process_single_item(text, model)
                results.append(result)
                total_estimated_cost += check_result["estimated_cost"]
                
                print(f"✅ 处理完成第{i+1}/{len(texts)}个项目")
                print(f"   预估累计成本: ${total_estimated_cost:.4f}")
                
                # 添加延迟避免速率限制
                time.sleep(1)
                
            except ThresholdExceededException as e:
                print(f"🚫 处理第{i+1}个项目时超出限制: {e}")
                break
            except Exception as e:
                print(f"❌ 处理第{i+1}个项目时出错: {e}")
                continue
        
        return results


class ModelComparison:
    """模型成本比较工具"""
    
    def __init__(self):
        self.monitor = BillingMonitor()
    
    def compare_models(self, prompt: str, models: List[str]) -> Dict[str, Dict[str, Any]]:
        """比较不同模型的成本和响应"""
        results = {}
        
        for model in models:
            print(f"\n🔍 测试模型: {model}")
            
            # 检查模型是否配置
            model_config = self.monitor.config.get_model_config(model)
            if not model_config:
                print(f"⚠️ 模型 {model} 未配置，跳过")
                continue
            
            # 估算成本
            estimated_tokens = len(prompt.split()) * 1.5
            estimated_cost = self.monitor.estimate_cost(model, int(estimated_tokens), int(estimated_tokens))
            
            results[model] = {
                "estimated_cost": estimated_cost,
                "input_price": model_config.input_token_price,
                "output_price": model_config.output_token_price,
                "max_tokens": model_config.max_tokens
            }
            
            print(f"   预估成本: ${estimated_cost:.6f}")
            print(f"   输入价格: ${model_config.input_token_price:.6f}/1K tokens")
            print(f"   输出价格: ${model_config.output_token_price:.6f}/1K tokens")
        
        # 排序并显示最经济的选择
        if results:
            sorted_models = sorted(results.items(), key=lambda x: x[1]["estimated_cost"])
            print(f"\n💰 最经济的模型: {sorted_models[0][0]} (${sorted_models[0][1]['estimated_cost']:.6f})")
        
        return results


class CostTracker:
    """成本跟踪和报告工具"""
    
    def __init__(self):
        self.monitor = BillingMonitor()
    
    def generate_report(self) -> str:
        """生成使用报告"""
        summary = self.monitor.get_usage_summary()
        
        report = f"""
📊 OpenAI 使用报告
{'=' * 50}

💰 成本统计:
   总成本:     ${summary.get('total_cost', 0):.4f}
   今日成本:   ${summary.get('daily_cost', 0):.4f}
   本月成本:   ${summary.get('monthly_cost', 0):.4f}

🔢 Token统计:
   总输入:     {summary.get('total_input_tokens', 0):,}
   总输出:     {summary.get('total_output_tokens', 0):,}
   今日输入:   {summary.get('daily_input_tokens', 0):,}
   今日输出:   {summary.get('daily_output_tokens', 0):,}

📞 请求统计:
   总请求数:   {summary.get('total_requests', 0):,}

📅 时间信息:
   上次重置:   {summary.get('last_reset_date', 'N/A')}
   日重置:     {summary.get('last_daily_reset', 'N/A')}
   月重置:     {summary.get('last_monthly_reset', 'N/A')}

⚠️ 限制状态:
"""
        
        # 添加限制状态
        if summary.get('daily_cost_limit'):
            daily_percent = summary.get('daily_cost_usage_percent', 0)
            status = "🔴" if daily_percent >= 100 else "🟡" if daily_percent >= 80 else "🟢"
            report += f"   日成本限制: {status} {daily_percent:.1f}% (${summary['daily_cost_limit']:.2f})\n"
        
        if summary.get('monthly_cost_limit'):
            monthly_percent = summary.get('monthly_cost_usage_percent', 0)
            status = "🔴" if monthly_percent >= 100 else "🟡" if monthly_percent >= 80 else "🟢"
            report += f"   月成本限制: {status} {monthly_percent:.1f}% (${summary['monthly_cost_limit']:.2f})\n"
        
        return report
    
    def export_data(self, filename: str):
        """导出数据到文件"""
        import json
        
        summary = self.monitor.get_usage_summary()
        config_data = {
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "usage_summary": summary,
            "models_configured": list(self.monitor.config.models.keys()),
            "thresholds": {
                "daily_cost_limit": self.monitor.config.thresholds.daily_cost_limit,
                "monthly_cost_limit": self.monitor.config.thresholds.monthly_cost_limit,
                "daily_token_limit": self.monitor.config.thresholds.daily_token_limit,
                "monthly_token_limit": self.monitor.config.thresholds.monthly_token_limit,
                "warning_threshold": self.monitor.config.thresholds.warning_threshold,
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 数据已导出到: {filename}")


def example_chatbot():
    """示例: 聊天机器人"""
    print("\n=== 聊天机器人示例 ===")
    
    try:
        bot = ChatBot("gpt-3.5-turbo")
        
        # 模拟对话
        messages = [
            "Hello, how are you?",
            "What's the weather like?", 
            "Tell me a joke"
        ]
        
        for msg in messages:
            print(f"User: {msg}")
            response = bot.chat(msg)
            print(f"Bot: {response}")
            
            # 显示当前使用统计
            stats = bot.get_usage_stats()
            print(f"💰 当前成本: ${stats['daily_cost']:.4f}")
            print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")


def example_batch_processing():
    """示例: 批量处理"""
    print("\n=== 批量处理示例 ===")
    
    try:
        processor = BatchProcessor()
        
        # 示例文本列表
        texts = [
            "This is a long article about artificial intelligence and machine learning...",
            "Another piece of text that needs to be summarized for our project...",
            "The third document contains important information about data processing..."
        ]
        
        # 批量处理
        results = processor.process_batch(texts)
        
        print(f"\n✅ 处理完成，共{len(results)}个结果")
        for i, result in enumerate(results):
            print(f"{i+1}. {result}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_model_comparison():
    """示例: 模型比较"""
    print("\n=== 模型比较示例 ===")
    
    try:
        comparator = ModelComparison()
        
        prompt = "Explain the concept of machine learning in simple terms"
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]
        
        results = comparator.compare_models(prompt, models)
        
        print("\n📊 比较结果:")
        for model, data in results.items():
            print(f"{model}: ${data['estimated_cost']:.6f}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_cost_tracking():
    """示例: 成本跟踪"""
    print("\n=== 成本跟踪示例 ===")
    
    try:
        tracker = CostTracker()
        
        # 生成报告
        report = tracker.generate_report()
        print(report)
        
        # 导出数据
        tracker.export_data("usage_report.json")
        
    except Exception as e:
        print(f"Error: {e}")


def example_custom_configuration():
    """示例: 自定义配置"""
    print("\n=== 自定义配置示例 ===")
    
    try:
        monitor = BillingMonitor()
        
        # 添加自定义模型
        custom_models = [
            ModelConfig(
                name="claude-3-opus",
                input_token_price=0.015,
                output_token_price=0.075,
                max_tokens=200000
            ),
            ModelConfig(
                name="gemini-pro",
                input_token_price=0.0005,
                output_token_price=0.0015,
                max_tokens=32768
            )
        ]
        
        for model in custom_models:
            monitor.config_manager.add_model_config(model)
            print(f"✅ 添加模型配置: {model.name}")
        
        # 设置严格的限制
        strict_thresholds = ThresholdConfig(
            daily_cost_limit=1.0,        # 每日$1限制
            monthly_cost_limit=20.0,     # 每月$20限制
            daily_token_limit=100000,    # 每日10万token限制
            warning_threshold=0.7        # 70%警告
        )
        
        monitor.config_manager.update_thresholds(strict_thresholds)
        print("✅ 更新阈值配置")
        
        # 显示当前配置
        config = monitor.config
        print(f"\n📋 当前配置:")
        print(f"   模型数量: {len(config.models)}")
        print(f"   日成本限制: ${config.thresholds.daily_cost_limit}")
        print(f"   月成本限制: ${config.thresholds.monthly_cost_limit}")
        print(f"   警告阈值: {config.thresholds.warning_threshold*100}%")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """运行高级示例"""
    print("OpenAI Billing Monitor - 高级使用示例")
    print("=" * 60)
    
    # 运行不需要API调用的示例
    example_model_comparison()
    example_cost_tracking()
    example_custom_configuration()
    
    print("\n" + "=" * 60)
    print("高级示例完成!")
    print("\n取消注释其他示例来测试API调用功能")
    print("（注意：这将产生实际的API费用）")
    
    # 如果想测试实际的API调用，取消下面的注释：
    # example_chatbot()
    # example_batch_processing()


if __name__ == "__main__":
    main()
