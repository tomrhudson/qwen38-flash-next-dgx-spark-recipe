# Qwen3.8 Flash Next on two DGX Sparks

A weights-free, two-node SGLang deployment recipe for
[`RadixArk/Qwen3.8-Flash-Next-NVFP4`](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4)
on two NVIDIA DGX Sparks using tensor parallelism 2 over a direct ConnectX-7
RoCEv2 link.

The repository contains launcher code and configuration only. It does **not**
contain model weights, Hugging Face caches, container images, credentials,
hostnames, or private network addresses. The launcher downloads the public
checkpoint into each operator's local Hugging Face cache at runtime.

## Validated recipe

| Setting | Value |
|---|---:|
| Model | `Qwen3.8-Flash-Next-NVFP4` |
| Topology | 2× DGX Spark, TP=2 |
| Context | `262144` tokens |
| `MEM_FRACTION_STATIC` | `0.78` |
| `MAX_MAMBA_CACHE_SIZE` | `40` |
| `CHUNKED_PREFILL_SIZE` | `2048` |
| `MAX_RUNNING_REQUESTS` | `16` |
| NEXTN | steps/top-k/draft `3/1/4` |

The server accepts 16 admitted requests, but the tested Mamba-state allocation
executed approximately 8 simultaneously. Use client concurrency 8 for normal
throughput-oriented operation; concurrency above 8 primarily adds queueing.

See [BENCHMARK.md](BENCHMARK.md) for the sanitized performance baseline.

### Why these memory and concurrency defaults?

`MEM_FRACTION_STATIC=0.78` and `MAX_MAMBA_CACHE_SIZE=40` are validated
operating defaults for this two-Spark configuration, not proven optimal values.
The hybrid cache architecture constrains the memory/concurrency tradeoff, but it
does not require these exact numbers. They were selected from the observed
memory budget and runtime limits, then checked with long-context, concurrency,
and sustained-load tests; no exhaustive parameter sweep or controlled
before/after throughput comparison was performed.

The previous `MEM_FRACTION_STATIC=0.70` configuration allocated only 179,136 KV
tokens per rank, less than the configured 262,144-token context. After tuning,
the pool held 831,552 tokens (about 10.11 GB per rank), with roughly 22 GiB of
host memory still available per Spark immediately after validation. The `0.78`
choice increased capacity for long contexts and reusable prefixes while
retaining headroom for runtime workspaces and the operating system. This
fraction budgets static allocations including model weights and the KV pool;
it is not a cache-only fraction or a guarantee of higher single-request decode
speed.

The Mamba limit counts **state slots, not requests or gigabytes**. In the tested
SGLang runtime, with `MAMBA_RADIX_CACHE_STRATEGY=extra_buffer` and NEXTN
steps/top-k/draft `3/1/4`, startup reported **five state slots per running
request**. The resulting concurrency limit was:

```text
floor(40 state slots / 5 slots per request) = 8 running requests
```

The previous 38-slot allocation supported only seven. Raising
`MAX_RUNNING_REQUESTS` to 16 cannot override this state-pool limit; requests
beyond the eight executing requests queue. At offered concurrency 12, the
benchmark observed eight running and four queued requests. Concurrency eight
also delivered the best measured decode throughput, and the 20-minute soak
completed 374/374 requests with zero retractions or container restarts.

The five-slot cost is specific to the tested runtime and cache/speculation
settings, not a universal property of the model. Recheck startup allocation
logs, effective concurrency, memory headroom, and benchmark results when
changing the SGLang build, cache strategy, or speculative-decoding settings.

## Prerequisites

- Two DGX Sparks with Docker and the NVIDIA container runtime.
- A direct ConnectX-7 cable with RoCEv2 configured on both nodes.
- Passwordless SSH from the head Spark to the worker Spark.
- At least 170 GiB free per node for the checkpoint, image, and build/cache
  overhead on first setup.
- `curl`, `rsync`, `nvidia-smi`, and either `hf`, `huggingface-cli`, or Python's
  `huggingface_hub` available to the launcher.

The launcher targets GB10/SM121 and builds a derivative SGLang image containing
the upstream recipe's Triton fallback for Qwen Sparse Attention. Do not use
`--load-format dummy` for this checkpoint on GB10; the temporary allocation can
overcommit unified memory and make a node unresponsive.

## Quick start

```bash
git clone https://github.com/tomrhudson/qwen38-flash-next-dgx-spark-recipe.git
cd qwen38-flash-next-dgx-spark-recipe
cp .env.example .env
```

Edit only the local topology in `.env` first:

- `HEAD_CX7_IP` and `WORKER_CX7_IP`
- the CX-7 interface/HCA names if they differ
- `WORKER_HOST`, `WORKER_USER`, or `WORKER_SSH`
- `HOST_BIND` if private-network clients must reach the API

Then validate before downloading or starting anything:

```bash
./start.sh doctor
./start.sh download
./start.sh serve
```

`./start.sh` without an action runs the complete preflight, download, image
build, synchronization, and serving sequence.

## Operations

| Command | Purpose |
|---|---|
| `./start.sh doctor` | Read-only Docker, GPU, memory, disk, SSH, fabric, and recipe checks |
| `./start.sh download` | Download and verify the checkpoint, then synchronize the worker |
| `./start.sh serve` | Build/resolve the image and start worker then head |
| `./start.sh status` | Show API and container state on both nodes |
| `./start.sh logs` | Tail head and worker logs |
| `./start.sh smoke` | Run a direct OpenAI-compatible smoke request |
| `./stop.sh` | Stop both recipe containers |

## API security

SGLang's endpoint is unauthenticated. `.env.example` therefore binds to
`127.0.0.1`. If you change `HOST_BIND`, expose it only on a trusted private
network behind an authenticated proxy or firewall. Never forward the API port
directly to the public internet.

## Weights and licensing

No weights are redistributed here. The launcher references the model repository
by ID and downloads it at runtime. Review and accept the model publisher's
license and terms independently before use. Container images and third-party
dependencies retain their own licenses.

The launcher is derived from Mia's AI Lab's MIT-licensed
[`Qwen3.8-Flash-Next-Dual-DGX-Sparks`](https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks)
recipe. See [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

## Public-tree safety check

Before publishing changes:

```bash
python3 scripts/audit_public_tree.py
bash -n start.sh stop.sh
```

The audit rejects common credential formats, private keys, known private
topology markers, weight formats, unapproved `.env` files, large artifacts,
and symlinks.
