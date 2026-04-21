/**
 * A2UI 改善提案系统 - 公共工具函数
 * 统一管理所有页面的公共逻辑
 */

const API_BASE = window.location.origin.replace(':8005', ':8004');

// ========== 认证相关 ==========

/**
 * 获取存储的 token
 */
function getToken() {
    return localStorage.getItem('a2ui_token');
}

/**
 * 解析 token 获取用户信息
 */
function parseToken() {
    const token = getToken();
    if (!token) return null;
    try {
        return JSON.parse(decodeURIComponent(token));
    } catch {
        return null;
    }
}

/**
 * 检查登录状态，未登录则跳转
 */
function requireAuth() {
    const user = parseToken();
    if (!user) {
        window.location.href = 'login.html';
        return null;
    }
    return user;
}

/**
 * 检查管理员权限
 */
function requireAdmin() {
    const user = parseToken();
    if (!user || user.role !== 'admin') {
        alert('需要管理员权限');
        window.location.href = 'admin.html';
        return null;
    }
    return user;
}

/**
 * 退出登录
 */
function logout() {
    if (confirm('确定要退出登录吗？')) {
        localStorage.removeItem('a2ui_token');
        window.location.href = 'login.html';
    }
}

/**
 * 获取带授权的请求头
 */
function getAuthHeaders() {
    const user = parseToken();
    if (!user || !user.token) return {};
    return { 'Authorization': `Bearer ${user.token}` };
}

// ========== 自动登出 ==========

let idleTime = 0;
let idleInterval = null;

/**
 * 启动自动登出计时器
 */
function startIdleTimer(minutes = 10) {
    if (idleInterval) return;
    
    idleInterval = setInterval(() => {
        idleTime++;
        if (idleTime >= minutes) {
            if (confirm('长时间未操作，是否继续？')) {
                idleTime = 0;
            } else {
                logout();
            }
        }
    }, 60000); // 每分钟检查一次
    
    // 重置计时器的事件
    document.addEventListener('click', () => idleTime = 0);
    document.addEventListener('keypress', () => idleTime = 0);
    document.addEventListener('scroll', () => idleTime = 0);
}

/**
 * 停止自动登出计时器
 */
function stopIdleTimer() {
    if (idleInterval) {
        clearInterval(idleInterval);
        idleInterval = null;
    }
    idleTime = 0;
}

// ========== 用户界面 ==========

/**
 * 初始化导航栏用户显示
 */
function initNavUser() {
    const user = parseToken();
    const userDisplay = document.getElementById('user-display');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    
    if (user && userDisplay) {
        userDisplay.textContent = (user.display_name || user.username) + ' (' + user.role + ')';
        if (loginBtn) loginBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
    } else {
        if (loginBtn) loginBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

/**
 * 显示 Toast 提示
 */
function showToast(message, type = 'success') {
    // 移除已存在的 toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== API 请求 ==========

/**
 * 发起 API 请求
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers
    };
    
    try {
        const res = await fetch(url, { ...options, headers });
        
        // 处理 401 未授权
        if (res.status === 401) {
            showToast('登录已过期，请重新登录', 'error');
            setTimeout(() => logout(), 1500);
            throw new Error('Unauthorized');
        }
        
        // 处理其他错误
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '请求失败');
        }
        
        return await res.json();
    } catch (e) {
        console.error('API Error:', e);
        throw e;
    }
}

/**
 * GET 请求
 */
function apiGet(endpoint) {
    return apiRequest(endpoint, { method: 'GET' });
}

/**
 * POST 请求
 */
function apiPost(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT 请求
 */
function apiPut(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE 请求
 */
function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}

// ========== 工具函数 ==========

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * 转义 HTML 防止 XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 获取状态显示文本
 */
function getStatusText(status) {
    const map = {
        'pending': '待审核',
        'reviewing': '审核中',
        'approved': '已采纳',
        'completed': '已完成',
        'rejected': '已拒绝'
    };
    return map[status] || status;
}

/**
 * 获取角色显示文本
 */
function getRoleText(role) {
    const map = {
        'admin': '管理员',
        'reviewer': '审核员',
        'user': '普通用户'
    };
    return map[role] || role;
}

// ========== 初始化 ==========

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否需要登录
    const currentPage = window.location.pathname.split('/').pop();
    const publicPages = ['login.html', 'index.html'];
    
    if (!publicPages.includes(currentPage)) {
        requireAuth();
    }
    
    // 初始化用户显示
    initNavUser();
});
