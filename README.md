# Skillz

Personal agent workflows for Codex and Claude Code, published as [open Agent Skills](https://agentskills.io).

## Skills

| Skill | Use it for |
| --- | --- |
| [`deep-reader`](plugins/skillz/skills/deep-reader/SKILL.md) | Studying a long book, thesis, or paper chapter by chapter without loading it all into context, keeping page-anchored notes you can come back to and verifying quotes against the source. Third-party, from [tronghieu/agent-skills](https://github.com/tronghieu/agent-skills). |
| [`distill-book`](plugins/skillz/skills/distill-book/SKILL.md) | Turning an EPUB or PDF into a 30-second, 3-minute, and 10-minute briefing of its most valuable ideas, with every claim linked back to the source and an optional interactive HTML reader. Third-party, from [qianquandong/book80-skill](https://github.com/qianquandong/book80-skill). |
| [`performance-engineering`](plugins/skillz/skills/performance-engineering/SKILL.md) | Designing, diagnosing, and optimizing software for latency, throughput, CPU, and memory. Works from user-facing budgets and representative measurement through algorithms, allocation, numerical contracts, and SIMD, with Rust and C++ guidance. |
| [`rust-benchmark-ci`](plugins/skillz/skills/rust-benchmark-ci/SKILL.md) | Setting up criterion benchmarks and a CI regression gate you can trust: github-action-benchmark with committed floors, a gh-pages benchmark series, allocation-count series, and rules for when a benchmark number proves a performance claim. |
| [`requirements-rewrite`](plugins/skillz/skills/requirements-rewrite/SKILL.md) | Restating accepted ADRs and overlapping guides as a requirements snapshot at a recorded revision, or refreshing it after refactoring or new ADRs, while ADRs stay the binding history and the CONTEXT.md and ADR workflow route through the snapshot. |

All ship in the `skillz` plugin. Agents pick a skill from its description, so describe the problem ("this endpoint got slow", "add a benchmark gate to CI", "refresh our requirements after the refactor") and the matching skill loads.

## Install

**Claude Code**

```text
/plugin marketplace add tobyhede/skillz
/plugin install skillz@tobyhede
```

To develop against a local checkout, add the marketplace by path instead: `/plugin marketplace add /path/to/skillz`.

**Codex**: add this repository as a plugin marketplace, then install `skillz` from the `tobyhede` marketplace.

See the [Claude Code plugin marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces) and [Codex skills docs](https://developers.openai.com/codex/skills/) for other options.

## Layout

```text
.
├── .agents/plugins/marketplace.json   # Codex marketplace
├── .claude-plugin/marketplace.json    # Claude Code marketplace
└── plugins/skillz/
    ├── plugin.json                     # Agent Plugins manifest
    ├── .codex-plugin/plugin.json       # Codex manifest; its "skills" field publishes skills/
    ├── .claude-plugin/plugin.json      # Claude Code manifest
    └── skills/<skill-name>/            # The one source for each skill
```

Both marketplaces point at `plugins/skillz`, and each skill is written once under `skills/`, so Codex and Claude Code load the same skill files. The three `plugin.json` manifests must agree on name, version, description, and license; bump the version in all three for a release.

## Contributing

Follow [CONTRIBUTING.md](CONTRIBUTING.md) to add or change a skill. Before opening a pull request, run the same checks CI runs:

```sh
python3 scripts/validate.py
for t in plugins/skillz/skills/*/tests; do ls "$t"/test_*.py >/dev/null 2>&1 && python3 -m unittest discover -s "$t"; done
```

The validator fails until a new skill has a row in the table above.

## License

MIT. Third-party skills keep their upstream license and attribution in their own directory: see each skill's `LICENSE` and `PROVENANCE.md`.
