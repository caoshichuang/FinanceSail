#!/bin/bash
# FinanceSail 自动部署脚本

set -e

PROJECT_DIR="/home/admin/redbook-auto"
NGINX_WEB_DIR="/var/www/finance-sail"
LOG_FILE="/tmp/redbook-auto.log"

echo "========================================="
echo "FinanceSail 部署开始"
echo "========================================="

cd $PROJECT_DIR

# 1. 拉取最新代码
echo "[1/5] 拉取最新代码..."
# 使用下载方式更新代码（避免 git fetch 超时问题）
cd /home/admin
rm -rf redbook-auto-new
mkdir redbook-auto-new
cd redbook-auto-new
curl -L https://github.com/caoshichuang/FinanceSail/archive/refs/heads/main.zip -o main.zip
python3 -m zipfile -e main.zip .
# 保留原有配置和数据
cp -r $PROJECT_DIR/.env FinanceSail-main/ 2>/dev/null || true
cp -r $PROJECT_DIR/data FinanceSail-main/ 2>/dev/null || true
cp -r $PROJECT_DIR/logs FinanceSail-main/ 2>/dev/null || true
# 替换项目目录
rm -rf $PROJECT_DIR
mv FinanceSail-main $PROJECT_DIR
cd $PROJECT_DIR

# 2. 安装Python依赖
echo "[2/5] 安装Python依赖..."
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 构建前端
echo "[3/5] 构建前端..."
cd admin
npm install --registry=https://registry.npmmirror.com
npm run build
cd ..

# 4. 部署到Nginx目录
echo "[4/5] 部署前端到Nginx..."
sudo mkdir -p $NGINX_WEB_DIR
sudo rm -rf $NGINX_WEB_DIR/*
sudo cp -r admin/dist/* $NGINX_WEB_DIR/
sudo chown -R www-data:www-data $NGINX_WEB_DIR

# 5. 重启服务
echo "[5/5] 重启服务..."

# 重启Python后端
pkill -f "src.main" || true
sleep 1
export PATH=$PATH:/home/admin/.local/bin
screen -dmS redbook bash -c 'export PATH=$PATH:/home/admin/.local/bin && cd /home/admin/redbook-auto && python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080'

# 重载Nginx
sudo systemctl reload nginx

sleep 2

echo "========================================="
echo "FinanceSail 部署完成！"
echo "========================================="
echo "后端状态："
ps aux | grep "src.main" | grep -v grep
echo "========================================="
echo "Nginx状态："
sudo systemctl status nginx --no-pager | head -5
