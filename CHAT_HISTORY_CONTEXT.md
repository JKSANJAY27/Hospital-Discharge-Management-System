# Chat History & Context System

## Overview
The chatbot now maintains full conversation history in MongoDB and uses this context to provide more intelligent, context-aware responses.

## Enhanced MongoDB Schemas

### MessageMongo
Each message now includes:
- **Basic fields**: role, content, timestamp, session_id, user_id
- **Context metadata**: 
  - `metadata`: Store language, location, user_agent
  - `intent`: Detected intent (discharge_simplification, medication_query, etc.)
  - `token_count`: Track token usage
  - `response_time_ms`: Performance metrics
  - `model_used`: Which AI model generated the response
  - `citations`: Source references
  - `audio_url`: TTS audio link if generated

### SessionMongo
Sessions now track:
- **Conversation metadata**:
  - `message_count`: Total messages in session
  - `primary_language`: Detected conversation language
  - `topics`: Array of discussed topics
  - `last_intent`: Most recent intent
  - `context_summary`: AI-generated summary for long conversations

## Context Retrieval Strategy

### Sliding Window Approach
- Last **10 messages** are used for detailed context
- Older messages (beyond 10) are summarized using AI
- This balances context depth with token efficiency

### Context Structure
```python
conversation_history = [
    {
        "role": "user",
        "content": "What medications should I take?",
        "timestamp": "2026-01-10T10:00:00",
        "intent": "medication_query"
    },
    {
        "role": "assistant",
        "content": "Based on your discharge instructions...",
        "timestamp": "2026-01-10T10:00:05",
        "intent": "medication_query"
    }
]
```

## How Context is Used

### 1. Building Full Context Query
```python
full_context_query = f"""
{profile_context}          # User health profile
{history_context}          # Last 10 messages
{conversation_summary}     # AI summary if >10 messages

=== Current User Query ===
User Query: {request.query}
"""
```

### 2. Passing to Workflow
The workflow receives:
- `conversation_history`: Structured list of previous messages
- `query_for_classification`: Full context with profile + history
- `user_profile`: Health profile data
- `user_location`: GPS coordinates
- `response_language`: Target language

### 3. LLM Context Building
```python
messages = [
    ("system", "You are Swastha, a healthcare assistant..."),
    ("user", "Previous message 1"),
    ("assistant", "Previous response 1"),
    ("user", "Previous message 2"),
    ("assistant", "Previous response 2"),
    ("user", "Current message")
]
```

## New API Endpoints

### GET /sessions/{session_id}/messages
Returns messages with full metadata:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "...",
      "intent": "...",
      "audio_url": "...",
      "metadata": {...},
      "citations": [...],
      "response_time_ms": 1250
    }
  ],
  "session_metadata": {
    "message_count": 15,
    "primary_language": "English",
    "topics": ["medication", "discharge_instructions"],
    "last_intent": "medication_query",
    "context_summary": "Patient asking about post-surgery care..."
  }
}
```

### POST /sessions/{session_id}/summarize
Generates AI summary for long conversations:
```json
{
  "summary": "Patient discussed post-surgery medication schedule...",
  "message_count": 25,
  "generated_at": "2026-01-10T12:00:00"
}
```

## Benefits

### 1. Context-Aware Responses
- Bot remembers previous questions and answers
- Can reference earlier conversation points
- Provides personalized follow-ups

### 2. Multi-Turn Conversations
- "What about the blue pill?" - Bot knows which medication
- "Tell me more" - Bot expands on previous response
- "In Hindi please" - Bot switches language mid-conversation

### 3. Performance Tracking
- Response time monitoring
- Token usage analytics
- Model performance comparison

### 4. Better User Experience
- Coherent multi-turn dialogues
- No need to repeat context
- Natural conversation flow

## Example Use Cases

### Use Case 1: Medication Follow-up
```
User: "What medications should I take?"
Bot: "You should take Metformin 500mg with breakfast and Aspirin 81mg..."

User: "What's the blue pill for?"
Bot: [Using context] "The blue pill is Metformin 500mg. It helps control your blood sugar..."
```

### Use Case 2: Language Switching
```
User: "Tell me about wound care"
Bot: "Here are your wound care instructions: Clean twice daily..."

User: "हिंदी में बताओ"
Bot: [Using context + language detection] "घाव की देखभाल के निर्देश: दिन में दो बार..."
```

### Use Case 3: Complex Medical History
```
[After 15 messages discussing diabetes, heart condition, medications]

User: "Can I exercise?"
Bot: [Using full context + summary] "Given your recent heart surgery and diabetes, here's a safe exercise plan..."
```

## Configuration

### Message Retention
- **Active sessions**: All messages stored
- **Archived sessions**: Messages retained for audit (HIPAA)
- **Context window**: Last 10 messages for active context
- **Summary generation**: Triggered for sessions with 10+ messages

### Token Management
- User messages: ~token count tracked
- Assistant responses: Full token usage logged
- Context pruning: Automatic summary for long conversations

## Database Indexes
Recommended MongoDB indexes for performance:
```javascript
db.messages.createIndex({ "session_id": 1, "timestamp": 1 })
db.messages.createIndex({ "user_id": 1, "timestamp": -1 })
db.sessions.createIndex({ "user_id": 1, "status": 1, "updated_at": -1 })
```

## Future Enhancements
1. **Semantic Search**: Find relevant past conversations
2. **Intent Clustering**: Group similar conversations
3. **Proactive Reminders**: Based on conversation history
4. **Multi-Session Context**: Reference across different sessions
5. **Export Conversations**: Download full chat history
