# Behavior cases

## Should activate

- “/skillz:requirements-rewrite refresh our requirements” in Claude Code. An explicit invocation from an old habit or script; it follows `adr-snapshot`.
- “$requirements-rewrite refresh our requirements” in Codex. The explicit mention loads the alias, which follows `adr-snapshot`.
- “/skillz:requirements-rewrite” with no repository or scope. It follows `adr-snapshot`, which asks for the missing source before drafting.

A deprecated alias is explicit-only, so it has no indirect case here; the indirect request is listed under Should not activate, where `adr-snapshot` handles it.

## Should not activate

- “Bring our requirements up to date with the ADRs.” Without the old name, `adr-snapshot` activates directly and this alias does not compete with it.

## Expected behavior

- Reads `../adr-snapshot/SKILL.md` and follows it with the same inputs, resolving its references from `../adr-snapshot/`.
- Tells the user once that the skill is now `adr-snapshot` and the alias will be removed in 0.5.0.
- When `../adr-snapshot/SKILL.md` is missing, stops and asks the user to install the `skillz` plugin and invoke `adr-snapshot`, rather than improvising the workflow.
- Never activates implicitly in Codex or Claude Code.
