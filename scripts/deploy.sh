#!/bin/bash
# FinanceSail 自动部署脚本

set -e

PROJECT_DIR="/home/admin/redbook-auto"
BACKUP_DIR="/tmp/redbook-backup"

echo "========================================="
echo "FinanceSail 部署开始"
echo "========================================="

# 1. 备份敏感文件
echo "[1/5] 备份配置文件..."
mkdir -p $BACKUP_DIR
cp $PROJECT_DIR/.env $BACKUP_DIR/.env 2>/dev/null || echo "警告：.env 文件不存在"
cp $PROJECT_DIR/data/holidays.json $BACKUP_DIR/holidays.json 2>/dev/null || true
cp $PROJECT_DIR/data/db.sqlite3 $BACKUP_DIR/db.sqlite3 2>/dev/null || true

# 2. 拉取最新代码
echo "[2/5] 拉取最新代码..."
cd $PROJECT_DIR

# 优化 git 配置，避免超时
git config --global http.version HTTP/1.1
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 60

# 尝试拉取代码，最多重试 5 次
SUCCESS=0
for i in 1 2 3 4 5; do
  echo "尝试第 $i 次拉取..."
  if git fetch origin main --depth=1; then
    echo "拉取成功！"
    SUCCESS=1
    break
  else
    echo "拉取失败，等待 10 秒后重试..."
    sleep 10
  fi
done

if [ $SUCCESS -eq 0 ]; then
  echo "错误：5 次尝试均失败，无法拉取代码"
  exit 1
fi

git reset --hard origin/main

# 3. 恢复敏感文件
echo "[3/5] 恢复配置文件..."
cp $BACKUP_DIR/.env $PROJECT_DIR/.env 2>/dev/null || echo "警告：.env 文件未恢复"
cp $BACKUP_DIR/holidays.json $PROJECT_DIR/data/holidays.json 2>/dev/null || true
cp $BACKUP_DIR/db.sqlite3 $PROJECT_DIR/data/db.sqlite3 2>/dev/null || true

# 4. 构建前端
echo "[4/5] 构建前端..."
cd $PROJECT_DIR/admin
npm install --registry=https://registry.npmmirror.com
npm run build
cd $PROJECT_DIR

# 5. 重启服务
echo "[5/5] 重启服务..."
pkill -f "src.main" || true
sleep 2
export PATH=$PATH:/home/admin/.local/bin
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080 > /tmp/redbook-auto.log 2>&1 &

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "========================================="
echo "FinanceSail 部署完成！"
echo "========================================="
echo "服务状态："
ps aux | grep "src.main" | grep -v grep || echo "警告：服务未运行"
echo "========================================="
echo "访问地址：http://139.224.40.205:8080"
echo "========================================="
curl -s http://localhost:8080/api/health || echo "警告：服务未响应"
