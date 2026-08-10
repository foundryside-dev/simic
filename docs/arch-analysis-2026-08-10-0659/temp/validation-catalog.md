# Validation Report — 02-subsystem-catalog.md

**Validator:** analysis-validator (independent)
**Document:** `docs/arch-analysis-2026-08-10-0659/02-subsystem-catalog.md` (911 lines, 9 entries)
**Contract:** `docs/arch-analysis-2026-08-10-0659/temp/task-explorers.md` (Output Contract block, lines 13–38)
**Date:** 2026-08-10
**Scope:** CHECK 1 (contract compliance) + CHECK 2 (bidirectional dependency matrix) only, per coordinator brief. Evidence quality, source verification against `experiments/kernel_demo.py`, and Plotting Sidecar factual claims were explicitly out of scope and were not performed.

---

## STATUS: NEEDS_REVISION (CRITICAL)

**Blocking issue:** the dependency matrix does not close. 8 asymmetries across 9 entries, including one **direction contradiction** (two entries each declaring the other as inbound-only) and one **intra-entry contradiction** (one entry declaring the same neighbour as both inbound and outbound, with the inbound evidence describing an outbound edge). This feeds diagram generation; an edge that two entries disagree about cannot be drawn correctly, and a naive merge would silently pick one.

**Second critical issue:** the catalog is **stale** relative to three of its eight temp sources. Three entries in the merged catalog are older revisions than what the explorers left on disk.

**CHECK 1 is otherwise clean:** all 9 entries carry all 8 sections, in contract order, with no extras and no truncation.

---

# CHECK 1 — Contract compliance

## 1.1 Section presence and ordering — PASS (9/9)

Verified mechanically: every line that begins with `**` at column 0 **and** is preceded by a blank line (i.e. every block that a section-splitting parser would treat as a section header) was enumerated across the whole file. Result: exactly 7 such blocks per entry, in exactly the contract order, for all 9 entries, plus the 3 document-header blocks (`Target`, `Version anchor`, `Entries`).

| # | Entry | Line | Location | Responsibility | Key Components | Dependencies | Patterns | Concerns | Confidence | `---` |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Identity, Config & Determinism Spine | 19 | 21 | 23 | 25 | 41 | 45 | 55 | 67 | 69 |
| 2 | Data, Episodes & Telemetry | 71 | 73 | 75 | 77 | 96 | 100 | 108 | 116 | 118 |
| 3 | Host, Seeds & Slot Lifecycle | 120 | 122 | 124 | 126 | 148 | 152 | 167 | 176 | 178 |
| 4 | Counterfactual Fan Executor | 180 | 182 | 184 | 189 | 237 | 252 | 312 | 367 | 388 |
| 5 | Records & Store | 390 | 392 | 394 | 396 | 410 | 415 | 430 | 444 | 446 |
| 6 | Policy & Learning | 448 | 450 | 452 | 454 | 470 | 474 | 485 | 495 | 497 |
| 7 | Certification Battery | 499 | 501 | 505 | 511 | 612 | 619 | 655 | 762 | 793 |
| 8 | Run Orchestration & CLI | 795 | 797 | 799 | 801 | 814 | 818 | 833 | 855 | 857 |
| 9 | Plotting Sidecar | 859 | 861 | 863 | 865 | 881 | 885 | 895 | 908 | 910 |

- **No extra sections.** Zero blank-line-preceded `**X:**` blocks beyond the seven contract sections in any entry.
- **No reordering.** Column order above is monotonic in every row.
- **No skipped sections.** 9 × 7 = 63 sections, all present.
- **`Inbound:` / `Outbound:` labels present** in all 9 Dependencies sections (lines 42/43, 97/98, 149/150, 238/244, 412/413, 471/472, 614/615, 815/816, 882/883).

**Informational (not a violation):** entries 5–9 place a blank line between `**Dependencies:**` and the `- Inbound:` bullet; entries 1–4 do not. Cosmetic; both forms parse identically.

## 1.2 The "Falsifiability verdict:" block (line 781) — RESOLVED: legitimate lead-in, NOT an extra section

The coordinator located it at ~773; it is at **line 781**, inside the **Certification Battery** entry.

**Verdict: it is a bolded lead-in inside the existing Confidence section, not a ninth section.** Three independent reasons:

