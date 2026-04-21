# 改善提案收集系统 - 完整方案

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前台 UI (A2UI)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  提交提案   │  │  提案列表    │  │  数据看板   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 服务 (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  提案管理   │  │  统计分析    │  │  用户管理   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据库 (SQLite)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ proposals   │  │  categories │  │   users     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 数据库设计

### proposals (提案表)
```sql
CREATE TABLE proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    problem_desc TEXT NOT NULL,
    solution TEXT,
    expected_effect TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/reviewing/approved/rejected/completed
    priority VARCHAR(20) DEFAULT 'normal', -- low/normal/high/urgent
    submitter VARCHAR(50),
    assignee VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE INDEX idx_status ON proposals(status);
CREATE INDEX idx_category ON proposals(category);
CREATE INDEX idx_created_at ON proposals(created_at);
```

### categories (分类表)
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(20),
    icon VARCHAR(20)
);
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/proposals | 提交新提案 |
| GET | /api/proposals | 获取提案列表 |
| GET | /api/proposals/{id} | 获取提案详情 |
| PUT | /api/proposals/{id} | 更新提案状态 |
| DELETE | /api/proposals/{id} | 删除提案 |
| GET | /api/stats/overview | 获取统计数据 |
| GET | /api/stats/by-category | 按分类统计 |
| GET | /api/stats/by-month | 按月统计 |
| GET | /api/stats/trend | 趋势分析 |

## 数据分析维度

### 1. 整体概览
- 总提案数
- 各状态数量 (待审核/审核中/已采纳/已完成/已拒绝)
- 采纳率 = 已采纳 / 总数
- 完成率 = 已完成 / 已采纳

### 2. 分类统计
- 各类型提案数量及占比
- 各类型采纳率对比

### 3. 时间趋势
- 每月提交数量趋势
- 每月完成数量趋势

### 4. 效率指标
- 平均处理时长
- 提案到采纳的平均天数
- 提案到完成的平均天数

### 5. 人员统计
- 提交最多的用户 TOP 10
- 处理最多的管理员 TOP 10
