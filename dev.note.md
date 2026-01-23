pkill -f 'uvx' -9  || rm -rf /home/s/.cache/uv/*      
 
   "command": "uvx",
      "args": [
        "--index-url",
        "https://mirrors.sustech.edu.cn/pypi/web/simple",
        "--from",
        "/home/s/...../mcp-ssh-session",
        "mcp-ssh-session"
      ],
      
      
      /home/s/ss_proj/saifuls_copy_dashboard/.locals/mcp-ssh-session

      SSH_ENV_FILE=/home/s/ss_proj/saifuls_copy_dashboard/ssssssssss.env  uvx --index-url https://mirrors.sustech.edu.cn/pypi/web/simple --from git+https://github.com/Saifullah336/mcp-ssh-session mcp-ssh-session

      script -q -a -f y_dev.log -c "SSH_ENV_FILE=/home/s/ss_proj/ssssssssss.env uvx --index-url https://mirrors.aliyun.com/pypi/simple --from /home/s/ss_proj/saifuls_copy_dashboard/.locals/mcp-ssh-session mcp-ssh-session" 

https://charly-lersteau.com/blog/2019-11-24-faster-python-pip-install-mirrors/
## Logging Quirks

**Important**: Only `logger.error()` logs appear in y_dev.log. `logger.info()` and `logger.debug()` are filtered out.

**Why**: The logging configuration or log level filtering only allows ERROR level logs to be captured.

**Solution**: Always use `logger.error()` for debugging logs that need to be visible in dev logs. The `[DEBUG:STREAMING]` prefix makes it easy to identify and clean up later.

**Example**:
```python
# This won't appear in logs
logger.info(f"Processing file {file}")

# This WILL appear in logs
logger.error(f"[DEBUG:STREAMING] Processing file {file}")
``` 