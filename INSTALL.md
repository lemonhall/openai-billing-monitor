# 安装和使用指南

## 🚀 快速安装

### 从源码安装（开发版本）

```bash
# 克隆仓库
git clone https://github.com/lemonhall/openai-billing-monitor.git
cd openai-billing-monitor

# 安装依赖
pip install -r requirements.txt

# 安装包（开发模式）
pip install -e .
```

### 从PyPI安装（推荐）

```bash
pip install openai-billing-monitor
```

## 📋 系统要求

- Python 3.8 或更高版本
- 支持的操作系统：Windows、macOS、Linux

## 🔧 依赖包

核心依赖：
- `openai>=1.0.0` - OpenAI API客户端
- `pydantic>=2.0.0` - 数据验证和设置管理
- `pyyaml>=6.0` - YAML配置文件支持
- `tiktoken>=0.4.0` - Token计数

可选依赖：
- `tkinter` - GUI界面（通常随Python安装）

## 🎯 验证安装

运行以下命令验证安装是否成功：

```bash
# 测试基本功能
python -c "from openai_billing import BillingMonitor; print('✅ 安装成功!')"

# 启动GUI（如果支持）
openai-billing-gui
```

或者运行完整测试：

```bash
python test_basic.py
```

## 🔑 配置API密钥

### 方法1: 环境变量

```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# macOS/Linux
export OPENAI_API_KEY=your-api-key-here
```

### 方法2: 代码中设置

```python
from openai_billing import OpenAIWrapper

client = OpenAIWrapper(api_key="your-api-key-here")
```

## 🏃‍♂️ 快速开始

### 1. 基本使用

```python
from openai_billing import monitor_openai_call
import openai

@monitor_openai_call(model_name="gpt-3.5-turbo")
def chat_with_ai(message):
    client = openai.OpenAI()
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )

# 使用
response = chat_with_ai("Hello!")
```

### 2. 查看使用统计

```python
from openai_billing import BillingMonitor

monitor = BillingMonitor()
summary = monitor.get_usage_summary()
print(f"总成本: ${summary['total_cost']:.4f}")
```

### 3. 启动GUI

```bash
# 方式1: 使用Python模块启动（推荐）
python -m openai_billing.gui.main

# 方式2: 命令行工具（需要配置PATH）
openai-billing-gui

# 方式3: 在Python代码中启动
from openai_billing.gui import main
main()
```

**PATH配置说明**：
- **Windows**: 将 `%USERPROFILE%\AppData\Roaming\Python\Python3xx\Scripts` 添加到系统PATH
- **macOS/Linux**: 将 `~/.local/bin` 添加到PATH

如果遇到"命令未找到"错误，请使用方式1的Python模块启动。

## 🎛️ 配置文件位置

配置文件默认存储在：

- **Windows**: `%USERPROFILE%\.openai_billing\`
- **macOS**: `~/.openai_billing/`
- **Linux**: `~/.openai_billing/`

包含文件：
- `openai_billing_config.yaml` - 主配置文件
- `openai_billing_stats.json` - 使用统计数据

## 🔧 自定义配置目录

```python
from openai_billing.config import ConfigManager

# 自定义配置目录
config_manager = ConfigManager(config_dir="/path/to/custom/config")
```

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```bash
   pip install --upgrade openai-billing-monitor
   ```

2. **GUI无法启动**
   - 确保安装了tkinter：`python -m tkinter`
   - 在某些Linux发行版上需要：`sudo apt-get install python3-tk`
   - 使用Python模块方式启动：`python -m openai_billing.gui.main`

3. **Token计数错误**
   ```bash
   pip install --upgrade tiktoken
   ```

4. **配置文件权限问题**
   - 确保用户对配置目录有读写权限
   - 或使用自定义配置目录

### 获取帮助

- 📖 查看 [README.md](README.md) 了解详细使用说明
- 🐛 提交问题到 [Issues](https://github.com/lemonhall/openai-billing-monitor/issues)
- 💬 参与讨论 [Discussions](https://github.com/lemonhall/openai-billing-monitor/discussions)

## 📊 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 高级功能示例
python examples/advanced_usage.py

# GUI演示
python examples/gui_example.py

# 快速启动GUI
python start_gui.py
```

## 🔄 更新

```bash
# 从PyPI更新
pip install --upgrade openai-billing-monitor

# 从源码更新
git pull origin main
pip install -e .
```

## 🗑️ 卸载

```bash
pip uninstall openai-billing-monitor

# 删除配置文件（可选）
# Windows: rmdir /s %USERPROFILE%\.openai_billing
# macOS/Linux: rm -rf ~/.openai_billing
```

---

🎉 **安装完成！现在你可以开始监控和控制你的OpenAI API成本了。**
