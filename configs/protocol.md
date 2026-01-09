# MCP Multi-Model Collaboration Protocol

## Message Format
```json
{
  "message_id": "uuid",
  "turn": 1,
  "sender": "model_a",
  "recipient": "model_b",
  "content": "Analysis of page 5 shows missing timestamp",
  "tool_calls": [
    {
      "name": "search_memory",
      "params": {"query": "timestamp evidence"}
    }
  ],
  "metadata": {
    "priority": "high",
    "case_id": "2024-CIV-001"
  }
}
