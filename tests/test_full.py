<#!/usr/bin/env python3
"""
改善提案系统 - 完整功能测试套件
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8004"

class ProposalSystemTester:
    def __init__(self, test_name="默认测试"):
        self.test_name = test_name
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"       └─ {message}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    # ========== 认证模块测试 ==========
    
    def test_health(self):
        """测试服务健康状态"""
        try:
            r = requests.get(f"{BASE_URL}/", timeout=5)
            self.log("健康检查", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            self.log("健康检查", False, str(e))
    
    def test_login_success(self):
        """测试登录成功"""
        try:
            data = {"username": "admin", "password": "admin123"}
            r = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=5)
            result = r.json()
            if r.status_code == 200 and "token" in result:
                self.log("登录成功", True, f"用户: {result.get('username')}, 角色: {result.get('role')}")
                return result["token"]
            else:
                self.log("登录成功", False, str(result))
                return None
        except Exception as e:
            self.log("登录成功", False, str(e))
            return None
    
    def test_login_fail(self):
        """测试登录失败"""
        try:
            data = {"username": "admin", "password": "wrongpassword"}
            r = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=5)
            self.log("登录失败", r.status_code == 401, f"Status: {r.status_code}")
        except Exception as e:
            self.log("登录失败", False, str(e))
    
    # ========== 提案模块测试 ==========
    
    def test_create_proposal(self, token=None):
        """测试创建提案"""
        data = {
            "title": f"测试提案-{int(time.time())}",
            "category": "流程优化",
            "problem_desc": "这是一个测试问题描述",
            "solution": "这是测试解决方案",
            "priority": "normal",
            "submitter": "自动化测试"
        }
        try:
            r = requests.post(f"{BASE_URL}/api/proposals", json=data, timeout=5)
            result = r.json()
            if r.status_code == 200 and "id" in result:
                self.log("创建提案", True, f"ID: {result['id']}")
                return result["id"]
            else:
                self.log("创建提案", False, str(result))
                return None
        except Exception as e:
            self.log("创建提案", False, str(e))
            return None
    
    def test_get_proposals(self):
        """测试获取提案列表"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("获取提案列表", len(data) > 0, f"共 {len(data)} 条")
                return data
            else:
                self.log("获取提案列表", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("获取提案列表", False, str(e))
            return []
    
    def test_get_proposal_by_id(self, proposal_id, token=None):
        """测试获取单个提案"""
        try:
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
            r = requests.get(f"{BASE_URL}/api/proposals/{proposal_id}", headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log(f"获取提案 #{proposal_id}", data["id"] == proposal_id, f"标题: {data.get('title', '')}")
                return data
            else:
                self.log(f"获取提案 #{proposal_id}", False, f"Status: {r.status_code}")
                return None
        except Exception as e:
            self.log(f"获取提案 #{proposal_id}", False, str(e))
            return None
    
    def test_update_proposal(self, proposal_id, token):
        """测试更新提案状态"""
        if not token:
            self.log(f"更新提案 #{proposal_id}", False, "无token")
            return False
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "reviewing"},
                          headers={'Authorization': f'Bearer {token}'}, 
                          timeout=5)
            self.log(f"更新提案状态", r.status_code == 200, f"Status: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            self.log(f"更新提案状态", False, str(e))
            return False
    
    def test_update_to_approved(self, proposal_id, token):
        """测试更新为已采纳"""
        if not token:
            return False
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "approved"},
                          headers={'Authorization': f'Bearer {token}'}, 
                          timeout=5)
            self.log(f"采纳提案", r.status_code == 200, f"Status: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            self.log(f"采纳提案", False, str(e))
            return False
    
    def test_update_to_completed(self, proposal_id, token):
        """测试更新为已完成"""
        if not token:
            return False
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "completed"},
                          headers={'Authorization': f'Bearer {token}'}, 
                          timeout=5)
            self.log(f"完成提案", r.status_code == 200, f"Status: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            self.log(f"完成提案", False, str(e))
            return False
    
    def test_delete_proposal(self, proposal_id, token):
        """测试删除提案"""
        if not token:
            return False
        try:
            r = requests.delete(f"{BASE_URL}/api/proposals/{proposal_id}",
                              headers={'Authorization': f'Bearer {token}'},
                              timeout=5)
            self.log(f"删除提案", r.status_code == 200, f"Status: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            self.log(f"删除提案", False, str(e))
            return False
    
    def test_get_nonexistent(self):
        """测试获取不存在的提案"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals/99999", timeout=5)
            self.log("获取不存在的提案", r.status_code == 404, f"Status: {r.status_code}")
        except Exception as e:
            self.log("获取不存在的提案", False, str(e))
    
    # ========== 统计模块测试 ==========
    
    def test_stats_overview(self):
        """测试统计概览"""
        try:
            r = requests.get(f"{BASE_URL}/api/stats/overview", timeout=5)
            if r.status_code == 200:
                data = r.json()
                has_fields = all(k in data for k in ["total", "pending", "approved", "completed"])
                self.log("统计概览", has_fields, f"total={data.get('total', 0)}")
                return data
            else:
                self.log("统计概览", False, f"Status: {r.status_code}")
                return None
        except Exception as e:
            self.log("统计概览", False, str(e))
            return None
    
    def test_stats_by_category(self):
        """测试分类统计"""
        try:
            r = requests.get(f"{BASE_URL}/api/stats/by-category", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("分类统计", isinstance(data, list), f"共 {len(data)} 个分类")
                return data
            else:
                self.log("分类统计", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("分类统计", False, str(e))
            return []
    
    def test_stats_chart_data(self):
        """测试图表数据"""
        try:
            r = requests.get(f"{BASE_URL}/api/stats/chart-data", timeout=5)
            if r.status_code == 200:
                data = r.json()
                has_keys = all(k in data for k in ["by_category", "by_status", "by_month", "by_priority"])
                self.log("图表数据", has_keys, "数据完整")
                return data
            else:
                self.log("图表数据", False, f"Status: {r.status_code}")
                return None
        except Exception as e:
            self.log("图表数据", False, str(e))
            return None
    
    def test_stats_by_month(self):
        """测试月度统计"""
        try:
            r = requests.get(f"{BASE_URL}/api/stats/by-month", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("月度统计", isinstance(data, list), f"共 {len(data)} 个月")
                return data
            else:
                self.log("月度统计", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("月度统计", False, str(e))
            return []
    
    # ========== 用户管理测试 ==========
    
    def test_get_users(self, token):
        """测试获取用户列表"""
        if not token:
            self.log("获取用户列表", False, "无token")
            return []
        try:
            r = requests.get(f"{BASE_URL}/api/users", 
                          headers={'Authorization': f'Bearer {token}'}, 
                          timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("获取用户列表", len(data) > 0, f"共 {len(data)} 个用户")
                return data
            else:
                self.log("获取用户列表", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("获取用户列表", False, str(e))
            return []
    
    def test_create_user(self, token):
        """测试创建用户"""
        if not token:
            self.log("创建用户", False, "无token")
            return None
        data = {
            "username": f"testuser_{int(time.time())}",
            "password": "test123456",
            "role": "user",
            "display_name": "测试用户"
        }
        try:
            r = requests.post(f"{BASE_URL}/api/users", 
                            json=data,
                            headers={'Authorization': f'Bearer {token}'}, 
                            timeout=5)
            if r.status_code == 200:
                result = r.json()
                self.log("创建用户", "id" in result, f"ID: {result.get('id')}")
                return result.get('id')
            else:
                self.log("创建用户", False, f"Status: {r.status_code}")
                return None
        except Exception as e:
            self.log("创建用户", False, str(e))
            return None
    
    def test_delete_user(self, user_id, token):
        """测试删除用户"""
        if not token or not user_id:
            return False
        try:
            r = requests.delete(f"{BASE_URL}/api/users/{user_id}",
                              headers={'Authorization': f'Bearer {token}'},
                              timeout=5)
            self.log("删除用户", r.status_code == 200, f"Status: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            self.log("删除用户", False, str(e))
            return False
    
    # ========== 权限测试 ==========
    
    def test_unauthorized_access(self, endpoint):
        """测试未授权访问"""
        try:
            r = requests.get(f"{BASE_URL}/{endpoint}", timeout=5)
            self.log(f"未授权访问 {endpoint}", r.status_code == 401, f"Status: {r.status_code}")
        except Exception as e:
            self.log(f"未授权访问 {endpoint}", False, str(e))
    
    # ========== 筛选测试 ==========
    
    def test_filter_by_status(self):
        """测试按状态筛选"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals?status=pending", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("状态筛选(pending)", all(p["status"]=="pending" for p in data), f"共 {len(data)} 条")
                return data
            else:
                self.log("状态筛选(pending)", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("状态筛选(pending)", False, str(e))
            return []
    
    def test_filter_by_category(self):
        """测试按分类筛选"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals?category=流程优化", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("分类筛选(流程优化)", all(p["category"]=="流程优化" for p in data), f"共 {len(data)} 条")
                return data
            else:
                self.log("分类筛选(流程优化)", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("分类筛选(流程优化)", False, str(e))
            return []
    
    # ========== 运行完整测试 ==========
    
    def run_full_test(self, round_num):
        print(f"\n{'='*50}")
        print(f"  第 {round_num} 轮测试 - {self.test_name}")
        print(f"{'='*50}")
        
        # 1. 健康检查
        self.test_health()
        
        # 2. 登录测试
        token = self.test_login_success()
        self.test_login_fail()
        
        # 3. 创建提案
        new_id = self.test_create_proposal()
        
        # 4. 获取列表
        self.test_get_proposals()
        
        # 5. 获取单个提案
        if new_id:
            self.test_get_proposal_by_id(new_id, token)
            
            # 6. 更新状态
            if token:
                self.test_update_proposal(new_id, token)
                self.test_update_to_approved(new_id, token)
                self.test_update_to_completed(new_id, token)
        
        # 7. 筛选测试
        self.test_filter_by_status()
        self.test_filter_by_category()
        
        # 8. 统计测试
        self.test_stats_overview()
        self.test_stats_by_category()
        self.test_stats_chart_data()
        self.test_stats_by_month()
        
        # 9. 用户管理
        if token:
            self.test_get_users(token)
            new_user_id = self.test_create_user(token)
            if new_user_id:
                self.test_delete_user(new_user_id, token)
        
        # 10. 权限测试
        self.test_unauthorized_access("api/users")
        
        # 11. 边界测试
        self.test_get_nonexistent()
        
        # 12. 删除提案
        if new_id and token:
            self.test_delete_proposal(new_id, token)
        
        return self.passed, self.failed
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"  测试总结 - {self.test_name}")
        print(f"{'='*50}")
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {self.passed}")
        print(f"  ❌ 失败: {self.failed}")
        print(f"  成功率: {self.passed/total*100:.1f}%")
        print(f"{'='*50}")

def main():
    print("="*50)
    print("  改善提案系统 - 完整功能测试")
    print("="*50)
    
    tester = ProposalSystemTester("完整功能测试")
    
    for i in range(1, 4):
        tester.run_full_test(i)
        time.sleep(0.5)
    
    tester.print_summary()
    
    return tester.passed, tester.failed

if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)
