# OpenManus 安装和运行指南

## 重要提示

**你当前在 `base` 环境中运行，需要切换到 `openmanus` 环境！**

## 步骤 1: 激活正确的 conda 环境

```bash
# 激活 openmanus 环境
conda activate openmanus

# 验证环境
python --version  # 应该显示 Python 3.12.x
which python      # 应该显示 /Users/wy770/miniconda3/envs/openmanus/bin/python
```

## 步骤 2: 安装所有依赖

```bash
# 确保在 openmanus 环境中
conda activate openmanus

# 安装所有 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（如果需要浏览器功能）
playwright install
```

## 步骤 3: 安装缺失的依赖（如果还有错误）

如果运行时提示缺少某个模块，运行：

```bash
conda activate openmanus
pip install <缺失的模块名>
```

常见缺失的模块：
- `structlog`
- `markdownify`
- `docker`
- `browser-use` (注意：包名是 browser-use，导入时是 browser_use)

## 步骤 4: 运行项目

```bash
# 确保在 openmanus 环境中
conda activate openmanus

# 运行主程序
python main.py
```

## 快速安装脚本

如果遇到问题，可以运行：

```bash
chmod +x quick_install.sh
./quick_install.sh
```

## 常见问题

### 问题 1: ModuleNotFoundError
**原因**: 在错误的 conda 环境中运行，或依赖未安装
**解决**:
```bash
conda activate openmanus
pip install -r requirements.txt
```

### 问题 2: 仍然在 base 环境
**解决**: 每次打开新终端都需要激活环境
```bash
conda activate openmanus
```

### 问题 3: 配置文件错误
**解决**: 确保 `config/config.toml` 文件存在且配置正确

## 验证安装

运行以下命令验证关键模块是否已安装：

```bash
conda activate openmanus
python -c "
import sys
modules = ['pydantic', 'openai', 'browser_use', 'playwright', 'docker', 'structlog', 'markdownify']
missing = []
for mod in modules:
    try:
        __import__(mod.replace('-', '_'))
        print(f'✓ {mod}')
    except ImportError:
        print(f'✗ {mod} (缺失)')
        missing.append(mod)

if missing:
    print(f'\n缺失的模块: {missing}')
    sys.exit(1)
else:
    print('\n所有关键模块已安装!')
"
```

