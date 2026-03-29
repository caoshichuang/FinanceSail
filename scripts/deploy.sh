#!/bin/bash
# FinanceSail 自动部署脚本（简化版）

set -e

PROJECT_DIR="/home/admin/redbook-auto"

echo "========================================="
echo "FinanceSail 部署开始"
echo "========================================="

cd $PROJECT_DIR

# 1. 重启服务
echo "[1/2] 重启服务..."
pkill -f "src.main" || true
sleep 1
export PATH=$PATH:/home/admin/.local/bin
screen -dmS redbook bash -c 'export PATH=$PATH:/home/admin/.local/bin && cd /home/admin/redbook-auto && python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080'

# 2. 检查服务状态
echo "[2/2] 检查服务状态..."
sleep 5
ps aux | grep "src.main" | grep -v grep || echo "服务启动中..."
curl -s http://localhost:8080/api/health || echo "服务启动中..."

echo "========================================="
echo "FinanceSail 部署完成！"
echo "========================================="
echo "访问地址：http://139.224.40.205:8080"
echo "========================================="
curl -s http://localhost:8080/api/health
