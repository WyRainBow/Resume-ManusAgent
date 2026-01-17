#!/bin/bash

# OpenManus 后端启动脚本（使用 conda）

set -e

PROJECT_DIR="/Users/wy770/Resume_OpenMauns/OpenManus"
CONDA_ENV="openmanus"

echo "========================================"
echo "  OpenManus 后端启动脚本"
echo "========================================"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 激活 conda 环境
eval "$(conda shell.bash hook)"
conda activate ${CONDA_ENV}

# 设置 PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

echo "启动后端服务..."
echo "访问地址: http://localhost:8080"
echo "API 文档: http://localhost:8080/docs"
echo "按 Ctrl+C 停止服务"
echo "========================================"

# 启动后端
python -m uvicorn app.web.server:app --host 0.0.0.0 --port 8080 --reload
