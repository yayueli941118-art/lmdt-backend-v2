# LMDT 2.0 — 经济学计算核心引擎

> **LMDT (Labor Market Digital Twin) 2.0 Backend** • FastAPI 微服务

## 职责边界

本仓库**不负责 UI 渲染**，专职提供以下核心经济学算法的 RESTful API 服务：

| 模块 | 算法 | API 示例 |
|------|------|----------|
| 人力资本 | 明瑟收入方程 (Mincer Equation) | `POST /api/v2/mincer` |
| 迁移决策 | NPV 动态累积 + 盈亏平衡 | `POST /api/v2/migration/npv` |
| 劳动力需求 | CES 派生需求 + 希克斯-马歇尔定理 | `POST /api/v2/demand/derived` |
| 宏观政策 | 贝弗里奇曲线错配度计算 | `POST /api/v2/macro/beveridge` |
| 收入替代 | 收入效应 vs 替代效应分解 | `POST /api/v2/supply/substitution` |
| 歧视经济学 | Oaxaca-Blinder 分解 | `POST /api/v2/discrimination/decompose` |

## 技术栈

- **框架**: FastAPI (Python 3.11+)
- **计算**: NumPy / SciPy
- **验证**: Pydantic v2
- **部署**: Uvicorn + Docker

## 架构原则

- 纯计算服务：接收参数 JSON → 返回结果 JSON
- 无状态设计：不依赖 session / 数据库
- 输入校验：Pydantic 强类型模型
- 所有核心公式保留学术溯源注释

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 文档

启动后访问 `http://localhost:8000/docs` 查看 Swagger UI 交互式 API 文档。

---

*LMDT 2.0 · 西南交通大学希望学院 · 黎雅月*
