#!/usr/bin/env python3
"""
改善提案收集系统 - 自动化测试
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8004"

class ProposalTester:
    def __init__(self):
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
    
    def test_health(self):
        """测试服务健康状态"""
        try:
            r = requests.get(BASE_URL, timeout=5)
            self.log("健康检查", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            self.log("健康检查", False, str(e))
    
    def test_create_proposal(self):
        """测试创建提案"""
        data = {
            "title": f"测试提案-{int(time.time())}",
            "category": "流程优化",
            "problem_desc": "这是一个测试问题描述",
            "solution": "这是测试解决方案",
            "priority": "normal",
            "submitter": "测试员"
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
    
    def test_get_proposal_by_id(self, proposal_id):
        """测试获取单个提案"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals/{proposal_id}", timeout=5)
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
    
    def test_update_proposal(self, proposal_id):
        """测试更新提案状态"""
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "reviewing"}, timeout=5)
            if r.status_code == 200:
                self.log(f"更新提案 #{proposal_id}", True, "状态 -> reviewing")
                return True
            else:
                self.log(f"更新提案 #{proposal_id}", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"更新提案 #{proposal_id}", False, str(e))
            return False
    
    def test_update_to_approved(self, proposal_id):
        """测试更新为已采纳"""
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "approved"}, timeout=5)
            if r.status_code == 200:
                self.log(f"采纳提案 #{proposal_id}", True, "状态 -> approved")
                return True
            else:
                self.log(f"采纳提案 #{proposal_id}", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"采纳提案 #{proposal_id}", False, str(e))
            return False
    
    def test_update_to_completed(self, proposal_id):
        """测试更新为已完成"""
        try:
            r = requests.put(f"{BASE_URL}/api/proposals/{proposal_id}", 
                          json={"status": "completed"}, timeout=5)
            if r.status_code == 200:
                self.log(f"完成提案 #{proposal_id}", True, "状态 -> completed")
                return True
            else:
                self.log(f"完成提案 #{proposal_id}", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"完成提案 #{proposal_id}", False, str(e))
            return False
    
    def test_delete_proposal(self, proposal_id):
        """测试删除提案"""
        try:
            r = requests.delete(f"{BASE_URL}/api/proposals/{proposal_id}", timeout=5)
            if r.status_code == 200:
                self.log(f"删除提案 #{proposal_id}", True, "已删除")
                return True
            else:
                self.log(f"删除提案 #{proposal_id}", False, f"Status: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"删除提案 #{proposal_id}", False, str(e))
            return False
    
    def test_get_nonexistent(self):
        """测试获取不存在的提案"""
        try:
            r = requests.get(f"{BASE_URL}/api/proposals/99999", timeout=5)
            self.log("获取不存在的提案", r.status_code == 404, f"Status: {r.status_code}")
        except Exception as e:
            self.log("获取不存在的提案", False, str(e))
    
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
    
    def test_categories(self):
        """测试获取分类列表"""
        try:
            r = requests.get(f"{BASE_URL}/api/categories", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.log("获取分类列表", len(data) > 0, f"共 {len(data)} 个分类")
                return data
            else:
                self.log("获取分类列表", False, f"Status: {r.status_code}")
                return []
        except Exception as e:
            self.log("获取分类列表", False, str(e))
            return []
    
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
    
    def run_full_test(self, round_num):
        print(f"\n{'='*50}")
        print(f"  第 {round_num} 轮测试")
        print(f"{'='*50}")
        
        # 1. 健康检查
        self.test_health()
        
        # 2. 创建提案
        new_id = self.test_create_proposal()
        
        # 3. 获取列表
        self.test_get_proposals()
        
        # 4. 获取单个提案
        if new_id:
            self.test_get_proposal_by_id(new_id)
            
            # 5. 更新状态：审核中
            self.test_update_proposal(new_id)
            
            # 6. 更新状态：已采纳
            self.test_update_to_approved(new_id)
            
            # 7. 更新状态：已完成
            self.test_update_to_completed(new_id)
            
            # 8. 删除提案
            self.test_delete_proposal(new_id)
        
        # 9. 获取不存在的提案
        self.test_get_nonexistent()
        
        # 10. 统计概览
        self.test_stats_overview()
        
        # 11. 分类统计
        self.test_stats_by_category()
        
        # 12. 获取分类
        self.test_categories()
        
        # 13. 状态筛选
        self.test_filter_by_status()
        
        return self.passed, self.failed
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"  测试总结")
        print(f"{'='*50}")
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {self.passed}")
        print(f"  ❌ 失败: {self.failed}")
        print(f"  成功率: {self.passed/total*100:.1f}%")
        print(f"{'='*50}")

def main():
    print("="*50)
    print("  改善提案收集系统 - 连续10轮测试")
    print("="*50)
    
    tester = ProposalTester()
    
    for i in range(1, 11):
        tester.run_full_test(i)
        time.sleep(0.5)  # 短暂延迟
    
    tester.print_summary()
    
    # 返回最终结果
    return tester.passed, tester.failed

if __name__ == "__main__":
    passed, failed = main()
    exit(0 if failed == 0 else 1)
