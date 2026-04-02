#!/bin/bash
# FinanceSail 自动部署脚本
# 服务器路径: /home/admin/FinanceSail

set -e

PROJECT_DIR="/home/admin/FinanceSail"
BACKUP_DIR="/tmp/finacesail-backup"
REPO_URL="https://github.com/caoshichuang/FinanceSail.git"

echo "========================================="
echo "FinanceSail 部署开始"
echo "========================================="

# 1. 备份敏感文件
echo "[1/5] 备份配置文件..."
mkdir -p $BACKUP_DIR
cp $PROJECT_DIR/.env $BACKUP_DIR/.env 2>/dev/null || echo "警告: .env 文件不存在，跳过备份"
cp $PROJECT_DIR/data/holidays.json $BACKUP_DIR/holidays.json 2>/dev/null || true
cp $PROJECT_DIR/data/db.sqlite3 $BACKUP_DIR/db.sqlite3 2>/dev/null || true

# 2. 拉取最新代码
echo "[2/5] 拉取最新代码..."

# 清除代理设置（避免 clash/v2ray 代理干扰 GitHub 访问）
echo "清除代理设置..."
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true

# HTTPS clone 双模式：首次 clone / 后续 pull
if [ -d "$PROJECT_DIR/.git" ]; then
  echo "仓库已存在，执行增量更新..."
  cd $PROJECT_DIR
  # 确保远端 URL 为 HTTPS 格式（公开仓库，无需鉴权）
  git remote set-url origin $REPO_URL
  git fetch origin main
  git reset --hard origin/main
  echo "代码更新成功"
else
  echo "首次部署，执行 git clone..."
  mkdir -p "$(dirname $PROJECT_DIR)"
  git clone $REPO_URL "$PROJECT_DIR"
  echo "克隆成功: $PROJECT_DIR"
  cd $PROJECT_DIR
fi

# 3. 恢复敏感文件
echo "[3/5] 恢复配置文件..."
cp $BACKUP_DIR/.env $PROJECT_DIR/.env 2>/dev/null || echo "警告: .env 文件未恢复（首次部署需手动配置）"
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
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080 > /tmp/finacesail.log 2>&1 &

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "========================================="
echo "FinanceSail 部署完成"
echo "========================================="
echo "服务状态："
ps aux | grep "src.main" | grep -v grep || echo "警告：服务未运行"
echo "========================================="
echo "访问地址：http://139.224.40.205:8080"
echo "========================================="
curl -s http://localhost:8080/api/health || echo "警告：服务未响应（可能仍在启动中）"
