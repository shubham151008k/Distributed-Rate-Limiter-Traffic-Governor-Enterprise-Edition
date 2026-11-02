# Distributed Rate Limiter & Traffic Governor

This is our OJT project, Team G478 - Shubham Kumar and Aaniya Barua.

It is an in-memory token bucket rate limiter, made in Python, with a
simple demo page that shows each request being allowed or denied. It
is an educational simulation of a traffic governor, not a production
gateway.

The words Distributed and Enterprise are in the project title, but
what we are actually building is a single-process, in-memory demo
that runs on localhost. I want to be clear about that from the start,
because that is what our PRD says.

## What it does

- Limits requests per client, so one heavy client cannot starve the
  others. Each client gets its own bucket.
- Uses a token bucket. A bucket starts full, tokens refill slowly
  over time, and when you are out, requests are denied until tokens
  refill again.
- Shows it all on a one-page demo UI: a config form, a client
  selector, Send request and Burst buttons, a token gauge, an
  allowed or denied badge, counters, and a recent-decisions list.
- Lets you change the capacity and refill rate, with validation,
  and reset the buckets and counters.
- For full completion, it also includes a traffic-log analysis:
  find the top 5 IPs by request volume, and plot allowed versus
  rejected requests per minute.

Tier 1 is the core demo, and that is the minimum pass. Tier 3, the
log analysis, is required for full completion. Tier 2 items, like
HTTP 429 with retry guidance, a fail-open toggle, and a CSV decision
log, are optional extras, only if Tier 1 is stable and Tier 3 is on
track.

## How it works, in plain words

A request comes in, we look up that client's bucket in a dictionary,
protected by a lock so two threads cannot spend the same token.

We refill lazily, using a monotonic clock. That just means we work
out how much time has passed since the last check, add that many
tokens, and cap it at the capacity, so a clock going backwards
cannot remove tokens.

If there are enough tokens, we allow the request and subtract the
cost. If not, we deny it, and in the optional Tier 2 version we
also tell the client how long to wait before retrying.

There is no shared store here. The limiter state lives in process
memory only, and it is lost on restart. That is a limitation, and
it is on purpose for this project.

## What we use, and what we do not use

We use Python 3 standard library only for the core: http.server,
threading, time, and unittest. The demo page uses HTML, CSS,
JavaScript, and Bootstrap 5. For the Tier 3 analysis only, we use
pandas and matplotlib.

We do not use Redis, a database, or a message queue. We do not use
FastAPI, Flask, or Django, and we do not use Docker or cloud
deployment, unless our mentor approves it in writing. That is in
our PRD, and it is why this README does not mention Redis at all.

## How to run it

```
python server.py
```

Then open the demo page on localhost in your browser. The page
shows the default config, and you can start sending requests from
there.

Default config in the PRD is capacity 10, refill 2 tokens per
second.

Try this, as in the scripted demo:

1. Send one request, and watch the gauge drop by one.
2. Click Burst x15 quickly. With a fresh client, you should see
   exactly 10 allowed and 5 denied.
3. Wait a few seconds, send again, and watch the refilled tokens
   allow a request.
4. Switch to a second client, and check that the first client's
   exhausted bucket does not affect the second one.
5. Try an invalid capacity, like 0 or text, and check you get an
   inline error and nothing changes.

Run the tests with:

```
python -m unittest
```

## Traffic analysis (Tier 3)

The analysis script reads a traffic log of at least 10,000 lines,
skips and counts malformed lines, prints the top 5 IPs by request
volume, with ties broken by IP ascending, and saves a chart of
allowed versus rejected requests per 1-minute window, with empty
minutes shown as zero.

The findings from the actual output go in a short paragraph here
once the analysis has been run, not before. No result should be
copied from the PRD as if it was measured.

## Project layout, as in the PRD

```
limiter/token_bucket.py  - TokenBucket: refill, consume, remaining, retry-after
limiter/store.py         - Dictionary of buckets, lock, creation on first use
limiter/config.py        - Defaults and validation
server.py                - ThreadingHTTPServer, JSON endpoints, static files
static/index.html, app.js, styles.css - Bootstrap demo page
tests/                   - unittest, including fake-clock tests
analysis/analyze_traffic.py - pandas top-5, 1-minute chart
tools/generate_sample_log.py - Seeded synthetic log generator, if needed
```

## Limitations, honestly

- Single process, in-memory only. Restart the server and the
  buckets are gone.
- No multi-node coordination, no authentication, no TLS, and no
  production throughput guarantee.
- The demo clients are simulated labels and IPs chosen in the UI,
  not real authenticated users.
- Performance targets in the PRD, like 10,000 concurrent users,
  are report-and-explain targets, not pass or fail criteria, and
  they are not guaranteed by a standard-library server on a
  student laptop. Anything we report has to be actually measured.

## License

MIT License. See the LICENSE file in this repository.