1. **No blank line precedes it.** Line 780 ends `…confirms no CUDA assertion on the preflight/freeze path.` and line 781 begins `**Falsifiability verdict: yes, …`. In Markdown this is a continuation of the same paragraph as the Confidence body (which opens at line 762). It does not render as, and will not parse as, a new block.
2. **It is not in `**Label:**` header form.** The bold span is `**Falsifiability verdict: yes, and more strongly than structure alone would show**` — the bold wraps a full sentence including its predicate, closing at line 782. A section header closes its bold immediately after the colon.
3. **The mechanical section-enumeration in §1.1 does not surface it.** A downstream splitter keyed on blank-line-preceded `**X:**` will place this text inside Confidence, where it belongs.

**However — WARNING, worth fixing:** the block carries *substantive analytical content* (a falsifiability verdict, and an enumerated list of four failure classes that pass certification silently, at lines 781–790) inside a section the contract defines as `[High/Medium/Low] - [files read, lines checked, verification steps]`. Findings (a)–(d) are Concerns-class material. They are recoverable by a human reader but are in the wrong section for any consumer that reads Concerns to build a risk view. A second bolded lead-in, `**Failure classes that pass certification silently:**`, appears at lines 785–786 in true `**Label:**` form — it survives only because it begins mid-line. If any downstream tool ever splits on `**...:**` regardless of line position, that one *will* be misread as a section header.

**Recommendation:** move lines 781–790 into the Certification Battery `**Concerns:**` section (or a document-level synthesis), leaving Confidence to describe verification effort only. Not blocking; does not break contract form.

## 1.3 Truncation and merge integrity — NO TRUNCATION FOUND, but STALENESS FOUND

Method: for each of the 8 temp source files, the entry block was extracted from the `## ` heading through the first `---` following the final `**Confidence:**` line — i.e. the same cut the merge script performs — and tested for verbatim presence in the catalog.

| Temp source | Entries | Verbatim in catalog? |
|---|---|---|
| `catalog-1-identity.md` | 1 | ✅ yes (51 lines) |
| `catalog-2-data.md` | 1 | ✅ yes (48 lines) |
| `catalog-3-host.md` | 1 | ✅ yes (59 lines) |
| `catalog-4-fan.md` | 1 | ✅ yes (209 lines) |
| `catalog-5-store.md` | 1 | ✅ yes (57 lines) |
| `catalog-6-policy.md` | 1 | ✅ yes (50 lines) |
| `catalog-7-certification.md` | 1 | ❌ **no** — catalog has 293 lines, temp has 321 |
| `catalog-8-cli.md` | 2 | ❌ **no** — both entries diverge |

### 1.3a Long entries are GENUINE CONTENT, not merge corruption — CONFIRMED

- **Counterfactual Fan Executor** (catalog lines 180–388, 209 lines): byte-for-byte identical to `temp/catalog-4-fan.md`. The length is real — the entry carries 15 Key Components, 12 Patterns Observed and a 55-line Concerns section. **Not corruption.**
- **Certification Battery** (catalog lines 499–793, 295 lines): the catalog block is a **complete, well-formed prefix-and-suffix-intact** version of the temp entry — all 7 sections present, terminated correctly. It is not truncated; it is an **earlier revision**. See 1.3b.

### 1.3b CRITICAL — the catalog is stale against three entries

File modification times settle this:

```
2026-08-10 07:34:24  02-subsystem-catalog.md      <- last merge
2026-08-10 07:49:41  temp/catalog-7-certification.md
2026-08-10 07:52:42  temp/catalog-8-cli.md
```

The last re-merge ran at **07:34**; explorers 7 and 8 revised their files at **07:49** and **07:52**. Those revisions were never merged. Diffs (temp is the newer, richer text in every case):

**Certification Battery — 3 hunks, 28 lines missing from the catalog:**
- After catalog line 525 (Key Components, money-null): a 6-line paragraph documenting `test_learning.py:91` as the *discriminating* test pinning the rev 6.1 amendment (`0.4 < p < 0.6` band vs. ~1/6 for a point-level shuffle). This is the strongest verification evidence for the rev 6.1 amendment in the analysis and it is absent from the catalog.
- After catalog line 724 (Concerns, freeze-refusal coverage): an 11-line paragraph with **measured** timings (`gate8_pressure` skip path = 18 µs; missing-certificate refusal = 0.5 ms) establishing that the coverage gaps are *not* cost-explained.
- Confidence section: 11 lines replacing 3 — enumerating direct tests for all six statistical estimators, recording that the suite was **executed** (129 passed), and naming a newly-identified untested seam between estimators and threshold logic.

