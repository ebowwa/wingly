
## to connect to the websocket:
### install websocat for local testing
```brew install websocat```

### start the server
```
uv run app.py
```

### connect to the websocket
```
websocat ws://localhost:8080/api/conversation
```