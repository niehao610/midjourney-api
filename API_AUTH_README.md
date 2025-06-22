# Midjourney API 认证系统

## 概述

本项目已集成完整的API认证系统，所有的HTTP API端点现在都需要通过`Authorization`头进行身份验证。

## 认证方式

### HTTP请求头
所有API请求都需要在HTTP请求头中包含：

```
Authorization: Bearer <your_app_key>
```

### Token消费机制
- 每次调用需要消费token的API（如imagine、upscale、variation等）都会从用户的token余额中扣除1个token
- 查询类API（如获取任务状态）不消费token
- 上传和消息发送API仅需要认证，不消费token

## 用户管理

### 创建用户
```bash
python manage_users.py create <username> [token_total]
```
例子：
```bash
# 创建用户，默认100个token
python manage_users.py create testuser

# 创建用户，指定token数量
python manage_users.py create testuser 500
```

### 查询用户信息
```bash
# 按用户名查询
python manage_users.py info <username>

# 按App Key查询
python manage_users.py info-key <app_key>
```

### 更新用户Token总数
```bash
python manage_users.py update-tokens <app_key> <new_total>
```

### 重置用户Token使用量
```bash
python manage_users.py reset-usage <app_key>
```

## API端点认证状态

### 需要认证 + 消费Token的端点
- `POST /v1/api/trigger/imagine` - 创建图片生成任务
- `POST /v1/api/trigger/upscale` - 图片放大
- `POST /v1/api/trigger/variation` - 生成变体
- `POST /v1/api/trigger/reset` - 重置任务
- `POST /v1/api/trigger/describe` - 图片描述
- `POST /v1/api/trigger/solo_variation` - 独立变体
- `POST /v1/api/trigger/solo_low_variation` - 低变体
- `POST /v1/api/trigger/solo_high_variation` - 高变体
- `POST /v1/api/trigger/expand` - 图片扩展
- `POST /v1/api/trigger/zoomout` - 图片缩放

### 需要认证但不消费Token的端点
- `POST /v1/api/trigger/upload` - 文件上传
- `POST /v1/api/trigger/message` - 发送消息
- `POST /v1/api/trigger/queue/release` - 释放队列
- `GET /v1/api/trigger/task/{task_id}` - 查询任务详情
- `GET /v1/api/trigger/tasks` - 查询任务列表

### 不需要认证的端点
- `POST /v1/api/trigger/midjourney/result` - 接收Midjourney回调结果

## 错误响应

### 认证失败
```json
{
    "detail": "Invalid token or expired token."
}
```
HTTP状态码：403

### Token余额不足
```json
{
    "detail": "Token limit exceeded. Please contact administrator."
}
```
HTTP状态码：429

### 用户不存在
```json
{
    "detail": "User not found."
}
```
HTTP状态码：403

## API调用示例

### Python示例
```python
import requests

app_key = "your_app_key_here"
headers = {
    "Authorization": f"Bearer {app_key}",
    "Content-Type": "application/json"
}

# 创建图片生成任务
data = {
    "prompt": "a beautiful sunset over the ocean",
    "picurl": None
}

response = requests.post(
    "http://localhost:8086/v1/api/trigger/imagine",
    json=data,
    headers=headers
)

print(response.json())
```

### cURL示例
```bash
curl -X POST "http://localhost:8086/v1/api/trigger/imagine" \
  -H "Authorization: Bearer your_app_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset over the ocean", "picurl": null}'
```

## 数据库表结构

### user_info表
```sql
CREATE TABLE `user_info` (
  `id`  bigint(20) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(64) NOT NULL DEFAULT '',
  `app_key` varchar(64) NOT NULL DEFAULT '',
  `token_total` int(11) DEFAULT 0,
  `token_use`    int(11) DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uiq_user_name` (`user_name`),
  UNIQUE KEY `uiq_app_key` (`app_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Midjourney 用户信息表';
```

## 注意事项

1. **App Key安全性**：请妥善保管您的App Key，不要在公共场所或代码库中明文暴露
2. **Token管理**：请合理规划Token使用，避免超出限制
3. **错误处理**：建议在客户端代码中添加适当的错误处理逻辑
4. **Rate Limiting**：系统会根据Token余额自动限制API调用频率

## 故障排除

### 常见问题
1. **401 Unauthorized**：检查Authorization头是否正确设置
2. **403 Forbidden**：检查App Key是否有效
3. **429 Too Many Requests**：检查Token余额是否充足
4. **500 Internal Server Error**：检查数据库连接和服务器日志

### 日志查看
系统日志会记录认证失败、Token消费等关键信息，可通过查看日志文件进行故障排除。 