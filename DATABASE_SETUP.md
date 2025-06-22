# 数据库设置说明

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

创建 `.env` 文件，添加以下配置：

```env
# Discord Bot 配置
GUILD_ID=your_guild_id
CHANNEL_ID=your_channel_id
USER_TOKEN=your_user_token
DRAW_VERSION=your_draw_version

# 代理配置
PROXY_URL=http://127.0.0.1:33210

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=luban_v2v
DB_USER=root
DB_PASSWORD=123456

# 日志级别
LOG_LEVEL=INFO
```

## 3. 创建数据库

确保MySQL服务正在运行，然后创建数据库：

```sql
CREATE DATABASE luban_v2v CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

## 4. 初始化数据库表

运行初始化脚本：

```bash
python init_db.py
```

## 5. 启动服务

```bash
python server.py
```

## 数据库功能说明

### 自动功能
- **任务创建**：调用任何Midjourney操作接口时自动在数据库创建任务记录
- **状态更新**：接收到 Midjourney 结果时自动更新任务状态和结果
- **连接管理**：服务启动时自动连接数据库，关闭时自动断开
- **唯一标识**：每个任务都有唯一的task_id(UUID)和trigger_id
- **参数记录**：自动记录图片索引、缩放系数、扩展方向等操作参数

### 查询接口

1. **根据trigger_id查询任务**：
   ```
   GET /v1/api/trigger/task/{trigger_id}
   ```

2. **根据task_id查询任务**：
   ```
   GET /v1/api/trigger/task_by_id/{task_id}
   ```

3. **查询任务列表**：
   ```
   GET /v1/api/trigger/tasks?status=SUCCESS&limit=10&offset=0
   ```

### 任务状态说明

- `NOT_START`：未开始
- `SUBMITTED`：已提交
- `IN_PROGRESS`：进行中
- `SUCCESS`：成功完成
- `FAILED`：失败
- `FAILURE`：失败

### 任务类型说明

- `generate`：生成图片
- `upscale`：放大图片
- `variation`：变化图片
- `solo_variation`：单独变化
- `solo_low_variation`：低质量变化
- `solo_high_variation`：高质量变化
- `expand`：扩展图片
- `zoomout`：缩小图片
- `reset`：重置
- `describe`：描述图片

## 数据表结构

```sql
CREATE TABLE `midjourney_task` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `task_name` varchar(64) NOT NULL DEFAULT '',
  `task_id` varchar(64) NOT NULL DEFAULT '',
  `trigger_id` varchar(32) NOT NULL DEFAULT '',
  `ref_pic_url` text DEFAULT NULL,
  `image_index` int(11) DEFAULT 0,
  `msg_id` bigint default 0,
  `msg_hash` varchar(64) DEFAULT '',
  `zoom_out` int(11) DEFAULT 0 COMMENT '图片扩大（Outpaint）系数，2x -> 50、1.5x -> 75',
  `direction` varchar(32) NOT NULL DEFAULT '' COMMENT '图片扩大方向，取值：left/right/up/down',
  `task_type` varchar(32) NOT NULL DEFAULT '' COMMENT 'imagine，U V pan zoom',
  `task_status` varchar(32) NOT NULL DEFAULT '' COMMENT 'SUCCESS FAILED FAILURE SUBMITTED IN_PROGRESS NOT_START',
  `result_url` text default NULL,
  `attachments` text default NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unq_task_id` (`task_id`),
  KEY `idx_trigger_id` (`trigger_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Midjourney 任务信息表';
``` 