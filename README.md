# Skillz

Personal agent workflows for Codex and Claude Code, published as [open Agent Skills](https://agentskills.io).

## Skills

| Skill | Use it for |
| --- | --- |
| [`adr-snapshot`](plugins/skillz/skills/adr-snapshot/SKILL.md) | Restating accepted ADRs as current requirements, or refreshing them after new ADRs or a refactor. A bundled script locks the requirements to the ADR versions they cover and checks it in CI, so writing an ADR never forces other document edits; new ADRs show as pending until the next refresh. Fully superseded ADRs are deleted, since git keeps them. |
| [`deep-reader`](plugins/skillz/skills/deep-reader/SKILL.md) | Studying a long book, thesis, or paper chapter by chapter without loading it all into context, keeping page-anchored notes you can come back to and verifying quotes against the source. Third-party, from [tronghieu/agent-skills](https://github.com/tronghieu/agent-skills). |
| [`distill-book`](plugins/skillz/skills/distill-book/SKILL.md) | Turning an EPUB or PDF into a 30-second, 3-minute, and 10-minute briefing of its most valuable ideas, with every claim linked back to the source and an optional interactive HTML reader. Third-party, from [qianquandong/book80-skill](https://github.com/qianquandong/book80-skill). |
| [`implement-scratch-tickets`](plugins/skillz/skills/implement-scratch-tickets/SKILL.md) | The `implement-tickets` workflow for tickets kept as markdown files in the repository: it builds a feature's `.scratch/<feature>/issues/` ticket files into a chain of draft PRs, reviews and fixes them, and never touches the ticket files. Claude Code only, started by typing the command. |
| [`implement-tickets`](plugins/skillz/skills/implement-tickets/SKILL.md) | Building a spec's ready-for-agent GitHub tickets into a chain of draft PRs, one per ticket, each reviewed and fixed by agents that did not write it, then a run report. Claude Code only, started by typing the command. Copied from [cipherstash/skills](https://github.com/cipherstash/skills). |
| [`performance-engineering`](plugins/skillz/skills/performance-engineering/SKILL.md) | Designing, diagnosing, and optimizing software for latency, throughput, CPU, and memory. Works from user-facing budgets and representative measurement through algorithms, allocation, numerical contracts, and SIMD, with Rust and C++ guidance. |
| [`rust-benchmark-ci`](plugins/skillz/skills/rust-benchmark-ci/SKILL.md) | Setting up criterion benchmarks and a CI regression gate you can trust: github-action-benchmark with committed floors, a gh-pages benchmark series, allocation-count series, and rules for when a benchmark number proves a performance claim. |

All ship in the `skillz` plugin. Agents pick a skill from its description, so describe the problem ("this endpoint got slow", "add a benchmark gate to CI", "refresh our requirements after the refactor") and the matching skill loads.

### Workflow skills

`implement-tickets` runs a Claude Code workflow script that ships inside the skill, so the command is found in any repository. Only a person can start it, because typing the command is their opt-in to a run of up to four agents at once. It never merges a PR or marks one ready. Codex cannot run workflows, so in Codex it says so and stops. It needs Git and GitHub access for its agents. It uses more things where they are there:

- The `mattpocock-skills` plugin, whose `tdd` and `code-review` skills its agents call. skillz does not install it. Without it, the agents follow its steps themselves: red, green, refactor to build, and a review of the diff against the ticket. Each records a deviation.
- The Claude review routine in a repository's `.github/workflows/claude-review.yml`, which a review request for `cipherstash-agent` starts. The script's `routine` argument defaults to whether the repository has that file. Without it, the run requests no routine review and waits for none, a Haiku step waits for CI only, and each fix round audits the independent review, the PR's threads and CI. Pass `routine off` in a repository whose `claude-review.yml` is started some other way, such as this one's.
- The `company-skills` plugin from [cipherstash/skills](https://github.com/cipherstash/skills), whose `authoring-pull-requests`, `review-audit`, `review-fix` and `run-report` skills its agents call by name. skillz does not install it.

`implement-scratch-tickets` is the same workflow, with the same dependencies, for tickets kept as markdown files instead of GitHub issues. It reads the layout the `mattpocock-skills` local tracker writes: an optional `.scratch/<feature>/spec.md`, and one `.scratch/<feature>/issues/<NN>-<slug>.md` file per ticket, with a `Status: ready-for-agent` line on each ticket to build and a `Blocked by:` line naming the tickets that gate it. The run reads the files but never edits, stages or commits them, and passes each ticket's text to its agents, so it works when `.scratch/` is ignored by git. Each PR names its ticket on a `Ticket: <path>` line instead of closing an issue.

### Renamed skills

| Old name | New name | Renamed in | Alias removed in | Behaviour changed |
| --- | --- | --- | --- | --- |
| `requirements-rewrite` | `adr-snapshot` | 0.4.0 | 0.5.0 | 0.5.0 replaced the snapshot markers and same-change maintenance with a script-maintained lock file checked in CI. |

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
