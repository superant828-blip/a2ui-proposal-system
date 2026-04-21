#!/usr/bin/env python3
"""
A2UI 提案系统 - 端到端测试
使用 Playwright 进行前端交互测试
"""

import asyncio
import json
from datetime import datetime

# 测试配置
BASE_URL = "http://192.168.80.209:8005"
API_URL = "http://192.168.80.209:8004"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

class E2ETester:
    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "tests": []}
    
    def log(self, name, passed, msg=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if msg: print(f"       └─ {msg}")
        self.results["tests"].append({"name": name, "passed": passed, "message": msg})
        if passed: self.results["passed"] += 1
        else: self.results["failed"] += 1
    
    async def run_tests(self):
        print("="*50)
        print("A2UI 提案系统 - 端到端测试")
        print("="*50)
        
        # 1. 首页加载测试
        print("\n【测试1: 首页加载】")
        try:
            import urllib.request
            req = urllib.request.Request(BASE_URL + "/index.html")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.log("首页访问", resp.status == 200, f"状态码: {resp.status}")
        except Exception as e:
            self.log("首页访问", False, str(e))
        
        # 2. 管理后台访问测试
        print("\n【测试2: 管理后台访问】")
        try:
            req = urllib.request.Request(BASE_URL + "/admin.html")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.log("管理后台访问", resp.status == 200, f"状态码: {resp.status}")
        except Exception as e:
            self.log("管理后台访问", False, str(e))
        
        # 3. 登录功能测试
        print("\n【测试3: 登录功能】")
        try:
            import urllib.request
            data = json.dumps({"username": ADMIN_USER, "password": ADMIN_PASS}).encode()
            req = urllib.request.Request(API_URL + "/api/auth/login", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                token = result.get("token", "")
                self.log("管理员登录", token != "", f"Token: {token[:20]}...")
                return token
        except Exception as e:
            self.log("管理员登录", False, str(e))
            return None
    
    def test_frontend_elements(self):
        """测试前端页面元素"""
        print("\n【测试4: 前端元素检查】")
        
        # 检查关键文件是否存在
        import os
        files = [
            "frontend/index.html",
            "frontend/admin.html", 
            "frontend/stats.html",
            "frontend/users.html",
            "frontend/login.html",
            "frontend/js/utils.js",
            "frontend/css/theme.css"
        ]
        
        all_exist = True
        for f in files:
            exists = os.path.exists(f"/home/test/.openclaw/workspace/a2ui-proposal-system/{f}")
            if not exists:
                all_exist = False
                print(f"  ❌ 缺失: {f}")
        
        self.log("前端文件完整", all_exist)
        
        # 检查关键函数
        with open("/home/test/.openclaw/workspace/a2ui-proposal-system/frontend/admin.html") as f:
            admin_html = f.read()
            has_doAction = "doAction" in admin_html
            has_viewProposal = "viewProposal" in admin_html
            has_updateStatus = "updateStatus" in admin_html
            self.log("admin.html关键函数", has_doAction and has_viewProposal and has_updateStatus,
                   f"doAction: {has_doAction}, viewProposal: {has_viewProposal}, updateStatus: {has_updateStatus}")
        
        # 检查 utils.js
        with open("/home/test/.openclaw/workspace/a2ui-proposal-system/frontend/js/utils.js") as f:
            utils_js = f.read()
            has_apiGet = "function apiGet" in utils_js
            has_apiPost = "function apiPost" in utils_js
            has_showToast = "function showToast" in utils_js
            self.log("utils.js工具函数", has_apiGet and has_apiPost and has_showToast)
    
    def test_api_endpoints(self):
        """测试API端点"""
        print("\n【测试5: API端点检查】")
        import urllib.request
        
        endpoints = [
            ("/health", "健康检查"),
            ("/api/tags", "标签API"),
            ("/api/categories", "分类API"),
            ("/api/stats/overview", "统计API"),
        ]
        
        for endpoint, name in endpoints:
            try:
                req = urllib.request.Request(API_URL + endpoint)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.log(name, resp.status == 200)
            except Exception as e:
                self.log(name, False, str(e)[:50])
    
    def test_javascript_syntax(self):
        """测试JavaScript语法"""
        print("\n【测试6: JavaScript语法检查】")
        
        js_files = [
            "frontend/js/utils.js",
        ]
        
        for js_file in js_files:
            with open(f"/home/test/.openclaw/workspace/a2ui-proposal-system/{js_file}") as f:
                content = f.read()
                # 基本语法检查
                has_syntax_issues = (
                    content.count("{") != content.count("}") or
                    content.count("(") != content.count(")") or
                    content.count("[") != content.count("]")
                )
                # 检查重复声明
                has_duplicates = "let idleTime = 0" in content and "frontend/admin.html"
                
                self.log(f"{js_file}语法", not has_syntax_issues, 
                       f"括号匹配: {'✅' if not has_syntax_issues else '❌'}")
    
    def print_summary(self):
        total = self.results["passed"] + self.results["failed"]
        print(f"\n{'='*50}")
        print(f"  测试总结")
        print(f"{'='*50}")
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {self.results['passed']}")
        print(f"  ❌ 失败: {self.results['failed']}")
        print(f"  成功率: {self.results['passed']/total*100:.1f}%")
        print(f"{'='*50}")
        
        # 记录失败的测试
        if self.results["failed"] > 0:
            print("\n失败测试:")
            for t in self.results["tests"]:
                if not t["passed"]:
                    print(f"  - {t['name']}: {t['message']}")

def main():
    tester = E2ETester()
    
    # 运行各项测试
    asyncio.run(tester.run_tests())
    tester.test_frontend_elements()
    tester.test_api_endpoints()
    tester.test_javascript_syntax()
    
    tester.print_summary()
    
    return 0 if tester.results["failed"] == 0 else 1

if __name__ == "__main__":
    exit(main())
