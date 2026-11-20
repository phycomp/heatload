#!/usr/bin/env bash
# 部署至 Cloudflare Containers（手動）
# 用法: bash deploy.sh [project]  (project: quantum | kpi | all)
set -e
PROJECT="${1:-all}"

deploy_one() {
    local name="$1" dir="$2" image="$3"
    echo "=== 部署 $name ==="
    cd "$dir"
    docker build -t "$image:latest" .
    wrangler deploy
    cd - >/dev/null
}

if [ "$PROJECT" = "quantum" ] || [ "$PROJECT" = "all" ]; then
    deploy_one "量傳線" "/home/sam/量傳線" "liangchuan-line"
fi
if [ "$PROJECT" = "kpi" ] || [ "$PROJECT" = "all" ]; then
    deploy_one "產學合作KPI" "/home/sam/產學合作" "industry-academia-kpi"
fi
echo "部署完成"
PY