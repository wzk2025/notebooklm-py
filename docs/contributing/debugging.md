# Debugging Guide

How to debug issues and reverse engineer new NotebookLM features.

## Capturing Network Traffic

### Chrome DevTools Setup

1. Open Chrome DevTools (F12)
2. Go to **Network** tab
3. Check "Preserve log" to keep requests across navigations
4. Filter by: `batchexecute` (for RPC calls)

### Capturing an RPC Call

1. Clear network log
2. Perform action in NotebookLM UI
3. Find the `batchexecute` request
4. Examine:
   - **URL params**: `rpcids=METHOD_ID`
   - **Request body**: `f.req=...` (URL-encoded)
   - **Response**: Starts with `)]}'\n`

### Decoding the Request

The `f.req` parameter contains URL-encoded JSON:

```python
import urllib.parse
import json

# Copy the f.req value from DevTools
encoded = "..."

# Decode
decoded = urllib.parse.unquote(encoded)
print(decoded)

# Parse JSON
data = json.loads(decoded)
# Structure: [[[rpc_id, params_json, null, "generic"]]]

# The params are themselves JSON-encoded
inner_params = json.loads(data[0][0][1])
print(json.dumps(inner_params, indent=2))
```

### Decoding the Response

Responses have an anti-XSSI prefix and chunked format:

```python
response_text = """)]}'

123
["wrb.fr","wXbhsf","[[\\"abc123\\",\\"My Notebook\\"]]"]

45
["di",42]
"""

# Step 1: Remove prefix
lines = response_text.split('\n')
lines = [l for l in lines if not l.startswith(')]}\'')]

# Step 2: Find wrb.fr chunk
for i, line in enumerate(lines):
    if '"wrb.fr"' in line:
        chunk = json.loads(line)
        method_id = chunk[1]
        result_json = chunk[2]
        result = json.loads(result_json)
        print(f"Method: {method_id}")
        print(f"Result: {result}")
```

## Common Debugging Scenarios

### "Session Expired" Errors

**Symptoms:**
- `RPCError` mentioning unauthorized
- Redirects to login page

**Debug:**
```python
# Check if CSRF token is present
print(client.auth.csrf_token)

# Try refreshing
await client.refresh_auth()
print(client.auth.csrf_token)  # Should be new value
```

**Solution:** Re-run `notebooklm login`

### RPC Method Returns None

**Symptoms:**
- Method completes but returns `None`
- No error raised

**Debug:**
```python
# Add logging to see raw response
from notebooklm.rpc import decode_response

# In your test code:
raw_response = await http_client.post(...)
print("Raw:", raw_response.text[:500])

result = decode_response(raw_response.text, "METHOD_ID")
print("Parsed:", result)
```

**Common causes:**
- Rate limiting (Google returns empty result)
- Wrong RPC method ID
- Incorrect parameter structure

### Parameter Order Issues

RPC parameters are position-sensitive:

```python
# Wrong - audio will fail
params = [
    [2], notebook_id, [
        None, None, 1,
        source_ids,
        # ... missing positional elements
    ]
]

# Correct - all positions filled
params = [
    [2], notebook_id, [
        None, None, 1,
        source_ids,
        None, None,  # Required placeholders
        [None, [instructions, length, None, sources, lang, None, format]]
    ]
]
```

**Debug:** Compare your params with captured traffic byte-by-byte.

### Nested List Depth

Source IDs have different nesting requirements:

```python
# Single nesting (some methods)
["source_id"]

# Double nesting
[["source_id"]]

# Triple nesting (artifact generation)
[[["source_id"]]]

# Quad nesting (get_source_guide)
[[[["source_id"]]]]
```

**Debug:** Capture working traffic and count brackets.

## RPC Tracing

### Adding Debug Logging

Temporarily add logging to `_core.py`:

```python
async def rpc_call(self, method, params, ...):
    import json
    print(f"=== RPC Call: {method} ===")
    print(f"Params: {json.dumps(params, indent=2)}")

    # ... existing code ...

    print(f"Response status: {response.status_code}")
    print(f"Response preview: {response.text[:500]}")

    result = decode_response(response.text, method)
    print(f"Decoded result: {result}")

    return result
```

### Comparing with Browser

To verify your implementation matches the browser:

1. Capture browser request with DevTools
2. Save the decoded params
3. Run your code with logging
4. Compare params structure
5. Check for differences in:
   - Nesting depth
   - Null placeholder positions
   - String vs integer types

## Testing RPC Changes

### Quick Test Script

```python
import asyncio
from notebooklm import NotebookLMClient

async def test_method():
    async with await NotebookLMClient.from_storage() as client:
        # Test the method
        try:
            result = await client.notebooks.list()
            print(f"Success: {result}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test_method())
```

### Mocking for Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_list_notebooks():
    mock_response = [[["nb123", "Test Notebook", None, [[1234567890]], 3]]]

    with patch.object(ClientCore, 'rpc_call', new_callable=AsyncMock) as mock:
        mock.return_value = mock_response

        client = NotebookLMClient(mock_auth)
        await client.__aenter__()

        notebooks = await client.notebooks.list()

        assert len(notebooks) == 1
        assert notebooks[0].title == "Test Notebook"
```

## Reverse Engineering New Features

### Process

1. **Identify the feature** in NotebookLM UI
2. **Capture traffic** while using it
3. **Document the RPC ID** from URL params
4. **Decode request payload**
5. **Decode response structure**
6. **Implement and test**

### Documentation Template

When discovering a new method, document:

```markdown
## NEW_METHOD (RPC ID: XyZ123)

**Purpose:** What it does

**Request:**
```python
params = [
    # Document each position
    position_0,  # What this is
    position_1,  # What this is
    ...
]
```

**Response:**
```python
[
    result_data,  # Structure description
    ...
]
```

**Notes:**
- Any quirks or gotchas
- Related methods
```

## Getting Help

If you're stuck:

1. Check existing implementations in `_*.py` files
2. Look at test files for expected structures
3. Compare with discovery docs in `docs/reference/internals/`
4. Open an issue with:
   - What you're trying to do
   - Captured request/response (sanitized)
   - Error messages
