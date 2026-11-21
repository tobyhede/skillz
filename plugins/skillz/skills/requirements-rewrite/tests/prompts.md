# Behavior cases

## Should activate

- “Use requirements-rewrite to refresh our requirements.” Invoked by name, it follows `adr-snapshot`.
- “/skillz:requirements-rewrite on this repository.” An explicit invocation from an old habit or script.
- “Run requirements-rewrite.” With no repository or scope available, follow `adr-snapshot`, which asks for the missing source before drafting.

## Should not activate

- “Bring our requirements up to date with the ADRs.” Without the old name, `adr-snapshot` activates directly and this alias does not compete with it.

## Expected behavior

- Reads `../adr-snapshot/SKILL.md` and follows it with the same inputs, resolving its references from `../adr-snapshot/`.
- Tells the user once that the skill is now `adr-snapshot` and the alias will be removed in a later release.
- Never activates implicitly in Codex or Claude Code.
