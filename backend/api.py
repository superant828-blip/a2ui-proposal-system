#!/usr/bin/env python3
"""
改善提案收集系统 - 后端 API
基于 FastAPI + SQLite
功能增强版：情感分析、评分、评论、标签、搜索、通知、附件
"""

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import sqlite3
import os
import hashlib
import json
import re
from pathlib import Path

app = FastAPI(title="改善提案系统 API", version="1.2.0")

# 数据库路径
DB_PATH = os.getenv('PROPOSALS_DB_PATH', 
    '/home/test/.openclaw/workspace/a2ui-proposal-system/proposals.db')

# 上传文件目录
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 
    '/home/test/.openclaw/workspace/a2ui-proposal-system/uploads')

# 管理员账号
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 健康检查
@app.get("/")
def root():
    return {"status": "ok", "service": "改善提案系统 API", "version": "1.2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# CORS 配置
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

# 简单情感分析函数
def analyze_sentiment(text):
    """基于关键词的简单情感分析"""
    positive_words = ['好', '优秀', '棒', '赞', '提升', '改进', '优化', '高效', '方便', '实用', '有价值', '支持', '点赞']
    negative_words = ['差', '烂', '慢', '问题', 'bug', '错误', '麻烦', '难用', '低效', '垃圾', '抱怨', '不满']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    return 'neutral'

# 数据库初始化
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 提案表（扩展）
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
            score INTEGER DEFAULT 0,
            sentiment TEXT DEFAULT 'neutral',
            submitter TEXT,
            assignee TEXT,
            tags TEXT DEFAULT '[]',
            search_text TEXT DEFAULT '',
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
    
    # 标签表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#3b82f6'
        )
    ''')
    
    # 默认分类和标签
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
    
    # 评论表
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        )
    ''')
    
    # 附件表
    c.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        )
    ''')
    
    # 通知表
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建默认管理员
    c.execute('SELECT id FROM users WHERE username = ?', (ADMIN_USERNAME,))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password, role, display_name) VALUES (?, ?, ?, ?)',
                  (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), 'admin', '管理员'))
    
    # 添加一些默认标签
    default_tags = [('重要', '#ef4444'), ('紧急', '#f59e0b'), ('长期', '#8b5cf6'), ('快速修复', '#10b981')]
    c.executemany('INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)', default_tags)
    
    conn.commit()
    conn.close()

init_db()

# Token 验证
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization[7:]
    try:
        username, role = token.split(':')
        return {'username': username, 'role': role}
    except:
        raise HTTPException(status_code=401, detail="无效的令牌")

def require_admin(user = Depends(verify_token)):
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user

# ========== 数据模型 ==========

class Proposal(BaseModel):
    title: str
    category: str
    problem_desc: str
    solution: Optional[str] = None
    expected_effect: Optional[str] = None
    priority: str = "normal"
    submitter: str = "匿名"
    tags: Optional[List[str]] = []
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('标题不能为空')
        if len(v) > 200:
            raise ValueError('标题不能超过200字符')
        return v.strip()

class ProposalUpdate(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    score: Optional[int] = None

class CommentCreate(BaseModel):
    content: str

class TagCreate(BaseModel):
    name: str
    color: str = '#3b82f6'

# ========== 认证 API ==========

@app.post("/api/auth/login")
def login(data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT id, username, password, role, display_name FROM users WHERE username = ?', (data.get('username'),))
    user = c.fetchone()
    conn.close()
    
    if not user or user['password'] != hash_password(data.get('password', '')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    return {
        "token": f"{user['username']}:{user['role']}",
        "username": user['username'],
        "role": user['role'],
        "display_name": user['display_name']
    }

# ========== 提案 CRUD ==========

@app.post("/api/proposals")
def create_proposal(proposal: Proposal):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 情感分析
    full_text = f"{proposal.problem_desc} {proposal.solution or ''}"
    sentiment = analyze_sentiment(full_text)
    
    # 搜索文本
    search_text = f"{proposal.title} {proposal.problem_desc} {proposal.solution or ''} {proposal.category}"
    
    # 标签转JSON
    tags_json = json.dumps(proposal.tags) if proposal.tags else '[]'
    
    c.execute('''
        INSERT INTO proposals (title, category, problem_desc, solution, expected_effect, priority, submitter, status, sentiment, tags, search_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
    ''', (proposal.title, proposal.category, proposal.problem_desc, proposal.solution, 
          proposal.expected_effect, proposal.priority, proposal.submitter, sentiment, tags_json, search_text))
    
    proposal_id = c.lastrowid
    
    # 创建通知
    c.execute('INSERT INTO notifications (user, message, type) VALUES (?, ?, ?)',
              ('admin', f'新提案: {proposal.title}', 'proposal'))
    
    conn.commit()
    conn.close()
    
    return {"id": proposal_id, "status": "pending", "sentiment": sentiment, "message": "提案提交成功"}

@app.get("/api/proposals")
def get_proposals(
    status: Optional[str] = None, 
    category: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_score: Optional[int] = None,
    limit: int = 50
):
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
    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)
    if min_score is not None:
        query += " AND score >= ?"
        params.append(min_score)
    if search:
        query += " AND search_text LIKE ?"
        params.append(f"%{search}%")
    if tags:
        query += " AND tags LIKE ?"
        params.append(f"%{tags}%")
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    
    # 获取附件和评论数
    results = []
    for row in rows:
        item = dict(row)
        item['tags'] = json.loads(row['tags'] or '[]')
        
        # 获取评论数
        c.execute('SELECT COUNT(*) FROM comments WHERE proposal_id = ?', (row['id'],))
        item['comment_count'] = c.fetchone()[0]
        
        # 获取附件数
        c.execute('SELECT COUNT(*) FROM attachments WHERE proposal_id = ?', (row['id'],))
        item['attachment_count'] = c.fetchone()[0]
        
        results.append(item)
    
    conn.close()
    return results

@app.get("/api/proposals/{proposal_id}")
def get_proposal(proposal_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    item = dict(row)
    item['tags'] = json.loads(row['tags'] or '[]')
    
    # 获取评论
    c.execute('SELECT * FROM comments WHERE proposal_id = ? ORDER BY created_at DESC', (proposal_id,))
    item['comments'] = [dict(r) for r in c.fetchall()]
    
    # 获取附件
    c.execute('SELECT id, filename, filesize, uploaded_at FROM attachments WHERE proposal_id = ?', (proposal_id,))
    item['attachments'] = [dict(r) for r in c.fetchall()]
    
    conn.close()
    return item

@app.put("/api/proposals/{proposal_id}")
def update_proposal(proposal_id: int, update: ProposalUpdate, user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, status FROM proposals WHERE id = ?", (proposal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    updates = []
    params = []
    
    if update.status:
        updates.append("status = ?")
        params.append(update.status)
        
        # 创建状态变更通知
        c.execute('INSERT INTO notifications (user, message, type) VALUES (?, ?, ?)',
                  (update.status, f'提案 #{proposal_id} 状态变更为 {update.status}', 'status'))
        
        if update.status == "completed":
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
    
    if update.assignee:
        updates.append("assignee = ?")
        params.append(update.assignee)
    
    if update.priority:
        updates.append("priority = ?")
        params.append(update.priority)
    
    if update.score is not None:
        updates.append("score = ?")
        params.append(update.score)
        
        # 评分通知
        c.execute('INSERT INTO notifications (user, message, type) VALUES (?, ?, ?)',
                  (update.assignee or 'admin', f'提案 #{proposal_id} 获得评分: {update.score}分', 'score'))
    
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
    
    # 删除关联的评论和附件
    c.execute("DELETE FROM comments WHERE proposal_id = ?", (proposal_id,))
    c.execute("DELETE FROM attachments WHERE proposal_id = ?", (proposal_id,))
    c.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# ========== 评论 API ==========

@app.post("/api/proposals/{proposal_id}/comments")
def add_comment(proposal_id: int, comment: CommentCreate, user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查提案是否存在
    c.execute("SELECT id FROM proposals WHERE id = ?", (proposal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    c.execute('INSERT INTO comments (proposal_id, user, content) VALUES (?, ?, ?)',
              (proposal_id, user['username'], comment.content))
    
    # 情感分析
    sentiment = analyze_sentiment(comment.content)
    
    # 通知
    c.execute('INSERT INTO notifications (user, message, type) VALUES (?, ?, ?)',
              ('admin', f'{user["username"]} 评论了提案 #{proposal_id}', 'comment'))
    
    comment_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": comment_id, "sentiment": sentiment, "message": "评论成功"}

@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT user FROM comments WHERE id = ?", (comment_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 只能删除自己的评论 或 管理员
    if row[0] != user['username'] and user['role'] != 'admin':
        conn.close()
        raise HTTPException(status_code=403, detail="无权限删除")
    
    c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    
    return {"message": "删除成功"}

# ========== 附件 API ==========

@app.post("/api/proposals/{proposal_id}/attachments")
async def upload_attachment(proposal_id: int, file: UploadFile = File(...), user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 检查提案是否存在
    c.execute("SELECT id FROM proposals WHERE id = ?", (proposal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="提案不存在")
    
    # 保存文件
    filename = f"{proposal_id}_{datetime.now().timestamp()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    with open(filepath, 'wb') as f:
        f.write(content)
    
    filesize = len(content)
    
    c.execute('INSERT INTO attachments (proposal_id, filename, filepath, filesize) VALUES (?, ?, ?, ?)',
              (proposal_id, file.filename, filename, filesize))
    
    attachment_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": attachment_id, "filename": file.filename, "filesize": filesize, "message": "上传成功"}

@app.get("/api/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT filename, filepath FROM attachments WHERE id = ?", (attachment_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    filepath = os.path.join(UPLOAD_DIR, row[1])
    return FileResponse(filepath, filename=row[0])

@app.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT filepath FROM attachments WHERE id = ?", (attachment_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 删除文件
    filepath = os.path.join(UPLOAD_DIR, row[0])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    c.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
    conn.commit()
    conn.close()
    
    return {"message": "删除成功"}

# ========== 标签 API ==========

@app.get("/api/tags")
def get_tags():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tags ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/tags")
def create_tag(tag: TagCreate, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id FROM tags WHERE name = ?", (tag.name,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="标签已存在")
    
    c.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (tag.name, tag.color))
    tag_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": tag_id, "message": "标签创建成功"}

@app.delete("/api/tags/{tag_id}")
def delete_tag(tag_id: int, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="标签不存在")
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# ========== 通知 API ==========

@app.get("/api/notifications")
def get_notifications(user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 获取当前用户和管理员的通知
    c.execute('''
        SELECT * FROM notifications 
        WHERE user IN (?, 'admin')
        ORDER BY created_at DESC LIMIT 50
    ''', (user['username'],))
    
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.put("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, user = Depends(verify_token)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return {"message": "已标记为已读"}

# ========== 统计 API ==========

@app.get("/api/stats/overview")
def get_stats_overview():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM proposals")
    total = c.fetchone()[0]
    
    c.execute("SELECT status, COUNT(*) as count FROM proposals GROUP BY status")
    status_counts = dict(c.fetchall())
    
    c.execute("SELECT AVG(score) FROM proposals WHERE score > 0")
    avg_score = c.fetchone()[0] or 0
    
    c.execute("SELECT sentiment, COUNT(*) as count FROM proposals GROUP BY sentiment")
    sentiment_counts = dict(c.fetchall())
    
    c.execute("SELECT COUNT(*) FROM comments")
    comment_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM attachments")
    attachment_count = c.fetchone()[0]
    
    approved = status_counts.get('approved', 0) + status_counts.get('completed', 0)
    adoption_rate = (approved / total * 100) if total > 0 else 0
    completion_rate = (approved / total * 100) if approved > 0 else 0
    
    conn.close()
    
    return {
        "total": total,
        "pending": status_counts.get('pending', 0),
        "reviewing": status_counts.get('reviewing', 0),
        "approved": status_counts.get('approved', 0),
        "completed": status_counts.get('completed', 0),
        "rejected": status_counts.get('rejected', 0),
        "adoption_rate": round(adoption_rate, 1),
        "completion_rate": round(completion_rate, 1),
        "avg_score": round(avg_score, 1),
        "comment_count": comment_count,
        "attachment_count": attachment_count,
        "sentiment": sentiment_counts
    }

@app.get("/api/stats/chart-data")
def get_chart_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT category, COUNT(*) as total, AVG(score) as avg_score FROM proposals GROUP BY category')
    category_data = c.fetchall()
    
    c.execute('SELECT status, COUNT(*) as count FROM proposals GROUP BY status')
    status_data = c.fetchall()
    
    c.execute('SELECT sentiment, COUNT(*) as count FROM proposals GROUP BY sentiment')
    sentiment_data = c.fetchall()
    
    conn.close()
    
    return {
        "by_category": [{"name": r["category"], "total": r["total"], "avg_score": r["avg_score"] or 0} for r in category_data],
        "by_status": [{"name": r["status"], "count": r["count"]} for r in status_data],
        "by_sentiment": [{"name": r["sentiment"], "count": r["count"]} for r in sentiment_data]
    }

# ========== 用户管理 API ==========

@app.get("/api/users")
def get_users(user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username, role, display_name, created_at FROM users ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/users")
def create_user(data: dict, user = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT id FROM users WHERE username = ?', (data.get('username'),))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    c.execute('INSERT INTO users (username, password, role, display_name) VALUES (?, ?, ?, ?)',
              (data.get('username'), hash_password(data.get('password')), data.get('role', 'user'), 
               data.get('display_name') or data.get('username')))
    
    conn.commit()
    conn.close()
    return {"message": "用户创建成功"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
