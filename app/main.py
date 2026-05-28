"""
LMDT 2.0 — FastAPI 应用入口
启动: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import macro, micro

app = FastAPI(
    title="LMDT 2.0 API",
    description="劳动经济学数字孪生系统 · 计算核心引擎",
    version="2.0.0",
)

# CORS — 允许前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段全开放，生产环境改为前端域名白名单
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(macro.router)
app.include_router(micro.router)


@app.get("/")
async def root():
    return {"service": "LMDT 2.0 Backend", "status": "running", "version": "2.0.0"}