**Run Orchestration & CLI — Concerns section substantially restructured, 6 net new lines:**
- The temp version adds a coverage-status preamble (21 test modules, 129 tests, whole suite executed: 129 passed in 106 s, zero skips, CUDA-capable machine) and **tags every Concern** with a coverage verdict: `[COVERED — recorded for balance]`, `[UNCOVERED]`, `[PARTIAL]`, `[NOT COVERED — closed]`, `[N/A — structural]`.
- Adds two Concerns absent from the catalog entirely: **"The shared episode machinery and the entire collect assembly are tested, including end to end"** (a COVERED counter-finding) and **"The reporting layer consumes a gate-8 output that nothing tests gate 8 for producing."**
- The catalog therefore presents an untagged, less-qualified Concerns list, and omits a finding.

**Plotting Sidecar — version anchor is stale, and CONTRADICTS the catalog's own header:**
- Catalog line 861 (Location): *"Both analysed as **working tree at 2026-08-10 07:21, uncommitted-modified over `853e9ef`**"*
- Temp line 3: *"Both analysed at commit **`aa86388`**"*
- Catalog line 908 (Confidence): *"were read as the **working tree at 2026-08-10 ~07:21**, both `M` (uncommitted-modified) over commit `853e9ef`"* … *"the further uncommitted edits noted by the coordinator mean this entry can be invalidated again by any subsequent save."*
- Temp: *"were read as the working tree at 2026-08-10 ~07:21 and **have since been committed unchanged as `aa86388`**"*

**This is a self-contradiction inside the shipped document.** The catalog **header (lines 6–10)** asserts *"The **Plotting Sidecar** entry was re-done against the sidecar as committed at `aa86388` (07:32)"*, while the **entry it introduces** says it was read from an uncommitted working tree over `853e9ef` and warns it "can be invalidated again by any subsequent save." A reader has no way to know which statement to trust. The temp file resolves it — the working-tree state read at 07:21 *is* what was committed as `aa86388`, unchanged — but that resolution is only in `temp/`, not in the catalog.

**Note the important non-finding:** none of the three stale diffs touches a `**Dependencies:**` section. The dependency matrix in §CHECK 2 below is evaluated against text that is current in both catalog and temp. Staleness does not change the CHECK 2 findings.

## 1.4 Confidence sections citing no files or lines — NONE (0/9)

