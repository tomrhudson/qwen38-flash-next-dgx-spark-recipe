# Security

## Reporting

Open a private GitHub security advisory for vulnerabilities in this recipe. Do
not include credentials, private keys, tokens, internal addresses, or logs from
a private deployment in a public issue.

## Deployment boundary

The SGLang API launched by this recipe has no authentication. Keep it on a
trusted network and place an authenticated proxy or firewall in front of it.
The example configuration binds the API to loopback by default.

Never commit `.env`, Hugging Face tokens, SSH material, generated logs, model
weights, cache snapshots, or host-specific inventory. Run
`python3 scripts/audit_public_tree.py` before publishing changes.
