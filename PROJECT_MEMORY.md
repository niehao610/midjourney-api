# Midjourney API 项目记忆

## 项目概览

### 项目简介
这是一个基于 FastAPI 构建的 Midjourney API 服务，提供图片生成、放大、变体等功能。已完成完整的认证系统集成。

### 技术栈
- **框架**: FastAPI
- **数据库**: MySQL (使用 aiomysql + SQLAlchemy)
- **认证**: Bearer Token 认证
- **异步**: asyncio/aiohttp
- **日志**: loguru

### 项目结构
```
midjourney-api/
├── app/                    # 应用主目录
│   ├── routers.py         # API路由定义 (已添加认证)
│   ├── handler.py         # 请求处理器
│   ├── schema.py          # Pydantic模型
│   └── server.py          # FastAPI应用配置
├── lib/                   # 核心库
│   ├── database.py        # 数据库连接和表定义 (含user_info表)
│   ├── db_operations.py   # 数据库操作类 (含用户操作)
│   ├── auth.py           # 认证模块 (NEW)
│   └── api/              # 外部API集成
├── util/                  # 工具模块
├── task/                  # 任务处理
├── manage_users.py        # 用户管理脚本 (NEW)
├── test_auth.py          # 认证测试脚本 (NEW)
├── API_AUTH_README.md    # 认证系统文档 (NEW)
└── requirements.txt       # 依赖包
```

### 服务配置
- **默认端口**: 8086
- **API前缀**: `/v1/api/trigger`
- **启动文件**: `server.py`

## 认证系统实现

### 核心组件

#### 1. 数据库表 user_info
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 2. 认证模块 (lib/auth.py)
- `AuthBearer` - 自定义Bearer认证类
- `get_current_user()` - 获取当前用户信息
- `check_user_token_limit()` - 检查token限制
- `consume_user_token_by_app_key()` - 消费token

#### 3. 数据库操作 (lib/db_operations.py)
- `UserInfoOperations` 类提供用户相关操作
- `get_user_by_app_key()` - 根据app_key查询用户
- `create_user()` - 创建用户
- `update_token_usage()` - 更新token使用量

### API端点认证配置

#### 需要认证 + 消费Token (1个Token/次)
- `POST /imagine` - 图片生成
- `POST /upscale` - 图片放大
- `POST /variation` - 生成变体
- `POST /reset` - 重置任务
- `POST /describe` - 图片描述
- `POST /solo_variation` - 独立变体
- `POST /solo_low_variation` - 低变体
- `POST /solo_high_variation` - 高变体
- `POST /expand` - 图片扩展
- `POST /zoomout` - 图片缩放

#### 需要认证但不消费Token
- `POST /upload` - 文件上传
- `POST /message` - 发送消息
- `POST /queue/release` - 释放队列
- `GET /task/{task_id}` - 查询任务详情
- `GET /tasks` - 查询任务列表

#### 不需要认证
- `POST /midjourney/result` - 接收Midjourney回调结果

### 认证流程
1. 客户端在HTTP请求头中添加: `Authorization: Bearer <app_key>`
2. `AuthBearer` 类验证Bearer格式
3. `verify_token()` 方法验证app_key有效性
4. `get_current_user()` 获取用户信息
5. `check_user_token_limit()` 检查token余额
6. 执行API操作
7. `consume_user_token_by_app_key()` 消费token (如需要)

### 错误处理
- **403 Forbidden**: 认证失败、用户不存在
- **429 Too Many Requests**: Token余额不足
- **500 Internal Server Error**: 系统错误

## 管理工具

### 用户管理脚本 (manage_users.py)
```bash
# 创建用户
python manage_users.py create <username> [token_total]

# 查询用户信息
python manage_users.py info <username>
python manage_users.py info-key <app_key>

# 更新Token总数
python manage_users.py update-tokens <app_key> <total>

# 重置使用量
python manage_users.py reset-usage <app_key>
```

### 认证测试脚本 (test_auth.py)
- 自动化测试认证功能
- 验证各种认证场景
- 测试token消费机制

## 使用示例

### Python客户端
```python
import requests

app_key = "your_app_key_here"
headers = {
    "Authorization": f"Bearer {app_key}",
    "Content-Type": "application/json"
}

data = {"prompt": "a beautiful sunset", "picurl": None}
response = requests.post(
    "http://localhost:8086/v1/api/trigger/imagine",
    json=data, headers=headers
)
```

### cURL
```bash
curl -X POST "http://localhost:8086/v1/api/trigger/imagine" \
  -H "Authorization: Bearer your_app_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset", "picurl": null}'
```

## 部署和运行

### 环境变量
```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=luban_v2v
DB_USER=root
DB_PASSWORD=123456
```

### 启动服务
```bash
python server.py
```

### 数据库初始化
系统启动时自动创建表结构。

## 重要提醒

1. **安全性**: app_key需要妥善保管，不要泄露
2. **Token管理**: 定期检查用户token使用情况
3. **监控**: 关注认证失败日志
4. **备份**: 定期备份user_info表数据
5. **扩展**: 可考虑添加token过期机制、速率限制等

## 故障排除

### 常见问题
- 认证失败 → 检查app_key是否正确
- Token不足 → 使用管理脚本增加token
- 数据库连接 → 检查环境变量配置
- 服务启动 → 检查端口占用情况

### 日志位置
系统使用loguru记录日志，包含认证和token消费信息。 