Per the scope limit, evidence *quality* was not assessed. Presence only: all 9 Confidence sections cite specific files and specific line ranges. Grades: High ×8, Medium ×1 (Run Orchestration & CLI, line 855, self-graded Medium with the reason stated — `run_preflight`'s body 2919–3033 not read).

## 1.5 Naming compliance — PASS (precondition for CHECK 2)

Three checks, all mechanical:

- **Entry headings vs the fixed 9-name list** (`task-explorers.md:52–60`): all 9 `## ` headings match the fixed list **verbatim and in the same order**. Zero drift. This is what makes the CHECK 2 matrix constructible at all.
- **Standing Constraint 4** (*"Dependency names must be drawn from the fixed subsystem-name list so the coordinator can reconcile bidirectionality"*): **compliant.** Stripping code spans and canonical names from all 18 `- Inbound:` / `- Outbound:` bullet lines leaves **zero** unmatched capitalised multi-word phrases — no invented, abbreviated or paraphrased subsystem names. Multi-line continuations (FAN 239–243/245–250, CERT 616–617) were read manually and use canonical names throughout. **PLOT:882** references `tests/unit/kernel_demo/test_plots.py` but explicitly frames it as *"None from the fixed subsystem list … test scaffolding rather than a catalogued subsystem"* — that is the correct way to record an out-of-list dependant and is compliant, not a violation.
- **Standing Constraint 2** (no Simic domain codenames): **compliant.** `grep -icE 'leyline|momir|elesh|urabrask|jin-gitaxias|isperia|wrenn|emrakul|tamiyo|nissa|ugin|aurelia|tolaria|urborg'` over the catalog returns **0**.

## 1.6 Moving-target disclosure — as instructed

**Recorded per coordinator instruction:** the catalog contains **one entry analysed against a moving target.** The Plotting Sidecar entry (lines 859–910) describes `experiments/kernel_demo_plots.py`, a file rewritten upstream mid-analysis. Its factual claims were **not** validated here — form only was checked, and its form conforms. Its *version anchor* is stale and self-contradictory (§1.3b).

---

# CHECK 2 — Bidirectional dependency matrix

## 2.1 Declared edges

Abbreviations: **ID** = Identity, Config & Determinism Spine · **DATA** = Data, Episodes & Telemetry · **HOST** = Host, Seeds & Slot Lifecycle · **FAN** = Counterfactual Fan Executor · **STORE** = Records & Store · **POL** = Policy & Learning · **CERT** = Certification Battery · **CLI** = Run Orchestration & CLI · **PLOT** = Plotting Sidecar.

| Entry | Line | Declared **Inbound** (who depends on me) | Line | Declared **Outbound** (who I depend on) |
|---|---|---|---|---|
| ID | 42 | DATA, HOST, FAN, STORE, POL, CERT, CLI *(PLOT explicitly excluded)* | 43 | **none** |
| DATA | 97 | FAN, STORE, POL, CERT, CLI | 98 | ID, HOST |
| HOST | 149 | FAN, DATA, STORE, CERT, POL, PLOT | 150 | ID |
| FAN | 238–243 | CLI, CERT, STORE\*, POL\* *(\* "without a call edge")* | 244–250 | ID, DATA, HOST |
| STORE | 412 | FAN, CLI, POL, CERT, PLOT | 413 | ID |
| POL | 471 | CLI, CERT, **STORE** | 472 | DATA, **STORE**, ID |
| CERT | 614 | CLI | 615–617 | ID, DATA, HOST, FAN, STORE, POL, CLI |
| CLI | 815 | CERT, PLOT | 816 | ID, DATA, HOST, FAN, STORE, POL, CERT |
| PLOT | 882 | **None** | 883 | CLI, STORE, HOST, FAN |

## 2.2 Coordinator's four claims — all four VERIFIED

| Claim | Verdict | Evidence |
|---|---|---|
| ID Outbound "none within the file"; Inbound "all subsystems except Plotting Sidecar" | ✅ **CONFIRMED** | Line 43 declares no outbound. Line 42 names 7 inbound and explicitly excludes PLOT (*"`kernel_demo_plots.py:19` imports only `SEED_NAMES`, `FanRecord` and `Store`, none of which are defined here"*). PLOT's Outbound (883) correctly omits ID. Fully symmetric — all 7 counterparties declare ID in their Outbound. |
| CLI Outbound to all seven others | ✅ **CONFIRMED** | Line 816 names exactly ID, DATA, HOST, FAN, STORE, POL, CERT. All seven mirror it: ID:42, DATA:97, HOST:149, FAN:238, STORE:412, POL:471, CERT:614. **Zero asymmetries on any CLI outbound edge.** |
| PLOT Inbound "None" | ✅ **CONFIRMED and consistent** | Line 882. No entry anywhere lists PLOT in its Outbound. The negative is genuine, not an omission. |
| CERT ↔ CLI genuine cycle, both sides declared | ✅ **CONFIRMED — both sides declare it** | CERT Inbound = CLI (614) **and** CERT Outbound includes CLI (617). CLI Inbound includes CERT (815) **and** CLI Outbound includes CERT (816). All four half-edges present. This is the only correctly-declared cycle in the catalog. |

## 2.3 Asymmetries — 8 found

Rule applied: for every A declaring B as **Outbound**, B must declare A as **Inbound**; for every A declaring B as **Inbound**, B must declare A as **Outbound**.

### CRITICAL — FAN ↔ STORE: both halves declared as inbound, and the cited half is misattributed

**A1. FAN and STORE each declare the other as *inbound only*. Neither lists the other in Outbound. The one half that carries citations is not supported by them.**
- **FAN**, line 243: *"Records & Store and Policy & Learning consume `ArmResult`'s serialized field names (`rec.arms` read by name at :1845, :2511, :2517) **without a call edge**"* — i.e. FAN asserts **STORE → FAN** (STORE depends on FAN).
- **STORE**, line 412: `Inbound: Counterfactual Fan Executor; …` — i.e. STORE asserts **FAN → STORE** (FAN depends on STORE). **Uncited.**
- Neither entry lists the other in its **Outbound** (FAN:244–250 = ID/DATA/HOST; STORE:413 = ID).

**The three citations behind FAN's claim do not land in STORE.** Checking each against the declared Location ranges:

| Citation | Falls inside | STORE's range (1420–1681)? |
|---|---|---|
| `:1845` | **POL** (1682–1978) | no |
| `:2511` | **CERT** (2502–3062) | no |
| `:2517` | **CERT** (2502–3062) | no |

**Zero of the three fall inside STORE's declared range.** The sentence at line 243 bundles STORE and POL under one citation set, but the consumers at those lines are POL and CERT — both of which FAN already lists separately as Inbound (CERT at line 240, POL in the same sentence). So FAN's STORE clause appears to be a **misattribution**, not a competing directional claim.

That leaves **STORE:412's `Counterfactual Fan Executor` inbound as the only surviving half of this edge, and it carries no citation at all.**

- **Consequence for diagram generation:** as written, a generator that unions the two inbound lists emits a **spurious bidirectional FAN↔STORE edge that neither entry actually claims**, built from one misattributed clause and one uncited name. **Must be resolved before diagrams are generated.**
- **Resolution (do this, not a symmetric adjudication):** delete the `Records & Store` clause from FAN:243 unless source verification finds an `ArmResult` consumer inside 1420–1681; then require STORE:412 to supply its own evidence for the FAN inbound, or drop it.

### CRITICAL — intra-entry contradiction

**A2. POL declares STORE as BOTH Inbound and Outbound, and the Inbound evidence describes an Outbound edge.**
- **POL**, line 471 (Inbound): *"Records & Store (via `load_for_training` `:1672`, immediately above this range, **which is this subsystem's only sanctioned record source**)"* — the parenthetical describes POL *consuming* from STORE, which is an **outbound** relationship, filed under Inbound.
- **POL**, line 472 (Outbound): *"Records & Store (`FanRecord` `:1438`, `SplitViolation`, `_assert_trainable` `:1664`)"* — the same edge, correctly filed.
- STORE, line 412, declares POL as Inbound only; STORE's Outbound (413) does not name POL.
- **Adjudication:** POL → STORE (outbound) is correct and **is** mirrored by STORE's Inbound. The Inbound half at line 471 is **spurious and should be deleted.** Left in place, it manufactures a false STORE → POL edge.

### WARNING — omissions (one side declared, counterpart silent)

**A3. STORE's Outbound is under-declared by four.** STORE, line 413, declares only `Identity, Config & Determinism Spine`. Four other entries name STORE as their Inbound, which requires STORE to name them as Outbound:
- **DATA** line 97 lists STORE as Inbound ⟶ STORE:413 omits DATA.
- **HOST** line 149 lists STORE as Inbound (*"`ArmResult` carries `rms_ratio_blend_entry` :1218 and `alpha_beta_log` :1221"*) ⟶ STORE:413 omits HOST. **Note:** the cited evidence describes `ArmResult` fields, which the FAN entry claims as its own (FAN Key Components, line 1209–1221) — this inbound may be misattributed to STORE when it belongs to FAN.
- **FAN** line 243 lists STORE as Inbound ⟶ STORE:413 omits FAN (see A1).
- **POL** line 471 lists STORE as Inbound ⟶ STORE:413 omits POL (see A2; this half is probably spurious).

**A4. HOST ← POL declared one-sided.** HOST, line 149, lists `Policy & Learning (SEED_NAMES ordering :1776, :1846)` as Inbound. POL's Outbound (472) names DATA, STORE, ID — **not HOST**. Line numbers :1776 and :1846 fall inside POL's own range (1682–1978), so the edge looks real and POL's Outbound is the side that is wrong.

**A5. FAN ← POL declared one-sided.** FAN, line 243, lists POL as Inbound (`rec.arms` read at :1845). POL's Outbound (472) omits FAN. Line :1845 is inside POL's range, so again POL's Outbound is the incomplete side. (Both FAN and POL flag this as a field-name coupling with no call edge — if "no call edge" means "not a dependency", it should be stated symmetrically or dropped from both, not asserted on one side only.)

**A6. PLOT → FAN not mirrored.** PLOT, line 883 (Outbound): *"Counterfactual Fan Executor (imports `end_state_R`, `kernel_demo.py:1188`, and reads the `ArmResult` fields `curve_val`, `alpha_beta_log`, `rms_ratio_blend_entry`, `status`)"*. FAN's Inbound (238–243) names CLI, CERT, STORE, POL — **not PLOT**. This is a concrete, cited import edge; FAN's Inbound is the missing side. Note FAN's own Key Components place `end_state_R` at line 1189 and `ArmResult` at 1209 — the edge is unambiguous.

### Summary table

| # | Edge as declared | Declared at | Counterpart missing/contradicting at | Severity |
|---|---|---|---|---|
| A1 | FAN says STORE→FAN (citations land in POL/CERT, not STORE); STORE says FAN→STORE (uncited) | 243 / 412 | both Outbounds silent: 244–250 / 413 | **CRITICAL** (neither half stands as written) |
| A2 | POL lists STORE as Inbound *and* Outbound | 471 / 472 | STORE:413 omits POL | **CRITICAL** (intra-entry contradiction) |
| A3a | DATA Inbound: STORE | 97 | STORE Outbound 413 omits DATA | WARNING |
| A3b | HOST Inbound: STORE | 149 | STORE Outbound 413 omits HOST | WARNING |
| A3c | FAN Inbound: STORE | 243 | STORE Outbound 413 omits FAN | WARNING (= A1) |
| A3d | POL Inbound: STORE | 471 | STORE Outbound 413 omits POL | WARNING (= A2) |
| A4 | HOST Inbound: POL | 149 | POL Outbound 472 omits HOST | WARNING |
| A5 | FAN Inbound: POL | 243 | POL Outbound 472 omits FAN | WARNING |
| A6 | PLOT Outbound: FAN | 883 | FAN Inbound 238–243 omits PLOT | WARNING |

**Concentration:** 7 of 8 asymmetries involve **STORE's Outbound (line 413)** or **POL's Outbound (line 472)** — two single-line, name-only Dependencies declarations. Both entries wrote a minimal Outbound (STORE: 1 name; POL: 3 names) while their neighbours wrote evidence-cited Inbound lists naming them. Fixing lines 413 and 472, plus adding PLOT to line 238, closes all 8.

## 2.4 Format inconsistency in Dependencies — WARNING

Three entries (DATA:97–98, STORE:412–413, CERT:614–617) give **bare subsystem names with no line citations**. Six entries give names with symbol-and-line evidence. The contract does not require citations here, so this is not a violation — but it is not a coincidence that **two of the three uncited entries (STORE, and CERT's terse `Inbound: Run Orchestration & CLI`) are where the asymmetries cluster.** Uncited Dependencies lines appear to be where the reconciliation broke down.

---

# Required actions before proceeding to diagram generation

**Blocking (must fix, then re-validate):**
1. **Fix A1 (FAN ↔ STORE).** Not a symmetric adjudication: FAN:243's `Records & Store` clause rests on `:1845, :2511, :2517`, all three of which fall in POL/CERT territory, none in STORE's 1420–1681 — **delete that clause** unless source verification finds an `ArmResult` consumer inside STORE's range. Then STORE:412's `Counterfactual Fan Executor` inbound is the sole surviving half and must supply its own evidence or be dropped. Do not let a generator union the two inbound claims.
2. **Fix A2:** delete the spurious `Records & Store` from POL's **Inbound** (line 471); the edge is already correctly declared as POL Outbound at line 472.
3. **Rewrite STORE's Outbound (line 413)** to name every subsystem that declares STORE as Inbound — or remove the corresponding Inbound claims from DATA/HOST/FAN/POL. Currently 4 of 5 STORE edges are one-sided.
4. **Rewrite POL's Outbound (line 472)** to include HOST and FAN, or remove those Inbound claims from HOST:149 and FAN:243.
5. **Add PLOT to FAN's Inbound (line 238–243).** The import edge is cited and unambiguous.
6. **Re-merge the catalog from `temp/`.** Three entries (Certification Battery, Run Orchestration & CLI, Plotting Sidecar) are older than their sources. 28 lines of Certification Battery evidence, a whole CLI Concern, and the coverage tagging of the entire CLI Concerns list are missing from the shipped document.
7. **Resolve the Plotting Sidecar version-anchor contradiction.** The header (lines 6–10) says `aa86388`; the entry (lines 861, 908) says uncommitted working tree over `853e9ef`. The temp file has the corrected text.

**Non-blocking (fix or document as a limitation):**
8. Move the falsifiability verdict and its four failure classes (lines 781–790) from Confidence into Concerns for the Certification Battery entry.
9. Consider re-checking the HOST ← STORE inbound at line 149: its evidence (`ArmResult` fields at :1218, :1221) points at FAN's territory, not STORE's.
10. Normalise Dependencies formatting — either all entries cite symbols and lines, or none do.

**Retry budget:** this is attempt 1 of 2. If a second validation pass on the same issues fails, escalate to the user.

---

# Confidence Assessment

**Overall Confidence: High.**

| Finding | Confidence | Basis |
|---|---|---|
| §1.1 all 63 sections present, ordered, no extras | **High** | Mechanically enumerated every blank-line-preceded `**` block in the file; line numbers tabulated above are directly verified. |
| §1.2 Falsifiability block is a lead-in, not a section | **High** | Directly verified at `02-subsystem-catalog.md:780–782`: no blank line precedes it, bold span closes mid-sentence at line 782, and it does not appear in the mechanical section enumeration. |
| §1.3a long entries are genuine content | **High** | `catalog-4-fan.md` matches the catalog byte-for-byte (209 lines). Certification Battery's catalog block is structurally complete and correctly terminated. |
| §1.3b catalog is stale against 3 entries | **High** | `stat` mtimes (catalog 07:34:24 < temp-7 07:49:41 < temp-8 07:52:42) plus line-level unified diffs reproduced above. |
| §1.3b Plotting version-anchor self-contradiction | **High** | Both texts quoted verbatim from lines 6–10, 861, 908 of the same file. |
| §2.1 declared-edge table | **High** | Transcribed directly from the nine Dependencies sections at the cited line numbers. |
| §2.2 all four coordinator claims confirmed | **High** | Each half-edge checked against its counterpart entry; line numbers given. |
| §1.5 naming compliance (headings, Constraint 2, Constraint 4) | **High** | Mechanically checked: headings vs `task-explorers.md:52–60` byte-identical and same-order; codename grep returns 0; canonical-name stripping over all 18 dependency bullets leaves no residue. |
| §2.3 the 8 asymmetries | **High** for the *declaration* asymmetry (this is a pure textual cross-check of the document against itself). **Insufficient Data** for which side is *factually* right — resolving that requires reading `experiments/kernel_demo.py`, which was explicitly out of scope. |
| §2.3 A1 — FAN:243's STORE clause is misattributed | **High** | The three citations `:1845, :2511, :2517` fall in POL (1682–1978) and CERT (2502–3062); none in STORE (1420–1681). See the containment-validity note below. |
| §2.3 A4/A5/A6 and §action-9 (HOST←STORE probably belongs to FAN) | **High** | Same containment method: `:1776, :1846` ⊂ POL; `:1845` ⊂ POL; `:1188/:1209–1221` ⊂ FAN; `:1218, :1221` ⊂ FAN, not STORE. |

**Why line-range containment is reliable here (raises the four findings above from inference to evidence):** the `**Location:**` ranges in all 9 entries reproduce the contract's Assignments table (`task-explorers.md:64–73`) verbatim and partition lines 1–4,066 without gaps. There are exactly **three** documented overlaps in the whole catalog: ID claims 1534–1546 (inside STORE's block) and 2829–2847 (inside CERT's block), both explicitly acknowledged and reconciled at line 43; and `AGREEMENT_MARGIN` :3256 is claimed by ID's Key Components while falling in CLI's range (flagged separately below). **None** of the citations used in A1/A4/A5/A6/action-9 — `:1188, :1218, :1221, :1776, :1845, :1846, :2511, :2517` — falls in any of those three exception zones. Containment is therefore unambiguous for every finding that relies on it.

# Risk Assessment

**Implementation Risk: Medium.** **Reversibility: Easy** — every required action is a text edit to a Markdown document or a re-run of the merge script; nothing is destructive.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Diagram generator draws the FAN–STORE edge backwards, or invents a bidirectional edge neither entry claims | **High** | **High** if unfixed — a generator must resolve A1 somehow, and every resolution available to it is wrong | Adjudicate A1 against source before generating (action 1) |
| Downstream phases inherit an incomplete dependency graph — 8 of ~34 edges are one-sided, so any consumer reading only Outbound lists sees a graph missing 7 edges | **High** | **High** | Actions 3–5 |
| Diagrams and the architecture report are generated from a catalog that is 3 revisions stale, then the fresher `temp/` content is discovered later and everything must be regenerated | **Medium** | **Medium** | Action 6 — re-merge takes seconds; regenerating diagrams does not |
| A reader trusts the catalog's header (`aa86388`) over the entry (`853e9ef` working tree) or vice versa, and mis-scopes a follow-up | **Medium** | **Medium** | Action 7 |
| The Certification Battery's falsifiability findings (a)–(d) never reach a risk register because they sit in a Confidence section no risk-consumer reads | **Medium** | **Medium** | Action 8 |
| A future `**X:**`-splitting parser misreads `**Failure classes that pass certification silently:**` (line 785) as a section header | **Low** | **Low** | Action 8 removes the hazard as a side effect |
| Fixing the asymmetries by *adding* names rather than *adjudicating* them inflates the graph with edges that do not exist in code | **Medium** | **Medium** | Every fix must be grounded in source, not in making the matrix close — the contract-reviewer's source verification should land first |

# Information Gaps

- **Which side of each asymmetry is factually correct.** Determining whether STORE genuinely depends on DATA/HOST/FAN/POL, and which way FAN–STORE points, requires reading `experiments/kernel_demo.py` — explicitly out of scope here (a separate contract-reviewer agent owns source verification). **If supplied:** would convert each asymmetry from "the document disagrees with itself" into a specific one-line correction, and would settle A1's direction.
- **Whether the FAN/POL "field-name coupling without a call edge" counts as a dependency at all.** The contract does not define whether serialized-field-name coupling is an edge. Both FAN and POL flag it, neither commits. **If supplied (a coordinator ruling):** would resolve A1, A5 and possibly A3c/A3d as a class rather than one at a time.
- **Whether the coordinator intends to re-merge, or whether the 07:34 catalog is deliberately frozen.** I found no coordination-log entry post-dating the merge. `00-coordination.md` was not read (out of scope). **If supplied:** would downgrade §1.3b from CRITICAL to informational if the freeze is intentional and the temp revisions are being handled separately.
- **Whether explorers 7 and 8 revised anything else after 07:52.** mtimes were sampled once, at validation time. A further save after my read would invalidate §1.3b's diffs.
- **Evidence quality inside Confidence sections.** Explicitly out of scope. I confirmed citations are *present* in all 9; I did not check that any cited line number is real.

# Caveats & Required Follow-ups

**What the coordinator MUST verify before relying on this report:**

1. **This validation is structural only.** I checked the document against itself and against its own temp sources. I did **not** open `experiments/kernel_demo.py`. Every asymmetry in §2.3 is a statement that *the catalog contradicts itself*, never a statement about what the code does. Do not use my asymmetry list as a source of truth about the real dependency graph — use it as a list of places the catalog must be made self-consistent, and ground each fix in the contract-reviewer's source verification.
2. **My adjudications in A1, A2 and A4–A6 ("this side is the wrong one") rest on line-number containment** — the cited line falls inside another subsystem's declared range. Per the Confidence section, the ranges partition 1–4,066 cleanly with only three documented overlaps, none of which touches the citations I relied on, so this is evidence rather than inference. It is still a claim about *what the catalog says about itself*, not about the code: source verification should confirm each before the edit is made. Separately, note the one genuine range overlap I did not resolve — `AGREEMENT_MARGIN` at :3256 is claimed by the ID entry's Key Components while :3256 falls inside CLI's declared range 3063–3264, and PLOT:883 attributes it to CLI.
3. **The Plotting Sidecar entry's factual content is unvalidated by anyone**, per the coordinator's scope limit. Its form conforms; its version anchor is stale and self-contradictory. **The catalog contains one entry analysed against a moving target** — this should be carried forward as a stated limitation into every downstream deliverable, not silently dropped once the version anchor is corrected.
4. **§1.3b's diffs are a snapshot** taken at validation time. Re-run the temp-vs-catalog comparison immediately before re-merging.

**Assumptions this report rests on:**
- The Output Contract in `temp/task-explorers.md:13–38` is the authoritative contract, and "8 sections" counts the `## Name` heading plus the seven `**X:**` blocks.
- The merge cut rule described by the coordinator (cut each temp file after its final `---` following `**Confidence:**`) is the rule actually implemented; I reproduced it to test verbatim presence, and it matched exactly for 6 of 8 files, which corroborates the rule.
- Bidirectionality is expected to be **total** — every Outbound has a mirroring Inbound and vice versa. If the coordinator intends Inbound to be best-effort rather than complete, A3–A6 downgrade to informational; **A1 and A2 remain CRITICAL regardless**, because they are contradictions, not omissions.

**What this report explicitly does NOT account for:**
- Correctness of any Responsibility, Key Component, Pattern, or Concern.
- Whether the 9-name subsystem partition is the right partition.
- Whether Location line ranges are accurate or exhaustively cover the 4,066-line file.
- Whether any cited line number in the catalog exists in the source.

**Recommended next steps, in order:**
1. Re-merge from `temp/` (action 6) — cheapest fix, and it changes no Dependencies text, so it cannot invalidate CHECK 2.
2. Resolve the Plotting version anchor (action 7) — the re-merge does this automatically.
3. Get the contract-reviewer's source verdict on the FAN/STORE/POL/HOST/PLOT edges.
4. Apply actions 1–5 to the Dependencies sections using that verdict.
5. Re-validate (attempt 2 of 2) — CHECK 2 only, since CHECK 1 §1.1 will be unaffected by dependency edits.
6. Only then generate diagrams.
