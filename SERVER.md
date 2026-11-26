# Run this project on any server

This project is a single-process, in-memory demo. It runs on any
machine that has Python 3.11 or newer. No database, no Redis, no
framework, no Docker is needed.

## What changed to make it server-ready

In `server.py`:

```python
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
```

- On your own laptop, with nothing set, it still runs exactly as
  before: `python server.py`, then open http://localhost:8000
- On a server, set `HOST=0.0.0.0` before starting it. That means
  "let other computers on the network connect", not just this one.

## Steps on any server

1. Put the code on the server — `git clone` this repo, or copy the
   ZIP and extract it.
2. Check Python: `python --version` (or `python3 --version` on Linux).
   It needs Python 3.11 or newer.
3. Start it:

   Windows (Command Prompt / PowerShell):
   ```
   set HOST=0.0.0.0
   python server.py
   ```
   Or just double-click `start-server.bat`.

   Linux / Mac:
   ```
   HOST=0.0.0.0 python server.py
   ```
   Or run `./start-server.sh`.

4. Find the server's IP address:
   - Windows: `ipconfig` — look for IPv4 Address, e.g. 192.168.1.20
   - Linux: `hostname -I` or `ip addr`
5. Open it from any other computer on the same network:
   ```
   http://<server-ip>:8000
   ```
   Example: `http://192.168.1.20:8000`
6. Test it: click Reset, then Burst x15. With the defaults
   (capacity 10, refill 2/second) it should be 10 allowed, 5 denied.

## If the page does not open from another computer

- The server's firewall must allow port 8000. On Windows, allow
  Python through the firewall when it asks. On Linux, open the port
  in the firewall (for example `sudo ufw allow 8000/tcp` on Ubuntu).
- The other computer must be on the same network as the server,
  unless the server has a public IP.

## Keeping it running

If you close the terminal, the server stops.

- Linux, in the background: `nohup HOST=0.0.0.0 python server.py &`
- Windows: leave the terminal open, or run it as a scheduled task.
- For a public link, use a hosting service (Render, Railway, etc.)
  instead — that needs your mentor's written approval under the PRD,
  because the PRD forbids Docker / cloud unless approved in writing.

## Limits, honestly

- Single process, in-memory only. Restart the server and the
  buckets are gone.
- No login, no authentication. Anyone who can reach the server's
  IP and port 8000 can click Reset or change the capacity.
- Use it on a trusted / college network, not straight on the
  public internet.
