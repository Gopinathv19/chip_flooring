# chip_flooring
Creating the Environment for the Chip Designing Agents

## Local LM Studio mode

Set `USE_LOCAL=true` in `.env` to route requests to LM Studio instead of Hugging Face.

Example `.env`:

```env
USE_LOCAL=true
LOCAL_API_BASE_URL=http://127.0.0.1:1234/v1
MODEL_NAME=your-local-model-name
```

When `USE_LOCAL` is enabled, the script uses the OpenAI-compatible LM Studio endpoint and keeps the same request/response flow through `chat.completions.create(...)`.
