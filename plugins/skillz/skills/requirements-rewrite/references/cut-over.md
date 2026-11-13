# Cut-over

Use this once the intended authority change is settled and the content is audited.

## Prepare

Search incoming references before moving anything: documentation links and anchors, agent entry points, skills, diagnostics, source comments, tests, CI and generators. Confirm that retained engineering guidance has a reachable owner. Preserve user files and follow the task's archive and deletion constraints.

Choose a reversible archive layout. Preserve original bodies when traces depend on their wording or line numbers; explain historical path conventions in the archive index. Mark the archive as history, not binding, and point readers to current requirements.

Use forwarding pages only where existing consumers need them. Each should route to the current owner without duplicating rules. Record why a forwarding page remains and how it can eventually be removed. Keep current instructions out of the historical archive.

## Switch authority together

- Route implementation tasks from the repository’s agent entry points to the owning requirements, with triggers for the distinct task branches. Preserve any established mirror or symlink mechanism.
- Keep the repository’s glossary to names and definitions.
- Replace the old decision-maintenance workflow with same-commit updates to the owning requirements. Preserve engineering conventions that still apply.
- Update skill pointers, diagnostic links and documentation-check roots or expectations affected by moved files.
- Distinguish documentation adaptations from product fixes. Keep recorded implementation defects out of the rewrite unless the user expands the scope.

Inspect every changed diff, including delegated edits. Check the whole proposed branch diff, since earlier commits can contain faults absent from the latest patch.

## Verify and deliver

Run checks against the exact cut-over tree. Compare archived originals with the source revision, resolve live links and anchors, run rule-reference checks, and exercise relevant existing documentation consumers. Report missing dependencies and failed commands explicitly; a parser or link scan does not substitute for unexecuted tests.

Refresh the target revision before delivery and reconcile relevant changes through that SHA. Follow the repository's publishing and review workflow only within the user's authorization. A conflicting draft PR may be a useful intermediate deliverable, but report its unresolved integration and freshness limits.

Leave a durable record containing the delivered commit, target revision, validation results, unresolved questions and any remaining work. Distinguish “published” from “integrated” and “audited” from “tests passed”.
