#!/bin/bash
# LMDT 2.0 Backend — GCP Cloud Run 一键部署
# 使用: bash deploy.sh [project-id]

set -e

PROJECT_ID="${1:?Usage: bash deploy.sh YOUR_GCP_PROJECT_ID}"
REGION="asia-east1"  # 台湾彰化（最近中国大陆）
SERVICE="lmdt-backend-v2"

echo "🚀 Deploying to Cloud Run: $PROJECT_ID / $REGION / $SERVICE"

gcloud config set project "$PROJECT_ID"

gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 60

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)')
echo ""
echo "✅ 部署完成！"
echo "后端 URL: $URL"
echo "健康检查: $URL/health"
echo "API 文档: $URL/docs"
echo ""
echo "请将此 URL 填入 lmdt-frontend-v2/.env.production 的 VITE_API_BASE_URL，然后重新部署前端。"
