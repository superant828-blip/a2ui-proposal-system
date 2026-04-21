# 💡 改善提案收集系统

基于 OpenClaw A2UI + FastAPI + SQLite 的完整解决方案。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2UI 前端 (Canvas)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  提交提案   │  │  提案列表    │  │  数据看板   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI 后端 (端口 8004)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  提案 CRUD  │  │  统计分析    │  │  数据看板   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite 数据库                              │
│              proposals.db (提案数据存储)                       │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 启动后端服务

```bash
cd ~/workspace/a2ui-proposal-system
python3 backend/api.py
```

服务启动后访问：
- API 文档: http://localhost:8004/docs
- 健康检查: http://localhost:8004/

### 2. 推送到 Canvas

```bash
# 完整版 UI (含统计和列表)
openclaw nodes canvas a2ui push --node <node-id> --jsonl a2ui/proposal-full.json

# 基础表单版
openclaw nodes canvas a2ui push --node <node-id> --jsonl proposal-form-v2.json
```

## API 接口

### 提案管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/proposals | 提交新提案 |
| GET | /api/proposals | 获取提案列表 |
| GET | /api/proposals/{id} | 获取提案详情 |
| PUT | /api/proposals/{id} | 更新提案状态 |
| DELETE | /api/proposals/{id} | 删除提案 |

### 数据分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/stats/overview | 整体统计数据 |
| GET | /api/stats/by-category | 按分类统计 |
| GET | /api/stats/by-month | 按月统计 |
| GET | /api/categories | 获取分类列表 |

### API 使用示例

```bash
# 提交提案
curl -X POST http://localhost:8004/api/proposals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "优化代码审查流程",
    "category": "流程优化",
    "problem_desc": "当前代码审查流程耗时较长",
    "solution": "引入自动化工具进行预审",
    "priority": "high",
    "submitter": "张三"
  }'

# 获取统计
curl http://localhost:8004/api/stats/overview

# 获取分类统计
curl http://localhost:8004/api/stats/by-category
```

## 数据库

- 位置: `proposals.db`
- 包含表: `proposals`, `categories`

### 提案状态

| 状态 | 说明 |
|------|------|
| pending | 待审核 |
| reviewing | 审核中 |
| approved | 已采纳 |
| completed | 已完成 |
| rejected | 已拒绝 |

## 文件结构

```
a2ui-proposal-system/
├── backend/
│   └── api.py              # FastAPI 后端服务
├── a2ui/
│   ├── proposal-form.json      # 基础表单
│   ├── proposal-form-v2.json   # 完整表单
│   └── proposal-full.json      # 完整版 UI (含列表和统计)
├── docs/
│   └── architecture.md     # 架构文档
├── start.sh                # 启动脚本
└── README.md               # 本文件
```

## 功能特性

### 前台 (A2UI)
- ✅ 提交提案表单
- ✅ 提案列表展示
- ✅ 状态标签显示
- ✅ 统计卡片

### 后台 (API)
- ✅ 提案 CRUD
- ✅ 状态管理
- ✅ 统计分析
- ✅ 分类统计
- ✅ 趋势分析

### 数据分析
- 📊 整体概览 (总数/采纳率/完成率)
- 📊 分类统计 (各类型数量及采纳率)
- 📊 时间趋势 (每月提交数量)

## 扩展开发

### 添加新字段
1. 修改 `backend/api.py` 中的 `Proposal` 模型
2. 修改 A2UI JSON 添加对应字段组件

### 添加新统计
在 `/api/stats/` 下添加新的端点

### 集成其他数据库
修改 `init_db()` 函数切换到 MySQL/PostgreSQL
