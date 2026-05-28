# CLI reference

Every Precept command. Run `precept --help` for live help.

## Project commands

### `scan`

Scan a repo and show its cognitive profile.

```bash
precept scan [path]
precept scan . --json
```

### `analyze`

Run the full Intent → Impact → Risk pipeline on a request.

```bash
precept analyze "add rate limiting to /login" --repo .
precept analyze "..." --repo . --json
```

### `impact`

Show the blast radius of a planned change (single repo).

```bash
precept impact "rename users.email column" --repo .
```

### `conventions`

List all detected conventions + forbidden patterns.

```bash
precept conventions .
```

### `assets`

List reusable assets (components, hooks, utils, services), optionally filtered by domain.

```bash
precept assets             # all assets
precept assets billing     # filter by domain
```

### `pack`

Show the built-in cognition pack for a domain.

```bash
precept pack auth
precept pack payment
```

Available domains: `auth`, `otp`, `payment`, `webhook`, `order`, `notification`, `worker`.

### `graph`

Export the cognitive graph for a single repo.

```bash
precept graph mermaid --repo .
precept graph dot --repo . | dot -Tpng > graph.png
precept graph react_flow --repo .
```

## Memory commands

### `memory list`

List all memory entries (approved + pending), optionally filtered.

```bash
precept memory list --repo .
precept memory list --domain billing --repo .
```

### `memory recall`

Fuzzy search approved memory.

```bash
precept memory recall "rate limit" --repo .
```

### `memory decide`

Record an auto-approved team decision.

```bash
precept memory decide billing \
  "Use Stripe for subscriptions" \
  --body "Stripe Billing for B2C, manual invoice for B2B over $10k"
```

### `memory forget`

Delete a memory entry.

```bash
precept memory forget <entry-id>
```

## Workspace (multi-repo)

### `workspace create`

Create a central workspace at `~/.precept/workspaces/<name>/`.

```bash
precept workspace create my-product
```

### `workspace list`

List all central workspaces.

```bash
precept workspace list
```

### `workspace init`

Create a `precept.toml` in the current folder (legacy sibling-layout mode).

```bash
precept workspace init
```

### `workspace scan`

Scan all repos in the current workspace and show summary.

```bash
precept workspace scan
```

### `workspace impact`

Cross-repo blast radius for a change in one repo.

```bash
precept workspace impact api --change "rename users.email"
```

### `workspace graph`

Export the cross-repo graph.

```bash
precept workspace graph mermaid
precept workspace graph react_flow --json
```

## Link (per-repo)

### `link`

Connect this repo to a central workspace.

```bash
precept link my-product \
  --role backend \
  --domains billing,auth \
  --critical
```

This writes `.precept/config.toml` — commit it to git so every clone connects automatically.

### `unlink`

Remove the link.

```bash
precept unlink
```

### `migrate`

Move legacy `<repo>/.precept/{memory,approvals}.json` into the central workspace.

```bash
precept migrate
precept migrate --workspace my-product --dry-run
```

## Approval queue

### `approval list`

List pending approval requests.

```bash
precept approval list
```

### `approval show`

Show details of one request.

```bash
precept approval show <id>
```

### `approval approve` / `reject`

```bash
precept approval approve <id>
precept approval reject <id> --reason "too risky before release"
```

## MCP server

### `mcp`

Start the MCP server (stdio by default — for Claude Code, Cursor, Cline).

```bash
precept mcp --repo .
precept mcp --sse --port 8765 --repo .
```

## Global flags

| Flag | Description |
|---|---|
| `--repo / -r` | Path to the repo (default `.`) |
| `--workspace / -w` | Path to workspace root |
| `--json` | Output raw JSON instead of pretty table |
| `--help` | Show help for any command |

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PRECEPT_HOME` | `~/.precept` | Central knowledge home |
| `QDRANT_URL` | (none) | Enable semantic search via Qdrant |
| `QDRANT_API_KEY` | (none) | Qdrant cloud auth |
