#!/bin/bash

# OpenManus 前后端启动脚本（使用 conda）

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/wy770/Resume_OpenMauns/OpenManus"
CONDA_ENV="openmanus"

echo "========================================"
echo "  OpenManus 前后端启动脚本"
echo "========================================"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 检查并激活 conda 环境
echo -e "${YELLOW}[1/5]${NC} 检查 conda 环境..."
if ! conda env list | grep -q "^${CONDA_ENV}"; then
    echo -e "${RED}❌ Conda 环境 '${CONDA_ENV}' 不存在${NC}"
    echo -e "${YELLOW}正在创建 conda 环境...${NC}"
    conda create -n ${CONDA_ENV} python=3.11 -y
fi

# 激活 conda 环境
echo -e "${GREEN}✅ 激活 conda 环境: ${CONDA_ENV}${NC}"
eval "$(conda shell.bash hook)"
conda activate ${CONDA_ENV}

# 检查 Python 依赖
echo -e "${YELLOW}[2/5]${NC} 检查后端 Python 依赖..."
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}正在安装后端依赖...${NC}"
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ 后端依赖已安装${NC}"
fi

# 检查 Node.js 和 npm
echo -e "${YELLOW}[3/5]${NC} 检查 Node.js 和 npm..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装。请安装 Node.js (推荐使用 nvm 或从官网下载): https://nodejs.org/${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装。请安装 npm (通常随 Node.js 一起安装)。${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node --version) 和 npm $(npm --version) 已安装${NC}"

# 检查前端依赖
echo -e "${YELLOW}[4/5]${NC} 检查前端依赖..."
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}正在安装前端依赖...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✅ 前端依赖已安装${NC}"
fi

# 设置 PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

echo -e "${YELLOW}[5/5]${NC} 启动服务..."
echo "========================================"
echo -e "${GREEN}前端地址: http://localhost:5174${NC}"
echo -e "${GREEN}后端地址: http://localhost:8080${NC}"
echo -e "${GREEN}后端 API 文档: http://localhost:8080/docs${NC}"
echo "========================================"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止所有服务${NC}"
echo ""

# 创建一个函数来清理后台进程
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 服务已停止${NC}"
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM

# 启动后端（后台运行）
echo -e "${GREEN}🚀 启动后端服务 (端口 8080)...${NC}"
python -m uvicorn app.web.server:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端（后台运行）
echo -e "${GREEN}🚀 启动前端服务 (端口 5174)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待用户中断
echo ""
echo -e "${GREEN}✅ 前后端服务已启动！${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 等待后台进程
wait $BACKEND_PID $FRONTEND_PID
