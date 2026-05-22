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

`local_files_only=True`，需预先下载 embedding 模型到本地缓存：

```bash
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-zh-v1.5')"
```

> 这是为了避免网络不稳定时，启动阶段联网认证导致 MCP 连接超时。

## 配置 Claude Code

### 1. `.mcp.json`（项目根目录）

```json
{
  "mcpServers": {
    "memory": {
      "type": "stdio",
      "command": "python3",
      "args": [""]
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

## 使用建议：让记忆真正生效

MCP 工具默认不会自动调用——Claude 不会主动搜索记忆。要让它变成真正的 RAG，需要在 Claude Code 的**内置记忆系统**中写入一条引导指令：

在 `/home/zyy/.claude/projects/-home-zyy/memory/` 中创建反馈记忆，要求每次对话开始时自动调用 `search_memory`。这样链路变为：

> 用户提问 → Claude 自动搜记忆 → 找到相关上下文 → 融入回答

具体配置见 `MEMORY.md`。

## 关键点

- `ServerCapabilities()` **必须**显式声明 `tools=ToolsCapability()`，否则 Claude Code 不会发现工具
- 所有工具调用都有 `try/except` 错误处理，模型加载或数据库操作失败会返回中文错误信息
- 项目源文件位于 `mcp-memory-server/`，运行实例部署在 `chroma_data/`
