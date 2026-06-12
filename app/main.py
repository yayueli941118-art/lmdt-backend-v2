"""
LMDT 2.0 — FastAPI 应用入口 (Production-Ready)
启动: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
"""

import os, time, logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# ── OpenTelemetry ──────────────────────────────────
def _init_otel():
    """如果环境变量 OTEL_EXPORTER_OTLP_ENDPOINT 存在则启用 OTLP 导出"""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logging.info("OTEL disabled (no OTEL_EXPORTER_OTLP_ENDPOINT set)")
        return None

    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    resource = Resource.create({SERVICE_NAME: "lmdt-backend-v2"})

    # Traces
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    RequestsInstrumentor().instrument()
    logging.info(f"OTEL enabled: traces + metrics → {endpoint}")
    return provider

otel_provider = _init_otel()

# ── Lifespan ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if otel_provider:
        otel_provider.shutdown()

app = FastAPI(
    title="LMDT 2.0 API",
    description="劳动经济学数字孪生系统 · 计算核心引擎",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS (生产环境白名单) ─────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 自定义中间件：请求耗时日志 ────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
    logging.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed_ms:.1f}ms)")
    return response

# ── OpenTelemetry FastAPI 自动插桩 ─────────────────
if otel_provider:
    FastAPIInstrumentor.instrument_app(app)

# ── 路由 ──────────────────────────────────────────
from app.routers import macro, micro
from app.routers import labor_supply, discrimination, labor_demand, wage, macro_lab

app.include_router(macro.router)
app.include_router(micro.router)
app.include_router(labor_supply.router)
app.include_router(discrimination.router)
app.include_router(labor_demand.router)
app.include_router(wage.router)
app.include_router(macro_lab.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

# ── SPA 静态文件服务（生产部署） ────────────────
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: 所有非 API 路径返回 index.html"""
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    
    # 覆盖根路由：返回 SPA 首页
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
