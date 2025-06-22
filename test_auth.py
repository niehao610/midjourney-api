#!/usr/bin/env python3
"""
API认证系统测试脚本
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class APITester:
    def __init__(self, base_url: str = "http://localhost:8086"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_request(self, method: str, endpoint: str, app_key: str = None, data: Dict = None) -> Dict[str, Any]:
        """测试API请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if app_key:
            headers["Authorization"] = f"Bearer {app_key}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    result = {
                        "status_code": response.status,
                        "response": await response.json() if response.content_type == "application/json" else await response.text()
                    }
            else:
                async with self.session.post(url, headers=headers, json=data) as response:
                    result = {
                        "status_code": response.status,
                        "response": await response.json() if response.content_type == "application/json" else await response.text()
                    }
            
            return result
        except Exception as e:
            return {"status_code": 0, "error": str(e)}


async def main():
    """主测试函数"""
    print("🧪 API认证系统测试")
    print("=" * 50)
    
    # 测试用的App Key（需要提前创建）
    test_app_key = "test_app_key_123456"  # 请替换为实际的App Key
    invalid_app_key = "invalid_key_123"
    
    async with APITester() as tester:
        
        # 测试用例定义
        test_cases = [
            {
                "name": "无认证头的请求",
                "method": "POST",
                "endpoint": "/v1/api/trigger/imagine",
                "app_key": None,
                "data": {"prompt": "test prompt", "picurl": None},
                "expected_status": 403
            },
            {
                "name": "无效App Key",
                "method": "POST", 
                "endpoint": "/v1/api/trigger/imagine",
                "app_key": invalid_app_key,
                "data": {"prompt": "test prompt", "picurl": None},
                "expected_status": 403
            },
            {
                "name": "有效认证 - imagine",
                "method": "POST",
                "endpoint": "/v1/api/trigger/imagine", 
                "app_key": test_app_key,
                "data": {"prompt": "test prompt", "picurl": None},
                "expected_status": 200
            },
            {
                "name": "查询任务（需要认证）",
                "method": "GET",
                "endpoint": "/v1/api/trigger/tasks",
                "app_key": test_app_key,
                "data": None,
                "expected_status": 200
            },
            {
                "name": "查询任务（无认证）",
                "method": "GET", 
                "endpoint": "/v1/api/trigger/tasks",
                "app_key": None,
                "data": None,
                "expected_status": 403  
            },
            {
                "name": "文件上传（需要认证，不消费Token）",
                "method": "POST",
                "endpoint": "/v1/api/trigger/upload", 
                "app_key": test_app_key,
                "data": None,  # 实际测试时需要文件数据
                "expected_status": [200, 400]  # 可能因为没有文件数据而返回400
            },
            {
                "name": "Midjourney回调（不需要认证）",
                "method": "POST",
                "endpoint": "/v1/api/trigger/midjourney/result",
                "app_key": None,
                "data": {
                    "type": "end",
                    "id": 123456,
                    "content": "test content",
                    "attachments": [],
                    "embeds": [],
                    "trigger_id": "test_trigger"
                },
                "expected_status": 200
            }
        ]
        
        # 执行测试
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试 {i}: {test_case['name']}")
            print("-" * 30)
            
            result = await tester.test_request(
                method=test_case['method'],
                endpoint=test_case['endpoint'],
                app_key=test_case['app_key'],
                data=test_case['data']
            )
            
            # 判断结果
            expected_status = test_case['expected_status']
            actual_status = result['status_code']
            
            if isinstance(expected_status, list):
                is_success = actual_status in expected_status
            else:
                is_success = actual_status == expected_status
            
            if is_success:
                print(f"✅ 通过 - 状态码: {actual_status}")
                passed += 1
            else:
                print(f"❌ 失败 - 期望状态码: {expected_status}, 实际状态码: {actual_status}")
                failed += 1
            
            # 显示响应内容（仅在失败或需要调试时）
            if not is_success or actual_status >= 400:
                print(f"   响应: {json.dumps(result.get('response', {}), indent=2, ensure_ascii=False)}")
        
        # 总结
        print("\n" + "=" * 50)
        print(f"📊 测试总结")
        print(f"   通过: {passed}")
        print(f"   失败: {failed}")
        print(f"   总计: {passed + failed}")
        
        if failed == 0:
            print("🎉 所有测试通过！认证系统工作正常。")
        else:
            print("⚠️  部分测试失败，请检查认证系统配置。")


async def test_token_consumption():
    """测试Token消费功能"""
    print("\n🔋 Token消费测试")
    print("=" * 30)
    
    # 这里需要一个真实的App Key来测试
    test_app_key = "test_app_key_123456"  # 请替换为实际的App Key
    
    async with APITester() as tester:
        # 先查询用户信息（假设有查询接口）
        print("📊 查询用户Token余额...")
        
        # 执行一个消费Token的操作
        print("💰 执行Token消费操作...")
        result = await tester.test_request(
            method="POST",
            endpoint="/v1/api/trigger/imagine",
            app_key=test_app_key,
            data={"prompt": "test token consumption", "picurl": None}
        )
        
        if result['status_code'] == 200:
            print("✅ Token消费成功")
        elif result['status_code'] == 429:
            print("⚠️  Token余额不足")  
        else:
            print(f"❌ 操作失败: {result}")


if __name__ == "__main__":
    print("请确保：")
    print("1. API服务器正在运行（端口8086）")
    print("2. 数据库连接正常")
    print("3. 已创建测试用户，App Key为: test_app_key_123456")
    print("   如果没有，请运行: python manage_users.py create testuser")
    print()
    
    # 运行基础认证测试
    asyncio.run(main())
    
    # 运行Token消费测试（可选）
    # asyncio.run(test_token_consumption()) 