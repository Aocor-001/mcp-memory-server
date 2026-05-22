# MCP Memory Server

基于 MCP 协议的长期记忆服务，为 Claude Code 提供跨会话的语义记忆能力。

## 架构

```
Claude Code ── MCP/stdio ── memory_server.py
                                │
                    ┌───────────┴───────────┐
                    │                       │
              embedding 模型           Chroma 向量库
          (bge-base-zh-v1.5)        (PersistentClient)
```

- **嵌入模型**: `BAAI/bge-base-zh-v1.5` — 中文语义向量化
- **向量数据库**: Chroma (PersistentClient) — 本地持久化存储
- **通信协议**: MCP stdio — Claude Code 进程间通信

## 工具

| 工具 | 用途 |
|---|---|
| `add_memory` | 存入记忆，返回 ID |
| `search_memory` | 语义搜索，返回相关记忆片段 |
| `delete_memory` | 按 ID 删除 |
| `list_memories` | 分页浏览（offset/limit） |
| `memory_stats` | 查看总条数 |

## 安装

```
pip install -r requirements.txt
```

### 手动下载模型

默认启用 `local_files_only=True`，需预先下载 embedding 模型：

```bash
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-zh-v1.5')"
```

> 这是为了避免网络不稳定时，启动阶段联网认证导致 MCP 连接超时。

## 配置 Claude Code

### 1. `.mcp.json`

```json
{
  "mcpServers": {
    "memory": {
      "type": "stdio",
      "command": "python3",
      "args": ["path/to/memory_server.py"]
    }
  }
}
```

### 2. `.claude/settings.json`

```json
{
  "enableAllProjectMcpServers": true
}
```

### 3. 可选：自动触发记忆搜索

MCP 工具默认不会自动调用。如果希望每次新对话开始时 Claude 自动搜索记忆，可以配置 SessionStart hook，通过 `additionalContext` 注入启动指令：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"会话已启动。立即搜索记忆库，检索用户偏好和历史上下文。\"}}'"
          }
        ]
      }
    ]
  }
}
```

链路：

> 新会话 → SessionStart hook 注入指令 → Claude 自动搜索记忆 → 融入回答

## 关键设计决策

| 决策 | 原因 |
|---|---|
| `local_files_only=True` | 网络不稳定时启动联网认证会超时，模型需手动下载 |
| `ServerCapabilities` 显式声明 `tools=ToolsCapability()` | 否则 Claude Code 不会发现工具 |
| `PersistentClient` | 本地持久化，无需额外数据库服务 |
| SessionStart hook | 比 CLAUDE.md / MEMORY.md 更可靠可控 |
| embedding 模型懒加载 | 首次调用才加载，减少启动延迟 |
| try/except 全包裹 | 任何错误返回中文提示，不崩溃 |
