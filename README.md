# Distributed Rate Limiter & Traffic Governor

This is my OJT project. I made it because I kept wondering how big apps
stop one user (or one bot) from hammering an API and taking it down for
everyone else.

The short answer I ended up building around: count requests in one shared
place, not on each server separately. If every server counts on its own,
a user behind a load balancer just gets the limit multiplied by the
number of servers. So this project uses Redis as that shared counter.

## What it does

- Limits requests per API key and per IP, so free users and paid users
  don't get the same treatment.
- Uses a token bucket. You get a burst of tokens, they refill over time,
  and when you're out, you get a 429 until they refill.
- Has a traffic governor on top of the limiter. When things start slowing
  down, it drops background jobs first and tries to keep the important
  requests working. That's the part I found most interesting, because
  just blocking everyone equally felt wrong.
- Lets an admin change limits without restarting the app.
- Sends back normal rate limit headers, so a client can see how many
  requests it has left and when to retry.

Tiers I used for testing:

- Free: 60 burst, refills 1 per second
- Pro: 600 burst, refills 10 per second
- Enterprise: 6000 burst, refills 100 per second

Those numbers are just for the demo. In a real setup they'd come from
whatever plan a customer is actually on.

## How it works, in plain words

A request comes in, the middleware checks the governor first, then the
IP limit, then the API key limit. The actual counting happens in Redis
with a Lua script. I did it that way because a normal read, check, then
decrement can race when two servers hit at the same time. The Lua script
runs as one step on Redis, so two servers can't both spend the last token.

If Redis goes down, this version fails open by default. That means it
lets traffic through and logs it, instead of blocking everyone. I know
that's a trade-off. For a payment API I'd probably fail closed instead.
I left it as a setting so you can change your mind without rewriting
anything.

## How to run it

You need Python and Redis running locally.

```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or with Docker for Redis:

```
docker compose up redis
```

Then open http://localhost:8000/docs to try it in the browser.

Demo keys I used:

- `demo-free-key`
- `demo-pro-key`
- `demo-ent-key`

No key just counts as free.

Try it:

```
curl http://localhost:8000/api/data -H "X-API-Key: demo-free-key"
```

And to hammer it a bit:

```
python load_test.py free 100
python load_test.py pro 100
```

## What I actually tested

I ran this on my machine, without Redis at first and then with the
fallback, just to see if the numbers made sense.

- Free key, 100 requests: 60 went through, 40 got 429. That matched
  the 60 token burst, so I was fairly happy with that.
- Pro key, 100 requests: all 100 went through.
- Unit tests: 2 passed. Not a lot, I know. They cover the bucket
  filling up and different users not sharing each other's limits.

I still need to test it properly with two API servers against one
Redis. That's the real distributed test, and I haven't done that bit
yet in a clean way.

## What's not done yet

Honest list, so I don't pretend this is finished:

- No real login or user database, just demo keys.
- No dashboard UI yet, just an admin API and a metrics endpoint.
- Redis is still a single point of failure here. A cluster would be
  the next step.
- The governor's load calculation is simple, based on recent latency
  and errors. It works for a demo, but I wouldn't trust it blindly
  in production.

## Project layout

```
app/config.py      - tiers and limits
app/limiter.py     - token bucket in Redis, plus a sliding window version
app/governor.py    - priority shedding when things get busy
app/middleware.py  - checks requests before they reach the API
app/main.py        - demo APIs and admin endpoints
tests/             - basic tests for the bucket
load_test.py       - simple script to hammer the API
```

## What I learned from this

Mostly that rate limiting sounds simple until you try to do it across
more than one server. The algorithm is the easy part. The hard parts
are making the count atomic, deciding what to do when your counter
goes down, and not punishing good users when bad traffic shows up.

Still learning, and open to suggestions if you spot something wrong.
