# AI Service Configuration

TermCraft AI supports both local and cloud-based AI services with automatic fallback.

## Available Services

### 1. Ollama (Local) - Default
- **Model**: `phi3:medium` (14B parameters)
- **Benefits**: Private, fast, no API costs, works offline
- **Requirements**: Ollama running on `localhost:11434`

### 2. OpenRouter (Cloud)
- **Model**: `meta-llama/llama-3.3-8b-instruct:free` (default)
- **Benefits**: No local setup, access to latest models
- **Requirements**: OpenRouter API key

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# AI Service Configuration
PRIMARY_AI_SERVICE=ollama  # or "openrouter"

# OpenRouter Configuration (if using OpenRouter)
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-8b-instruct:free
```

### Service Priority

The system uses a **primary + fallback** approach:

1. **Primary Service**: Set by `PRIMARY_AI_SERVICE`
2. **Fallback Service**: Automatically switches if primary fails
3. **Error Handling**: Graceful degradation with helpful error messages

## Usage Examples

### Use Ollama as Primary (Default)
```bash
PRIMARY_AI_SERVICE=ollama
```
- Tries Ollama first
- Falls back to OpenRouter if Ollama fails
- Best for: Privacy, offline use, no API costs

### Use OpenRouter as Primary
```bash
PRIMARY_AI_SERVICE=openrouter
```
- Tries OpenRouter first  
- Falls back to Ollama if OpenRouter fails
- Best for: Latest models, no local setup

## Setup Instructions

### Ollama Setup
1. Install Ollama: https://ollama.ai/
2. Pull Phi3 model: `ollama pull phi3:medium`
3. Start Ollama: `ollama serve`
4. Verify: `curl http://localhost:11434/api/tags`

### OpenRouter Setup
1. Get API key: https://openrouter.ai/
2. Add to `.env`: `OPENROUTER_API_KEY=your_key`
3. Choose model: `OPENROUTER_MODEL=your_preferred_model`

## Troubleshooting

### Ollama Issues
- Check if Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model: `ollama list`
- Pull missing model: `ollama pull phi3:medium`

### OpenRouter Issues
- Verify API key in `.env`
- Check model availability: https://openrouter.ai/models
- Test connection: `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models`

### Fallback Behavior
- System automatically tries both services
- Logs show which service is being used
- Graceful error messages if both fail
- No data loss or service interruption

## Performance Comparison

| Service | Speed | Privacy | Cost | Offline | Model Quality |
|---------|-------|---------|------|---------|---------------|
| Ollama | Fast | High | Free | Yes | Good |
| OpenRouter | Medium | Medium | Pay-per-use | No | Excellent |

## Best Practices

1. **Development**: Use Ollama for fast, private development
2. **Production**: Consider OpenRouter for better model quality
3. **Hybrid**: Keep both configured for maximum reliability
4. **Monitoring**: Check logs to see which service is being used
