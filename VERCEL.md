# Run this project on Vercel

Vercel does not run a server that stays on. The demo page is served
as static files, and the API runs as a serverless function in
`api/index.py` (the same token-bucket code, wrapped in Vercel's
`BaseHTTPRequestHandler` handler).

## Honest limit

The bucket lives in the function's memory. Vercel can start a fresh
function at any time, which resets the buckets. A single Burst x15
call always works (10 allowed / 5 denied), because all 15 requests
happen inside one function call. One-by-one Send clicks may see a
fresh bucket if Vercel starts a new function between clicks. For a
demo where the bucket must stay alive between clicks, use Render
or any server that stays running instead.
