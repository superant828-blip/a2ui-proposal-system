#!/usr/bin/env python3
"""
改善提案收集系统 - 后端 API
基于 FastAPI + SQLite
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import sqlite3
import os
import hashlib

app = FastAPI(title="改善提案系统 API", version="1.1.0")

# 数据库路径（可从环境变量配置）
DB_PATH = os.getenv('PROPOSALS_DB_PATH', 
    '/home/test/.openclaw/workspace/a2ui-proposal-system/proposals.db')

# 管理员账号（可通过环境变量配置）
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# 健康检查
@app.get("/")
def root():
    return {"status": "ok", "service": "改善提案系统 API", "version": "1.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# CORS 配置（可从环境变量配置）
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码哈希
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 数据库初始化
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 提案表
    c.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            problem_desc TEXT NOT NULL,
            solution TEXT,
            expected_effect TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'normal',
            submitter TEXT,
            assignee TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    ''')
    
    # 分类表
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT,
            icon TEXT
        )
    ''')
    
    # 默认分类
    categories = [
        ('流程优化', '#3b82f6', '🔄'),
        ('工具改进', '#10b981', '🛠️'),
        ('文档完善', '#f59e0b', '📝'),
        ('环境改善', '#8b5cf6', '🏠'),
        ('其他', '#6b7280', '📌')
    ]
    c.executemany('INSERT OR IGNORE INTO categories (name, color, icon) VALUES (?, ?, ?)', categories)
    
    # 用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            display_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建默认管理员
    c.execute('SELECT id FROM users WHERE username = ?', (ADMIN_USERNAME,))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password, role, display_name) VALUES (?, ?, ?, ?)',
                  (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), 'admin', '管理员'))
    
    conn.commit()
    conn.close()

init_db()

# 简单的 token 验证（生产环境请使用 JWT）
def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    token = authorization[7:]
    
    # 验证 token 格式: username:role
    try:
        username, role = token.split(':')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        
        if not row or row[1] != role:
            raise HTTPException(status_code=401, detail="无效的令牌")
        
        return {'username': username, 'role': role}
    except:
        raise HTTPException(status_code=401, detail="无效的令牌")

def require_admin(user = Depends(verify_token)):
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user

# 数据模型
class Proposal(BaseModel):
    title: str
    category: str
    problem_desc: str
    solution: Optional[str] = None
    expected_effect: Optional[str] = None
    priority: str = "normal"
    submitter: str = "匿名"
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('标题不能为空')
        if len(v) > 200:
            raise ValueError('标题不能超过200字符')
        return v.strip()
    
    @field_validator('problem_desc')
    @classmethod
    def validate_problem_desc(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('问题描述不能为空')
        if len(v) > 2000:
            raise ValueError('问题描述不能超过2000字符')
        return v.strip()
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('优先级必须是: low, normal, high, urgent')
        return v

class ProposalUpdate(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'user'
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# ============ 用户管理 API ============

@app.post("/api/auth/login")
def login(data: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT id, username, password, role, display_name FROM users WHERE username = ?', (data.username,))
    user = c.fetchone()
    conn.close()
    
    if not user or user['password'] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成简单 token
    token = f"{user['username']}:{user['role']}"
    
    return {
        "token": token,
        "username": user['username'],
        "role": user['role'],
        "display_name": user['display_name']
    }

@app.get("/api/users")
def get_users(user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT id, username, role, display_name, created_at FROM users ORDER BY created_at DESC')
    users = c.fetchall()
    conn.close()
    
    return [dict(row) for row in users]

@app.post("/api/users")
def create_user(data: UserCreate, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查用户名是否存在
    c.execute('SELECT id FROM users WHERE username = ?', (data.username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    c.execute('INSERT INTO users (username, password, role, display_name) VALUES (?, ?, ?, ?)',
              (data.username, hash_password(data.password), data.role, data.display_name or data.username))
    
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": user_id, "message": "用户创建成功"}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 不能删除自己
    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    if row and row[0] == ADMIN_USERNAME:
        conn.close()
        raise HTTPException(status_code=400, detail="不能删除管理员账号")
    
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    
    conn.commit()
    conn.close()
    
    return {"message": "删除成功"}

@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: UserCreate, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查用户是否存在
    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户名是否重复
    c.execute('SELECT id FROM users WHERE username = ? AND id != ?', (data.username, user_id))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    c.execute('UPDATE users SET username = ?, role = ?, display_name = ? WHERE id = ?',
              (data.username, data.role, data.display_name or data.username, user_id))
    
    # 如果提供了新密码
    if data.password:
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hash_password(data.password), user_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "更新成功"}

# ============ 提案 CRUD API ============

@app.post("/api/proposals")
def create_proposal(proposal: Proposal):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO proposals (title, category, problem_desc, solution, expected_effect, priority, submitter, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (proposal.title, proposal.category, proposal.problem_desc, proposal.solution, 
          proposal.expected_effect, proposal.priority, proposal.submitter))
    
    proposal_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": proposal_id, "status": "pending", "message": "提案提交成功"}

@app.get("/api/proposals")
def get_proposals(status: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM proposals WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/api/proposals/{proposal_id}")
def get_proposal(proposal_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="提案不存在")
    
    return dict(row)

@app.put("/api/proposals/{proposal_id}")
def update_proposal(proposal_id: int, update: ProposalUpdate, user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查是否存在
    c.execute("SELECT id FROM proposals WHERE id = ?", (proposal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    # 构建更新语句
    updates = []
    params = []
    
    if update.status:
        updates.append("status = ?")
        params.append(update.status)
        if update.status == "completed":
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
    
    if update.assignee:
        updates.append("assignee = ?")
        params.append(update.assignee)
    
    if update.priority:
        updates.append("priority = ?")
        params.append(update.priority)
    
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(proposal_id)
        
        c.execute(f"UPDATE proposals SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()
    return {"message": "更新成功"}

@app.delete("/api/proposals/{proposal_id}")
def delete_proposal(proposal_id: int, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    conn.commit()
    conn.close()
    
    return {"message": "删除成功"}

# ============ 统计 API ============

@app.get("/api/stats/overview")
def get_stats_overview():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 总数
    c.execute("SELECT COUNT(*) FROM proposals")
    total = c.fetchone()[0]
    
    # 各状态数量
    c.execute("SELECT status, COUNT(*) as count FROM proposals GROUP BY status")
    status_counts = dict(c.fetchall())
    
    # 采纳率
    approved = status_counts.get('approved', 0) + status_counts.get('completed', 0)
    adoption_rate = (approved / total * 100) if total > 0 else 0
    
    # 完成率
    completed = status_counts.get('completed', 0)
    completion_rate = (completed / approved * 100) if approved > 0 else 0
    
    conn.close()
    
    return {
        "total": total,
        "pending": status_counts.get('pending', 0),
        "reviewing": status_counts.get('reviewing', 0),
        "approved": status_counts.get('approved', 0),
        "completed": status_counts.get('completed', 0),
        "rejected": status_counts.get('rejected', 0),
        "adoption_rate": round(adoption_rate, 1),
        "completion_rate": round(completion_rate, 1)
    }

@app.get("/api/stats/by-category")
def get_stats_by_category():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT category, 
               COUNT(*) as total,
               SUM(CASE WHEN status IN ('approved', 'completed') THEN 1 ELSE 0 END) as adopted
        FROM proposals 
        GROUP BY category
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    return [
        {
            "category": row["category"],
            "total": row["total"],
            "adopted": row["adopted"],
            "rate": round(row["adopted"] / row["total"] * 100, 1) if row["total"] > 0 else 0
        }
        for row in rows
    ]

@app.get("/api/stats/by-month")
def get_stats_by_month(months: int = 6):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute(f'''
        SELECT strftime('%Y-%m', created_at) as month,
               COUNT(*) as count
        FROM proposals 
        WHERE created_at >= date('now', '-{months} months')
        GROUP BY month
        ORDER BY month
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    return [{"month": row[0], "count": row[1]} for row in rows]

@app.get("/api/stats/chart-data")
def get_chart_data():
    """获取图表所需的所有数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 按分类统计
    c.execute('''
        SELECT category, 
               COUNT(*) as total,
               SUM(CASE WHEN status IN ('approved', 'completed') THEN 1 ELSE 0 END) as adopted
        FROM proposals 
        GROUP BY category
    ''')
    category_data = c.fetchall()
    
    # 按状态统计
    c.execute('SELECT status, COUNT(*) as count FROM proposals GROUP BY status')
    status_data = c.fetchall()
    
    # 按月统计
    c.execute('''
        SELECT strftime('%Y-%m', created_at) as month,
               COUNT(*) as count
        FROM proposals 
        WHERE created_at >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    ''')
    month_data = c.fetchall()
    
    # 按优先级统计
    c.execute('SELECT priority, COUNT(*) as count FROM proposals GROUP BY priority')
    priority_data = c.fetchall()
    
    conn.close()
    
    return {
        "by_category": [
            {"name": row["category"], "total": row["total"], "adopted": row["adopted"]}
            for row in category_data
        ],
        "by_status": [
            {"name": row["status"], "count": row["count"]}
            for row in status_data
        ],
        "by_month": [
            {"month": row["month"], "count": row["count"]}
            for row in month_data
        ],
        "by_priority": [
            {"name": row["priority"], "count": row["count"]}
            for row in priority_data
        ]
    }

@app.get("/api/categories")
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM categories")
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
