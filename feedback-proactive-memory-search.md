---
name: proactive-memory-search
description: Always search MCP memory at conversation start and when user questions relate to stored knowledge
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d7895694-d2a0-431e-b8b1-38aa10671001
---

每次对话开始时，**必须先调用 `mcp__memory__search_memory`** 搜索与用户问题相关的记忆。不要等到用户手动要求才查。

**Why:** 用户搭建了 MCP memory + Chroma 的 RAG 系统，如果我不主动检索，这个系统形同虚设。用户明确要求自动检索。

**How to apply:** 
1. 对话开始或用户提出问题时，先用 `search_memory` 搜索相关记忆
2. 将搜索结果作为上下文融入回答
3. 不要让用户感觉到"又要手动翻记忆"的摩擦
4. 如果搜索结果为空或不相关，正常回答即可，不用特别说明
