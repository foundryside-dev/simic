# PDR-0019 — Design-system recovery path: re-export if it survives, else reconstruct — never fabricate

Date: 2026-08-09   Status: proposed   Author: Claude (product-owner session)
Owner sign-off: REQUIRED — the deciding fact (does the SimicDesignSystem
project survive in the owner's claude.ai/design UI?) is owner-visible only.
Related: simic-42e575b93c, commit 6e74997, PDR-0018 (the divergence table),
memory: simic-design-system-partial-export

## Context

`.claude/skills/simic-design/` turned out to be the compiled-export residue
of a claude.ai Design System project (`SimicDesignSystem_5a908e`): commit
6e74997 committed 8 of ~41 files; the 33 manifest-referenced source files
(tokens, components, guidelines, UI kits) were never committed and no
matching project exists in the owner's writable claude.ai project list
(verified via DesignSync 2026-08-09). The skill is `user-invocable` and its
own instructions send agents into the missing tree.

## The call (proposed)

1. Owner checks whether the project survives anywhere in claude.ai/design.
2. If yes: full re-export / DesignSync pull, then re-apply the site's token
   corrections per the readme's divergence table.
3. If no: reconstruct from `_ds_bundle.js` (compiled components with source
   hashes) + `_ds_manifest.json` (44 tokens, card metadata) +
   `site/style.css` (token ground truth), clearly marked as reconstruction.
4. Standing constraints either way: never fabricate the missing files as if
   original; never hand-trim the generated descriptors (readme Index,
   github.md screen map) to match disk — they are the record of the gap.

Interim mitigations already merged (PDR-0018): `styles.css` flattened from
the site tokens with a provenance comment; readme warning block naming the
33 missing files and the re-sync checklist.

## Rationale

The compiled bundle makes the export look self-sufficient until something
follows a source path; leaving the skill half-broken compounds with every
session that invokes it. Reconstruction is ~80% mechanical but writes
history it cannot verify (source hashes will not match), so re-export is
strictly better if available — hence the owner-gated fork rather than an
autonomous choice.

## Reversal trigger

If reconstruction is chosen and a later re-sync surfaces the original
project, the reconstruction is discarded wholesale in favour of the export
(the sourceHashes in the bundle adjudicate which files are original).
