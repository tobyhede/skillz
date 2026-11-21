---
name: requirements-rewrite
description: Deprecated alias for adr-snapshot, kept for one release after the rename. Use only when requirements-rewrite is invoked by name; adr-snapshot activates for every other request.
disable-model-invocation: true
---

# Requirements rewrite (deprecated alias)

This skill was renamed to `adr-snapshot`. Read `../adr-snapshot/SKILL.md` and follow it with the same inputs. Its `references/`, `agents/` and `tests/` paths resolve from `../adr-snapshot/`; this alias directory holds none of them.

Tell the user once that `requirements-rewrite` is now `adr-snapshot` and that this alias will be removed in a later release.
