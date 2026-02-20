# Airia API Reference (for StockPulse)

Use this when coding the AI agent integration. Official URLs:

- **REST API docs:** https://api.airia.ai/docs (body/params per endpoint; get GUID + examples from Studio → Settings → Interfaces → View API Info)
- **Python SDK docs:** https://airiallc.github.io/airia-python/
- **Explore (product docs):** https://explore.airia.com/llms.txt (index), https://explore.airia.com/building-and-deploying-agents/interface-options/api-deployment

---

## Authentication

- **Headers:** `Content-Type: application/json`, `X-API-Key: YOUR_API_KEY`
- **API key:** Create in Airia Studio → Settings → Interfaces → View API Keys, or Settings → API Keys. Scope to the correct project.
- **Pipeline ID (GUID):** From Studio → Settings → Interfaces → View API Info next to the API interface. All interfaces run against the **Active** version of the agent.

---

## Python SDK (airia package)

```bash
pip install airia
# or
uv add airia
```

### Client

- **Sync:** `AiriaClient(api_key="...", base_url=..., timeout=...)`
- **Async:** `AiriaAsyncClient(api_key="...", ...)`
- API key can come from env: `AIRIA_API_KEY`
- Optional: `with_bearer_token()`, `with_openai_gateway()`, `with_anthropic_gateway()`

### Running a pipeline (agent)

Use **pipeline_execution** on the client:

```python
from airia import AiriaClient

client = AiriaClient(api_key="your_api_key")  # or leave None to use AIRIA_API_KEY env

response = client.pipeline_execution.execute_pipeline(
    pipeline_id="<YOUR_PIPELINE_GUID>",   # From View API Info in Studio
    user_input="Run one inventory cycle. Current context: ...",
    debug=False,
    # Optional:
    # user_id=..., conversation_id=..., async_output=False,
    # prompt_variables={"key": "value"},
    # save_history=True,
)

# Response: PipelineExecutionResponse
# - response.result  (Optional[str]) – main output text
# - response.report   (Optional[Dict]) – step results/debug
# - response.is_backup_pipeline (bool)
print(response.result)
```

### Other methods

- **Streaming:** `execute_pipeline(..., async_output=True)` → returns a streamed response.
- **Get execution by ID:** `client.pipeline_execution.get_pipeline_execution(execution_id="...")`
- **Temporary assistant (no pipeline):** `client.pipeline_execution.execute_temporary_assistant(model_parameters=..., user_input=..., prompt_parameters=...)`

### Structured output (optional)

Pass a Pydantic model so the agent’s reply is parsed into it:

```python
from pydantic import BaseModel

class OrderDecision(BaseModel):
    sku: str
    quantity: int
    supplier_id: str
    reason: str

response = client.pipeline_execution.execute_pipeline(
    pipeline_id="...",
    user_input="...",
    output_schema=OrderDecision,
)
# response.result is an OrderDecision instance
```

---

## For StockPulse backend

1. **Environment:** Set `AIRIA_API_KEY` and `AIRIA_PIPELINE_ID` (the agent’s GUID from View API Info).
2. **agent_caller.py:** Use `AiriaClient().pipeline_execution.execute_pipeline(pipeline_id=os.environ["AIRIA_PIPELINE_ID"], user_input=...)`. Build `user_input` from current inventory, sales velocity, and supplier lead times (e.g. JSON or natural language).
3. **Parse result:** Either free-form text or use `output_schema` with a Pydantic model for purchase orders (e.g. list of { sku, quantity, supplier_id, reason }) and map to DB rows.
4. **Errors:** SDK raises `AiriaAPIError` on API failures; handle and optionally push a step message over WebSocket for the UI.
