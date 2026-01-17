#!/bin/bash

# OpenManus 前端启动脚本

set -e

PROJECT_DIR="/Users/wy770/Resume_OpenMauns/OpenManus"

echo "========================================"
echo "  OpenManus 前端启动脚本"
echo "========================================"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 检查 Node.js 和 npm
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装。请安装 Node.js"
    exit 1
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "正在安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

echo "启动前端服务..."
echo "访问地址: http://localhost:5174"
echo "按 Ctrl+C 停止服务"
echo "========================================"

# 进入前端目录并启动
cd frontend
npm run dev
