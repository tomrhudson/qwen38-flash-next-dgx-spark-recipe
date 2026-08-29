# Sanitized benchmark baseline

This baseline was collected from an external load-generator host against the
direct API of two DGX Sparks running the configuration in `.env.example`.
Endpoint addresses, SSH targets, hostnames, credentials, generated reasoning,
and raw request traces are intentionally omitted.

## Decode concurrency

Each request used approximately 256 input tokens and a forced 512-token
completion. Throughput is aggregate output tokens per second.

| Concurrency | Output tok/s | Speedup vs c1 | Efficiency | TTFT p95 | E2E p95 |
|---:|---:|---:|---:|---:|---:|
| 1 | 38.43 | 1.00× | 100% | 0.41s | 14.81s |
| 2 | 68.64 | 1.79× | 89% | 0.82s | 15.74s |
| 4 | 151.70 | 3.95× | 99% | 1.28s | 15.68s |
| 8 | **215.06** | **5.60×** | 70% | 1.58s | 20.02s |
| 12 | 153.55 | 4.00× | 33% | 29.90s | 58.02s |
| 16 | 184.47 | 4.80× | 30% | 30.48s | 49.99s |

At offered concurrency 12, live SGLang metrics showed 8 running and 4 queued
requests. Concurrency 8 was the measured throughput optimum.

## Context and prefix behavior

| Workload | TTFT p95 | E2E p95 | Result |
|---|---:|---:|---|
| 4K unique, c1 | 2.55s | 4.55s | Pass |
| 32K unique, c1 | 19.36s | 21.24s | Pass |
| 128K unique, c1 | 83.49s | 85.58s | Pass |
| 240K passkey, c1 | 598.56s | 600.04s | 1/1 correct |
| 32K shared prefix, warm, c4 | 0.78s | 6.56s | Pass |

The native 262K allocation works, but near-window prefill is suitable for batch
work rather than interactive use. Reusing long shared prefixes materially
improves latency.

## Sustained load and canaries

- 20-minute concurrency-8 soak: 374/374 requests completed.
- Sustained output throughput: 157.61 tokens/s.
- Soak TTFT p50/p95: 0.93s / 1.64s.
- Soak E2E p50/p95: 26.00s / 37.76s.
- Deterministic serving canaries: 12/12 passed.
- SGLang retractions: 0.
- Container restarts during the run: 0.

These canaries cover the serving/parser/concurrency path; they are not a broad
model-quality evaluation.
