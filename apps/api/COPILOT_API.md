# Copilot API Documentation

The Copilot API exposes the multi-agent market intelligence system via REST endpoints. It orchestrates RAG, Financial Analysis, and Alert agents to answer complex financial queries.

## Base URL
`/api/v1`

## Endpoints

### 1. Copilot Query

Process a user query through the multi-agent intelligence system.

- **URL**: `/copilot/query`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body

```json
{
  "query": "What are the financials of Foodie Media Berhad?",
  "session_id": "optional-session-id",
  "stream": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The natural language query to process |
| `session_id` | string | No | Optional ID for conversation history tracking |
| `stream` | boolean | No | Whether to stream the response (currently false) |

#### Response

```json
{
  "answer": "Foodie Media Berhad reported revenue of RM 12.56 million...",
  "confidence_score": 0.85,
  "sources": [...],
  "agents_used": ["rag", "financial", "alert"],
  "citations": [
    {
      "source_id": "doc_123",
      "text": "Revenue increased by 44.8%...",
      "company": "Foodie Media Berhad",
      "filename": "quarterly_results.pdf",
      "page_number": 5
    }
  ],
  "steps": [
    {
      "step": "Planning",
      "thought": "I need to check financial reports..."
    },
    {
      "step": "Execution",
      "tool": "RAG Agent",
      "output": "Retrieved 3 documents..."
    }
  ]
}
```

### 2. Copilot Health Check

Check the health status of all agents and dependencies (Milvus, OpenRouter).

- **URL**: `/copilot/health`
- **Method**: `GET`

#### Response

```json
{
  "status": "healthy",
  "agents": {
    "supervisor": "ready",
    "rag": "ready",
    "financial": "ready",
    "alert": "ready"
  },
  "milvus": "connected",
  "openrouter": "configured",
  "timestamp": "2024-01-14T10:30:00.000Z"
}
```

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 422 | Validation Error (invalid request format) |
| 500 | Internal Server Error (agent processing failure, database error) |
| 503 | Service Unavailable (Milvus/OpenRouter down) |

### Error Response Format

```json
{
  "detail": "Copilot processing failed: Connection to Milvus failed"
}
```

## Frontend Integration Guide

To use this API in a React frontend:

```typescript
// Example fetch call
async function askCopilot(query: string) {
  try {
    const response = await fetch('/api/v1/copilot/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Copilot query failed:', error);
    throw error;
  }
}
```
