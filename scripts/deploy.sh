#!/bin/bash
# 代码同步并重启服务脚本

set -e

PROJECT_DIR="/home/admin/redbook-auto"
LOG_FILE="/tmp/redbook-auto.log"

echo "开始同步代码..."

cd $PROJECT_DIR

# 拉取最新代码
git pull origin main

# 重启服务
pkill -f "src.main" || true
sleep 1

export PATH=$PATH:/home/admin/.local/bin
nohup python3 -m src.main > $LOG_FILE 2>&1 &

sleep 2
ps aux | grep "src.main" | grep -v grep

echo "服务重启完成！"
