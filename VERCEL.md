# Run this project on Vercel

Vercel treats the repo's root `server.py` as the Python app, so the
whole app runs as one function — the same `server.py` that runs
locally with `python server.py`. No rewrites are needed: `/` serves
the demo page from `static/`, and `/api/*` is the same API.

`vercel.json` only does two things:
- `installCommand` skips pip install (the app is Python standard
  library only; `requirements.txt` is only for Tier 3 on a laptop).
- `includeFiles` bundles `static/` and `limiter/` into the function,
  so the page files are actually there to serve.

## Honest limit

The bucket lives in the function's memory. Vercel can start a fresh
function at any time, which resets the buckets. A single Burst x15
call always works (10 allowed / 5 denied), because all 15 requests
happen inside one function call. One-by-one Send clicks may see a
fresh bucket if Vercel starts a new function between clicks. For a
demo where the bucket must stay alive between clicks, use Render
or any server that stays running instead.
