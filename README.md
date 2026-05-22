# MCP Memory Server

MCP 服务器，为 Claude Code 提供跨会话的长期记忆功能。

## 工具

- `add_memory` — 将文本存入记忆库，返回记忆 ID
- `search_memory` — 用语义搜索检索记忆
- `delete_memory` — 按 ID 删除指定记忆
- `list_memories` — 分页列出所有记忆（支持 offset/limit）
- `memory_stats` — 查看记忆库总数

## 安装

```bash
pip install -r requirements.txt
```

模型 `BAAI/bge-base-zh-v1.5` 设置了 `local_files_only=True`，需要**预先手动下载**到本地缓存，否则 MCP 服务启动时会报错。这样做是为了避免启动时联网认证导致卡顿或失败（尤其网络不稳定时）。

手动下载方式：

```bash
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-zh-v1.5')"
```

## 配置 Claude Code

在项目根目录的 `.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "memory": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/mcp-memory-server/memory_server.py"]
    }
  }
}
```

并在 `.claude/settings.json` 中启用：

```json
{
  "enableAllProjectMcpServers": true
}
```

## 关键注意

- `ServerCapabilities()` 必须显式声明 `tools=ToolsCapability()`，否则 Claude Code 不会发现工具
