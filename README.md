# MCP Memory Server

MCP 服务器，为 Claude Code 提供跨会话的长期记忆功能。

## 工具

- `add_memory` — 将文本存入记忆库
- `search_memory` — 用语义搜索检索记忆

## 安装

```bash
pip install -r requirements.txt
```

模型 `BAAI/bge-base-zh-v1.5` 首次运行时会自动下载缓存。

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
- 网络受限环境下，加载模型需加 `local_files_only=True`
