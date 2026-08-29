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
