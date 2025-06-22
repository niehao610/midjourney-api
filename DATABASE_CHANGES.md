# 数据库表结构变更说明

## 主要变更

### 1. 新增字段

- **`task_id`** (varchar(64))：每个任务的唯一标识符，使用UUID生成
- **`image_index`** (int(11))：图片操作的索引，如upscale的第几张图片

### 2. 索引变更

- **唯一键变更**：从 `unq_trigger_id` 改为 `unq_task_id`
- **普通索引变更**：从 `idx_msg_id` 改为 `idx_trigger_id`
- **`trigger_id`不再唯一**：现在允许同一个trigger_id对应多个任务

### 3. 代码变更

#### 数据库操作类新增方法：
- `get_task_by_task_id()` - 根据task_id查询任务
- `update_task_status_by_task_id()` - 根据task_id更新状态
- `update_task_result_by_task_id()` - 根据task_id更新结果
- `delete_task_by_task_id()` - 根据task_id删除任务

#### 路由新增功能：
- 所有操作接口都会自动创建数据库记录
- 新增 `GET /v1/api/trigger/task_by_id/{task_id}` 查询接口
- 所有任务创建时自动生成UUID作为task_id

#### 参数记录增强：
- `upscale` 和 `variation` 操作自动记录 `image_index`
- `expand` 操作自动记录 `direction`
- `zoomout` 操作自动记录 `zoom_out` 系数

## 兼容性说明

- 原有的基于 `trigger_id` 的查询接口保持不变
- 新增基于 `task_id` 的查询接口
- 数据库表结构向后兼容

## 使用建议

1. **新项目**：建议使用 `task_id` 进行任务跟踪
2. **现有项目**：可以继续使用 `trigger_id`，同时逐步迁移到 `task_id`
3. **数据分析**：可以通过 `trigger_id` 聚合同一次操作的所有相关任务

## 数据迁移

如果你有现有的数据表，需要执行以下SQL来更新表结构：

```sql
-- 添加新字段
ALTER TABLE midjourney_task 
ADD COLUMN task_id varchar(64) NOT NULL DEFAULT '' AFTER task_name,
ADD COLUMN image_index int(11) DEFAULT 0 AFTER ref_pic_url;

-- 为现有数据生成task_id (需要自定义逻辑)
UPDATE midjourney_task SET task_id = UUID() WHERE task_id = '';

-- 删除旧索引
DROP INDEX unq_trigger_id ON midjourney_task;
DROP INDEX idx_msg_id ON midjourney_task;

-- 创建新索引
CREATE UNIQUE INDEX unq_task_id ON midjourney_task (task_id);
CREATE INDEX idx_trigger_id ON midjourney_task (trigger_id);
```

## 环境变量更新

确保 `.env` 文件包含正确的数据库配置：

```env
DB_NAME=luban_v2v
DB_PASSWORD=123456
``` 