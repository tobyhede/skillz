---
name: requirements-rewrite
description: Deprecated alias for adr-snapshot, kept for one release after the rename. Use only when requirements-rewrite is invoked by name; adr-snapshot activates for every other request.
disable-model-invocation: true
---

# Requirements rewrite (deprecated alias)

This skill was renamed to `adr-snapshot`. Tell the user once that `requirements-rewrite` is now `adr-snapshot` and that this alias will be removed in 0.5.0.

If the installed `adr-snapshot` skill is available, read `../adr-snapshot/SKILL.md` and follow it with the same inputs. Its `references/`, `scripts/` and other paths resolve from `../adr-snapshot/`; this alias directory holds none of them. If it is not available, for example because only this alias was installed, stop and ask the user to install the `skillz` plugin and invoke `adr-snapshot` instead.
