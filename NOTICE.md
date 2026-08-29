# Attribution and provenance

`start.sh`, `stop.sh`, and `LICENSE` are derived from the MIT-licensed
[`MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks`](https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks)
repository, validated from upstream commit
`dccb035c559f342fe8c0f65eb427671c6cf60730`.

Changes in this repository:

- default to the validated native-context settings `0.78 / 40 / 262144 / 2048 / 16`;
- provide a security-conscious generic `.env.example`;
- document a sanitized concurrency, context, prefix-cache, and soak baseline;
- add explicit weight/cache exclusions and a public-tree safety audit;
- omit upstream funding metadata and all deployment-local state.

No model weights, container layers, Hugging Face cache objects, logs,
credentials, or private topology data are redistributed.
