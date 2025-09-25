# Copilot Instructions for OpenAI Billing Monitor

## 项目概述

这是一个用于监控和控制 OpenAI API 成本的 Python 库，提供三种集成方式：装饰器、包装器和手动监控。核心特点是低侵入式集成和实时成本控制。

## 核心架构

### 主要组件
- **BillingMonitor** (`core/billing_monitor.py`) - 核心监控器，处理使用跟踪和限制执行
- **OpenAIWrapper** (`core/wrapper.py`) - OpenAI 客户端包装器，透明集成
- **monitor_openai_call** (`core/decorators.py`) - 装饰器，最小侵入式集成
- **ConfigManager** (`config/manager.py`) - 配置持久化管理器
- **Pydantic Models** (`models/billing_models.py`) - 强类型数据模型

### 数据流
1. API 调用 → 装饰器/包装器拦截
2. 提取 token 使用量 → BillingMonitor.track_usage()
3. 计算成本 → 更新统计 → 检查阈值
4. 超限则抛出 ThresholdExceededException
5. 配置和统计自动持久化到 YAML/JSON

## 关键开发模式

### 配置管理模式
配置存储在 `~/.openai_billing/` 目录：
```python
# 配置文件自动创建，支持热重载
config_manager = ConfigManager()
config = config_manager.load_config()  # 自动加载或创建默认配置
```

### 三层集成策略
```python
# 1. 装饰器方式（推荐，最低侵入）
@monitor_openai_call(model_name="gpt-4")
def my_api_call(messages):
    return client.chat.completions.create(...)

# 2. 包装器方式（完全透明）
client = OpenAIWrapper(api_key="...")
response = client.chat.completions.create(...)  # 自动监控

# 3. 手动方式（最大控制）
monitor = BillingMonitor()
usage_info = monitor.track_openai_response(response.model_dump(), "gpt-4")
```

### 异常处理策略
项目使用自定义异常层次：
- `BillingException` - 基类
- `ThresholdExceededException` - 超限异常（可配置是否抛出）
- `ModelNotConfiguredException` - 模型未配置异常

### Pydantic 数据验证
所有配置和统计使用 Pydantic 模型：
```python
# 强类型验证，自动序列化/反序列化
model_config = ModelConfig(
    name="gpt-4",
    input_token_price=0.03,
    output_token_price=0.06
)
```

## GUI 架构

GUI 使用 tkinter 构建，采用模块化窗口设计：
- **main.py** - 主窗口和自动刷新逻辑
- **config_window.py** - 配置管理窗口
- **stats_window.py** - 统计详情窗口

GUI 启动方式：`python -m openai_billing.gui.main`

## 开发工作流

### 测试和调试
- 运行基本测试：`python test_basic.py`
- GUI 测试：`python start_gui.py`
- 示例代码在 `examples/` 目录

### 构建和发布
- 使用 setuptools 和 pyproject.toml
- 控制台脚本：`openai-billing-gui`
- 可选依赖：`gui` (tkinter), `dev` (测试工具)

### 配置文件位置
- 配置：`~/.openai_billing/openai_billing_config.yaml`
- 统计：`~/.openai_billing/openai_billing_stats.json`
- 默认模型配置在 `config/default_configs.py`

## 代码约定

### 模块导入顺序
遵循标准 Python 导入顺序：标准库 → 第三方 → 项目内部

### 错误处理
- 监控可选：通过 `enabled` 配置控制
- 优雅降级：未配置模型时警告但继续
- 阈值检查：支持软警告和硬限制

### 类型提示
项目广泛使用类型提示，配置了 mypy 静态检查。

### 文档字符串
使用 Google 风格文档字符串，包含参数、返回值和异常说明。

## 扩展点

### 添加新模型
在 `config/default_configs.py` 中添加预定义配置：
```python
"new-model": ModelConfig(
    name="new-model",
    input_token_price=0.01,
    output_token_price=0.02
)
```

### 自定义 Token 计数
重写 `TokenCounter` 类或注入自定义计数逻辑。

### 回调机制
BillingMonitor 支持事件回调：
```python
monitor.on_threshold_warning = lambda event, data: ...
monitor.on_threshold_exceeded = lambda event, data: ...
```