
## to connect to the websocket:
### install websocat for local testing
```brew install websocat```

### start the server
```
uv run app.py
```

### start the python handler
```
cd telegram-ws
python telegram_handler.py
```

```
curl -X POST "http://localhost:8080/api/process-audio?prompt_type=default_transcription" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/Users/ebowwa/wingly/audio-samples/Elijah_October_27_2024_9__59PM.ogg;type=audio/ogg" \
  -F "batch=false" \
  -F "model_name=gemini-1.5-flash" \
  -F "temperature=1.0" \
  -F "top_p=0.95" \
  -F "top_k=40" \
  -F "max_output_tokens=8192"
```