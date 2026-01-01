#!/bin/bash

# OpenManus Web 服务器启动脚本

# 确保在 openmanus 环境中运行
if [[ "$CONDA_DEFAULT_ENV" != "openmanus" ]]; then
    echo "⚠️  请先激活 'openmanus' conda 环境: conda activate openmanus"
    exit 1
fi

echo "========================================"
echo "  OpenManus Web 服务器启动脚本"
echo "========================================"

# 检查并安装必要的 Python 依赖
echo "--- 检查 Python 后端依赖 ---"
python -c "import fastapi, uvicorn, websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装缺失的 Python 依赖..."
    pip install fastapi uvicorn websockets markdownify
fi

# 检查 Node.js 和 npm
echo "--- 检查 Node.js 和 npm ---"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装。请安装 Node.js (推荐使用 nvm 或从官网下载): https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装。请安装 npm (通常随 Node.js 一起安装)。"
    exit 1
fi

# 检查前端是否已构建
echo "--- 检查前端构建 ---"
if [ ! -d "frontend/dist" ] || [ -z "$(ls -A frontend/dist 2>/dev/null)" ]; then
    echo "前端未构建，正在构建..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "✅ 前端构建完成"
else
    echo "✅ 前端已构建"
fi

# 设置 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 启动服务器
echo "========================================"
echo "  启动 Web 服务器..."
echo "========================================"
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务器"
echo "========================================"

python app/web/server.py
