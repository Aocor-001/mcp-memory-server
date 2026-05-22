import json
import uuid
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

_chroma_client = None
_collection = None
_model = None

def _get_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        from chromadb import PersistentClient
        _chroma_client = PersistentClient(path="记忆库路径")
        _collection = _chroma_client.get_or_create_collection("collection")
    return _collection

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-base-zh-v1.5", local_files_only=True)
    return _model

# 创建 MCP 服务器
server = Server("memory-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_memory",
            description="从我的个人记忆库中检索相关信息。当需要回忆过去的笔记、想法或事实时使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询语句"},
                    "n_results": {"type": "integer", "description": "返回结果数量", "default": 3}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="add_memory",
            description="将重要的信息存储到我的长期记忆库中。当用户明确说'记住'、'记一下'，或者分享了需要保存的想法、笔记时使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "要记住的文本内容"},
                    "source": {"type": "string", "description": "这段记忆的来源，比如'用户口语'", "default": "用户口语"}
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="delete_memory",
            description="从记忆库中删除一条记忆。需要提供记忆的ID。",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "要删除的记忆ID"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="list_memories",
            description="分页列出记忆库中的所有记忆。用于浏览和管理。",
            inputSchema={
                "type": "object",
                "properties": {
                    "offset": {"type": "integer", "description": "偏移量", "default": 0},
                    "limit": {"type": "integer", "description": "每页数量", "default": 20}
                }
            }
        ),
        types.Tool(
            name="memory_stats",
            description="获取记忆库的统计信息，如总记忆数。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name not in ("search_memory", "add_memory", "delete_memory", "list_memories", "memory_stats"):
        raise ValueError(f"Unknown tool: {name}")

    try:
        model = _get_model()
    except Exception as e:
        return [types.TextContent(type="text", text=f"模型加载失败: {e}")]

    try:
        collection = _get_collection()
    except Exception as e:
        return [types.TextContent(type="text", text=f"数据库连接失败: {e}")]

    if name == "add_memory":
        content = arguments["content"]
        source = arguments.get("source", "用户口语")
        mem_id = str(uuid.uuid4())

        try:
            emb = model.encode(content).tolist()
            collection.add(
                documents=[content],
                embeddings=[emb],
                metadatas=[{"source": source}],
                ids=[mem_id]
            )
        except Exception as e:
            return [types.TextContent(type="text", text=f"记忆存储失败: {e}")]

        return [types.TextContent(type="text", text=f"已记住 (ID: {mem_id}): {content}")]

    if name == "delete_memory":
        memory_id = arguments["memory_id"]
        try:
            collection.delete(ids=[memory_id])
        except Exception as e:
            return [types.TextContent(type="text", text=f"删除失败: {e}")]
        return [types.TextContent(type="text", text=f"已删除记忆: {memory_id}")]

    if name == "list_memories":
        offset = arguments.get("offset", 0)
        limit = arguments.get("limit", 20)
        try:
            result = collection.get(offset=offset, limit=limit, include=["documents", "metadatas"])
        except Exception as e:
            return [types.TextContent(type="text", text=f"列表获取失败: {e}")]

        ids = result.get("ids", [])
        if not ids:
            return [types.TextContent(type="text", text="记忆库为空。")]

        lines = []
        for i, mem_id in enumerate(ids):
            doc = result["documents"][i] if result.get("documents") else ""
            meta = result["metadatas"][i] if result.get("metadatas") else {}
            source = meta.get("source", "未知") if isinstance(meta, dict) else "未知"
            lines.append(f"[{mem_id}] ({source}) {doc}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    if name == "memory_stats":
        try:
            count = collection.count()
        except Exception as e:
            return [types.TextContent(type="text", text=f"统计获取失败: {e}")]
        return [types.TextContent(type="text", text=f"记忆库共 {count} 条记忆。")]

    # search_memory
    query = arguments["query"]
    n_results = arguments.get("n_results", 3)

    try:
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
    except Exception as e:
        return [types.TextContent(type="text", text=f"记忆检索失败: {e}")]

    docs = results.get("documents", [[]])[0]
    if not docs:
        return [types.TextContent(type="text", text="记忆库中没有找到相关内容。")]

    formatted = []
    for i, doc in enumerate(docs):
        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
        source = meta.get("source", "未知") if isinstance(meta, dict) else "未知"
        formatted.append(f"--- 记忆片段 {i+1} ---\n{doc}\n(来源: {source})")

    return [types.TextContent(type="text", text="\n\n".join(formatted))]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="memory-server",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability()
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
