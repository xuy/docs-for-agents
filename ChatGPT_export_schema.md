# ChatGPT Export Schema Documentation

**Version:** 2025
**Purpose:** Comprehensive reference for AI agents to parse, process, and transform ChatGPT conversation exports
**Target Audience:** AI agents, automated parsers, data processors

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Conversation Object Schema](#conversation-object-schema)
4. [Message Mapping Structure](#message-mapping-structure)
5. [Content Types](#content-types)
6. [Author Roles](#author-roles)
7. [Tree Navigation](#tree-navigation)
8. [Image References](#image-references)
9. [Edge Cases and Special Scenarios](#edge-cases-and-special-scenarios)
10. [Parsing Best Practices](#parsing-best-practices)
11. [Examples](#examples)

---

## Overview

ChatGPT data exports contain a file called `conversations.json` which stores all conversation history in JSON format. This file can be extremely large (100MB+) and contains a flat array of conversation objects. Each conversation uses a tree/graph structure to represent message history, allowing for branching conversation paths.

**Key Characteristics:**
- Format: Single-line minified JSON (one very long line)
- Size: Can exceed 200MB for active users
- Structure: Array of conversation objects
- Encoding: UTF-8
- Message Storage: Tree/graph structure via parent-child relationships

---

## File Structure

### Top Level

```json
[
  { conversation_object_1 },
  { conversation_object_2 },
  { conversation_object_3 },
  ...
]
```

The root element is an array containing all conversations. Typical exports contain hundreds to thousands of conversations.

---

## Conversation Object Schema

### Core Fields (Always Present)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier for the conversation | "67a678d3-a274-8191-94ee-7ca817b25b36" |
| `title` | string | User-visible conversation title (may be auto-generated) | "Python Data Processing" |
| `create_time` | number | Unix timestamp (seconds with decimal) when conversation was created | 1760486728.607954 |
| `update_time` | number | Unix timestamp (seconds with decimal) of last update | 1767650773.064263 |
| `mapping` | object | Tree structure containing all messages (see below) | {...} |
| `current_node` | string | ID of the currently active message node | "5afdd785-e333-42ce-8453-1ada4380626e" |
| `conversation_id` | string | Alternative conversation identifier | "67a678d3-a274-8191-94ee-7ca817b25b36" |
| `is_archived` | boolean | Whether conversation is archived | false |
| `memory_scope` | string | Memory scope setting | "user" |
| `sugar_item_visible` | boolean | UI visibility flag | true |
| `is_study_mode` | boolean | Study mode flag | false |

### Optional Fields (May Be Present)

| Field | Type | Description | Presence Rate |
|-------|------|-------------|---------------|
| `default_model_slug` | string | Model used (e.g., "gpt-4", "gpt-5", "o1-preview") | ~98% |
| `conversation_template_id` | string | GPT/project template ID (starts with "g-p-" for projects) | ~25% |
| `gizmo_id` | string | Custom GPT identifier | ~25% |
| `gizmo_type` | string | Type of custom GPT | ~25% |
| `safe_urls` | array | Whitelisted URLs for browsing | ~95% |
| `is_do_not_remember` | boolean | Privacy setting for memory | ~95% |
| `voice` | string | Voice setting if using voice mode | ~4% |
| `async_status` | string | Async processing status | ~2% |
| `moderation_results` | array | Content moderation results | ~0% |
| `plugin_ids` | array | Plugin identifiers (legacy) | ~0% |
| `is_starred` | boolean | Whether conversation is starred | ~0% |
| `blocked_urls` | array | Blocked URLs | ~0% |
| `conversation_origin` | string | Origin of conversation | ~0% |
| `is_read_only` | boolean | Read-only flag | ~0% |
| `disabled_tool_ids` | array | Disabled tool IDs | ~0% |
| `context_scopes` | object | Context scope settings | ~0% |
| `sugar_item_id` | string | Sugar item identifier | ~0% |
| `pinned_time` | number | When conversation was pinned | ~0% |
| `owner` | string | Owner identifier | ~0% |

---

## Message Mapping Structure

The `mapping` field contains the entire conversation tree. Each key is a UUID representing a message node.

### Node Structure

```json
{
  "node-uuid-here": {
    "id": "node-uuid-here",
    "message": { message_object } | null,
    "parent": "parent-node-uuid" | null,
    "children": ["child-uuid-1", "child-uuid-2", ...]
  }
}
```

### Message Object Schema

When `message` is not null, it contains:

```json
{
  "id": "message-uuid",
  "author": {
    "role": "user" | "assistant" | "system" | "tool",
    "name": string | null,
    "metadata": {}
  },
  "create_time": number | null,
  "update_time": number | null,
  "content": {
    "content_type": "text" | "multimodal_text" | "code" | "execution_output" | ...,
    "parts": [...]
  },
  "status": "finished_successfully" | "in_progress" | ...,
  "end_turn": boolean | null,
  "weight": number,
  "metadata": {
    // Varies by message type
    "is_visually_hidden_from_conversation": boolean,
    "attachments": [...],
    "model_slug": string,
    "request_id": string,
    ...
  },
  "recipient": "all" | string,
  "channel": string | null
}
```

### Key Message Fields

| Field | Type | Description |
|-------|------|-------------|
| `author.role` | string | Who sent the message: "user", "assistant", "system", or "tool" |
| `content.content_type` | string | Type of content (see Content Types section) |
| `content.parts` | array | Array of content parts (strings, objects, or mixed) |
| `create_time` | number/null | When message was created (null for some system messages) |
| `status` | string | Message status, usually "finished_successfully" |
| `weight` | number | Message weight (0.0 or 1.0, used for hidden messages) |
| `metadata.is_visually_hidden_from_conversation` | boolean | Whether to hide in UI |

---

## Content Types

The `content.content_type` field indicates how to interpret the `parts` array.

### Discovered Content Types

| Content Type | Description | Parts Format |
|--------------|-------------|--------------|
| `text` | Plain text message | Array with single string |
| `multimodal_text` | Mixed text and media (images) | Array of strings and/or image objects |
| `code` | Code blocks | Array with string(s) containing code |
| `execution_output` | Code execution results | Array with execution output |
| `computer_output` | Computer/terminal output | Array with output text |
| `reasoning_recap` | Summary of reasoning process | Array with summary text |
| `thoughts` | Internal AI reasoning (o1 models) | Array with thought text |
| `user_editable_context` | User-editable context/instructions | Array with context text |
| `tether_browsing_display` | Browser tool display output | Object/array with browsing data |
| `super_widget` | Special widget/interactive element | Complex object structure |

### Parts Array Examples

**Simple Text:**
```json
{
  "content_type": "text",
  "parts": ["Hello, how can I help you today?"]
}
```

**Multimodal (Text + Images):**
```json
{
  "content_type": "multimodal_text",
  "parts": [
    {
      "content_type": "image_asset_pointer",
      "asset_pointer": "sediment://file_00000000329c620cae9335c4e8fffff8",
      "size_bytes": 221373,
      "width": 708,
      "height": 1536,
      "metadata": {
        "sanitized": true
      }
    },
    "What do you think of this image?"
  ]
}
```

**Code:**
```json
{
  "content_type": "code",
  "parts": ["def hello():\n    print('Hello, world!')"]
}
```

---

## Author Roles

Messages can come from different authors:

| Role | Description | Visibility | Notes |
|------|-------------|------------|-------|
| `user` | Human user messages | Always visible | User input |
| `assistant` | AI assistant responses | Always visible | ChatGPT responses |
| `system` | System messages (prompts, instructions) | Usually hidden | Filter these |
| `tool` | Tool execution results | Collapsible | Auto-inserted by ChatGPT |

**Note:** System messages often have `metadata.is_visually_hidden_from_conversation: true` and should be filtered when rendering user-facing conversation views.

### Tool Messages

Tool messages have special characteristics:

**Structure:**
```json
{
  "author": {
    "role": "tool",
    "name": "file_search",  // Tool name
    "metadata": {}
  },
  "content": {
    "content_type": "text" | "multimodal_text" | "tether_browsing_display",
    "parts": [...]
  }
}
```

**Common Tool Names:**
- `file_search` - File/document search tool
- `browser` - Web browsing tool
- `python` - Code execution tool
- `dalle` - Image generation tool

**UI Rendering Recommendation:**
Tool messages should be **collapsed by default** and **expandable on click** since they are auto-inserted by ChatGPT and not typed by the user. This keeps conversations clean while preserving full context.

---

## Tree Navigation

The mapping structure creates a tree/graph where:
- **Root Node:** Has `parent: null`, represents conversation start
- **Linear Path:** Most conversations follow a single parent→child chain
- **Branching:** Multiple children indicate conversation branching (user edited a message or tried different responses)

### Finding the Conversation Thread

**Method 1: Follow current_node backwards**
```python
def get_conversation_thread(mapping, current_node_id):
    thread = []
    node_id = current_node_id

    while node_id:
        node = mapping[node_id]
        if node['message']:
            thread.append(node)
        node_id = node['parent']

    return list(reversed(thread))
```

**Method 2: Traverse from root following children**
- Start at root (node with `parent: null`)
- Follow the first child (or use heuristics to pick the "main" branch)
- Continue until reaching a leaf node

### Handling Branches

When a node has multiple children, it indicates:
1. User edited their message and got a new response
2. User regenerated the assistant's response
3. Conversation split into multiple paths

For rendering, typically follow the path indicated by `current_node` or choose the first/last child.

---

## Image References

Images use asset pointers in the format:
```
sediment://file_XXXXXXXXXXXXXXXXXXXXXXXX
```

### Image Object Structure

```json
{
  "content_type": "image_asset_pointer",
  "asset_pointer": "sediment://file_00000000329c620cae9335c4e8fffff8",
  "size_bytes": 221373,
  "width": 708,
  "height": 1536,
  "fovea": null,
  "metadata": {
    "sanitized": true,
    "dalle": null,
    ...
  }
}
```

### Resolving Image Files

The export includes sanitized image files in the same directory:
- Format: `file_XXXXXXXXXXXXXXXXXXXXXXXX-sanitized.jpg` or `.jpeg` or `.png`
- The file ID from the asset_pointer maps directly to the filename
- Example: `sediment://file_00000000329c620cae9335c4e8fffff8` → `file_00000000329c620cae9335c4e8fffff8-sanitized.jpg`

**Note:** Not all images may be present. Check file existence before referencing.

---

## Edge Cases and Special Scenarios

### Empty Messages
Some messages (especially system messages) have empty content:
```json
{
  "content": {
    "content_type": "text",
    "parts": [""]
  }
}
```
**Handling:** Skip these when rendering visible conversations.

### Missing create_time
Some system messages have `create_time: null`:
```json
{
  "create_time": null,
  "author": {
    "role": "system"
  }
}
```
**Handling:** Use parent message's time or conversation's create_time.

### Hidden Messages
Messages with weight 0.0 or `is_visually_hidden_from_conversation: true` should typically be filtered:
```json
{
  "weight": 0.0,
  "metadata": {
    "is_visually_hidden_from_conversation": true
  }
}
```

### Tool Calls and Outputs
Tool messages represent function calls and their results:
- Role: `tool`
- Content may include structured data about tool execution
- Typically rendered as execution blocks in conversation view

### Project/GPT Conversations
Conversations using custom GPTs or projects have:
```json
{
  "conversation_template_id": "g-p-XXXXXXXXXXXXXXXXXXXXXXXX",
  "gizmo_id": "g-XXXXXXXXXXXXXXXXXXXXXXXX",
  "gizmo_type": "gizmo"
}
```

### Reasoning Models (o1, o3)
O1/O3 model conversations may include:
- `content_type: "thoughts"` - Internal reasoning
- `content_type: "reasoning_recap"` - Summary of reasoning

### Citations

ChatGPT includes citations in responses when referencing uploaded files or browsed content.

**Citation Formats:**

1. **Chinese Brackets Format:**
   ```
   【cite】【turn1view3】【turn1view2】
   ```

2. **Unicode Marker Format:**
   ```
   \ue200cite\ue202turn1view3\ue201
   \ue200filecite\ue202turn0file0\ue201
   ```

**Rendering:**
- Convert citations to numbered references: `[1]` `[2]` `[3]`
- Citations typically appear inline after referenced text
- Source content may not be available in export
- Display as superscript for clean appearance

**Example:**
```
Input text: "According to the document【cite】【turn0file0】, the data shows..."
Rendered:   "According to the document[1], the data shows..."
```

**Regex Patterns:**
- Chinese brackets: `【cite】【[^】]+】`
- Unicode markers: `\ue200(?:file)?cite\ue202[^\ue201]+\ue201`

---

## Parsing Best Practices

### For AI Agents

1. **Always check field existence** before accessing
   - Many fields are optional
   - Use `.get()` with defaults

2. **Handle large files efficiently**
   - conversations.json can be 200MB+
   - Use streaming parsers if possible
   - Consider processing in chunks

3. **Filter appropriately for use case**
   - User-facing: Hide system messages, filter by weight
   - Analysis: Keep all messages
   - Search/indexing: Extract text from all visible messages

4. **Preserve structure when transforming**
   - Tree structure contains important context
   - Timestamp order may differ from tree order

5. **Handle encoding properly**
   - Content may contain Unicode, emojis, code blocks
   - Ensure UTF-8 handling throughout pipeline

6. **Image resolution**
   - Check for image files in export directory
   - Handle missing images gracefully
   - Extract file ID from asset_pointer correctly

### Common Parsing Patterns

**Extract all visible messages in order:**
```python
def extract_visible_messages(conversation):
    messages = []
    for node in conversation['mapping'].values():
        msg = node.get('message')
        if not msg:
            continue

        # Filter system/hidden messages
        if msg['author']['role'] == 'system':
            continue
        if msg.get('weight', 1.0) == 0.0:
            continue
        if msg.get('metadata', {}).get('is_visually_hidden_from_conversation'):
            continue

        messages.append(msg)

    # Sort by create_time
    messages.sort(key=lambda m: m.get('create_time') or 0)
    return messages
```

**Extract text content:**
```python
def extract_text_content(message):
    parts = message['content'].get('parts', [])
    text_parts = []

    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict) and part.get('content_type') == 'image_asset_pointer':
            # Handle image reference
            text_parts.append(f"[Image: {part['asset_pointer']}]")

    return '\n'.join(text_parts)
```

---

## Examples

### Example 1: Simple Text Conversation

```json
{
  "title": "Hello World",
  "create_time": 1700000000.0,
  "update_time": 1700000100.0,
  "current_node": "msg-2",
  "mapping": {
    "root": {
      "id": "root",
      "message": null,
      "parent": null,
      "children": ["msg-1"]
    },
    "msg-1": {
      "id": "msg-1",
      "message": {
        "id": "msg-1",
        "author": {"role": "user"},
        "create_time": 1700000001.0,
        "content": {
          "content_type": "text",
          "parts": ["Hello!"]
        }
      },
      "parent": "root",
      "children": ["msg-2"]
    },
    "msg-2": {
      "id": "msg-2",
      "message": {
        "id": "msg-2",
        "author": {"role": "assistant"},
        "create_time": 1700000002.0,
        "content": {
          "content_type": "text",
          "parts": ["Hello! How can I help you today?"]
        }
      },
      "parent": "msg-1",
      "children": []
    }
  }
}
```

### Example 2: Branching Conversation

```
root
 └─ msg-1 (user)
     ├─ msg-2a (assistant, first attempt)
     └─ msg-2b (assistant, regenerated)
         └─ msg-3 (user, continuing from 2b)
```

Use `current_node` to determine which branch is active.

---

## Sources and References

This documentation is based on:
- Analysis of real ChatGPT export data (4200+ conversations)
- OpenAI Developer Community discussions
- Export format reverse engineering

### Related Resources

- [OpenAI Help: Export Data](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data)
- [Community Discussion: Parsing conversations.json](https://community.openai.com/t/decoding-exported-data-by-parsing-conversations-json-and-or-chat-html/403144)
- [Community: JSON Structure Questions](https://community.openai.com/t/questions-about-the-json-structures-in-the-exported-conversations-json/954762)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-06
**Maintained For:** AI agents and automated parsers
