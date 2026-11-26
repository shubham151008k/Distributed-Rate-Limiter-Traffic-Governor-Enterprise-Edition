# Run this project on Vercel

One function runs the whole demo: `api/index.py` serves the demo
page from `static/`, the JS/CSS, and the `/api/*` endpoints, using
the same token-bucket code as `server.py`. A catch-all rewrite sends
every path to that function, and the handler reads Vercel's `?path=`
query value to get the original path back.

`vercel.json` only does two things:
- `installCommand` skips pip install (the app is Python standard
  library only; `requirements.txt` is only for Tier 3 on a laptop).
- `includeFiles` bundles `static/` and `limiter/` into the function,
  so the page files are actually there to serve.

Note: the first Vercel deployment (26 Nov 2026, commit 3a3eed9
"Initial commit") was the only deployment in the Vercel dashboard
and did not match any GitHub commit — pushes to GitHub main did not
auto-deploy, so a redeploy has to be triggered from the Vercel
dashboard after checking the Git connection.

## Honest limit

The bucket lives in the function's memory. Vercel can start a fresh
function at any time, which resets the buckets. A single Burst x15
call always works (10 allowed / 5 denied), because all 15 requests
happen inside one function call. One-by-one Send clicks may see a
fresh bucket if Vercel starts a new function between clicks. For a
demo where the bucket must stay alive between clicks, use Render
or any server that stays running instead.
