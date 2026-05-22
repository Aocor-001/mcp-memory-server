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
        _chroma_client = PersistentClient(path="/home/zyy/chroma_data")
        _collection = _chroma_client.get_or_create_collection("my_memory")
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
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name not in ("search_memory", "add_memory"):
        raise ValueError(f"Unknown tool: {name}")

    model = _get_model()
    collection = _get_collection()

    if name == "add_memory":
        content = arguments["content"]
        source = arguments.get("source", "用户口语")

        emb = model.encode(content).tolist()
        collection.add(
            documents=[content],
            embeddings=[emb],
            metadatas=[{"source": source}],
            ids=[str(uuid.uuid4())]
        )
        return [types.TextContent(type="text", text=f"已记住: {content}")]

    # search_memory
    query = arguments["query"]
    n_results = arguments.get("n_results", 3)

    # 将查询向量化
    query_embedding = model.encode(query).tolist()

    # 在 Chroma 中检索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas"]
    )
    
    # 整理成可读文本
    docs = results.get("documents", [[]])[0]
    if not docs:
        return [types.TextContent(type="text", text="记忆库中没有找到相关内容。")]
    
    formatted = []
    for i, doc in enumerate(docs):
        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
        formatted.append(f"--- 记忆片段 {i+1} ---\n{doc}\n(来源: {meta})")
    
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
