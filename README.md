# Skillz

Agent workflows for Codex and Claude Code, published as [open Agent Skills](https://agentskills.io).

## Skills

| Skill | Use it for |
| --- | --- |
| [`performance-engineering`](plugins/skillz/skills/performance-engineering/SKILL.md) | Designing, diagnosing, and optimizing software for latency, throughput, CPU, and memory. Works from user-facing budgets and representative measurement through algorithms, allocation, numerical contracts, and SIMD, with Rust and C++ guidance. |
| [`rust-benchmark-ci`](plugins/skillz/skills/rust-benchmark-ci/SKILL.md) | Setting up criterion benchmarks and a CI regression gate you can trust: github-action-benchmark with committed floors, allocation-count series, and rules for when a benchmark number proves a performance claim. |

Both ship in the `skillz` plugin. Agents pick a skill from its description, so describe the problem ("this endpoint got slow", "add a benchmark gate to CI") and the matching skill loads.

## Install

**Claude Code**

```text
/plugin marketplace add tobyhede/skillz
/plugin install skillz@tobyhede
```

**Codex**: add this repository as a plugin marketplace, then install `skillz` from the `tobyhede` marketplace.

For local development, point the marketplace at your checkout instead (`/plugin marketplace add /path/to/skillz`). See the [Claude Code plugin marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces) and [Codex skills docs](https://developers.openai.com/codex/skills/) for other options.

## Layout

```text
.
├── .agents/plugins/marketplace.json   # Codex marketplace
├── .claude-plugin/marketplace.json    # Claude Code marketplace
└── plugins/skillz/
    ├── plugin.json                     # Agent Plugins manifest
    └── skills/<skill-name>/            # The one source for each skill
```

Each skill is written once under `plugins/skillz/skills/` and both marketplaces publish that directory, so the Codex and Claude Code versions are always the same files.

## Contributing

Add a skill at `plugins/skillz/skills/<skill-name>/SKILL.md`, following [CONTRIBUTING.md](CONTRIBUTING.md) for naming, descriptions, references, and the required behavior cases. Then run the validator, which pull requests also run in CI:

```sh
python3 scripts/validate.py
```

When you add a skill, add a row to the table above.

## License

MIT
