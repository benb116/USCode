# Process: The Pipeline Step by Step, with Schemas

Companion to `DESIGN.md` (strategy: what sources exist and what the repo should represent)
and `ARCHITECTURE.md` (system shape: stores, memoization, emission). This document walks
the pipeline **stage by stage**, specifying the *output schema of each stage* and grounding
each one in a worked example drawn from this repo's actual data:

- **18 U.S.C. § 1203** (Hostage taking) — its source credit and amendment notes (preserved
  in `Notes/Notes.txt`) are used as the running reconstruction example. The current
  `Code/usc18.xml` text verifiably contains every accumulated amendment, so each example
  below can be checked against data already in this repo.
- **P.L. 117-44** — commit `780bd5c` in this repo's history, whose diff mixes a real
  statutory change, serialization churn, and a text-corruption repair. Each pipeline stage
  below is partly designed to pull those three things apart.
- **The Juneteenth amendment** (from `Notes/BillPatterns.txt`) as the instruction-parsing
  example.
- **`LawNetwork/`** (12,769 short titles, 4,239 act-dates, the citation map) as the seed
  data for the resolver stage.

```
STAGE 0        STAGE 1      STAGE 2      STAGE 3       STAGE 4      STAGE 5/6        STAGE 7/8
bootstrap  →   acquire  →   parse    →   resolve   →   derive   →   reconcile/   →   emit/
(one-time)     artifacts    facts        links         versions     validate         publish
                  ↑                        |                            |
                  └── liveness queue ──────┘                            |
                  └── human patches  ←──── discrepancy work-queue ──────┘
```

Every stage's output is rows in `data/build.sqlite` plus blobs in the CAS
(`ARCHITECTURE.md` schema); the schemas below are shown as JSON/YAML for readability.

---

## Conventions used by every schema

**Law IDs** — adopt the convention already established in `LawNetwork/short.json`:

| Form | Meaning | Example |
|---|---|---|
| `<congress>-<number>` | Public law (1901–present numbering) | `117-58`, `104-132` |
| `<year>:<chapter>` | Session law before P.L. numbering | `1937:432`, `1874:R.S.` |

**Unit IDs** — USLM identifier paths, extended with the layer prefix from `DESIGN.md` §B.0:

| Layer | Example |
|---|---|
| Statute ledger | `/us/stat/117/pl-58` |
| Act compilation | `/us/act/social-security-act/s201` |
| Code section | `/us/usc/t18/s1203` (sub-units: `/us/usc/t18/s1203/a`) |

**Event IDs** — integers ordered by the canonical timeline (enactment order; editorial and
delayed-execution events interleaved at their real-world date, per `DESIGN.md` §B.3).

**Hashes** — `sha256:` prefixed; text blobs are hashed after canonical serialization
(Stage 7's renderer is the only serializer, used everywhere, so identical text ⇒ identical
hash — this is what makes memoization and dedup work).

---

## Stage 0 — Bootstrap (one-time inventory)

What exists in this repo today, and what state it's in:

| Asset | State | Role going forward |
|---|---|---|
| `Code/*.xml` (56 titles, ~268 MB) | ⚠️ Stripped: **0** `sourceCredit`/`note` elements survive `cleanup.py`; repealed/renumbered stubs deleted | Superseded — re-acquire unstripped release points (the notes are the reconstruction dataset, `DESIGN.md` §A.2) |
| Git history (50 commits, 117th Congress) | Real per-law commits, but diffs mix statutory change with serialization churn (see `780bd5c`) | Regression fixture for Stage 7: the new pipeline must reproduce these laws' *semantic* diffs cleanly |
| `LawNetwork/short.json` (12,769), `dates.json` (4,239), `map.txt`, `g.txt` | Working prototype | Seed data for Stage 3 resolver |
| `Notes/BillPatterns.txt` | Prototype grammar of amendment language | Spec seed for Stage 2's instruction parser |
| `Notes/QuotedBlock.txt` | Mapping of bill-XML tags → USC USLM tags | Spec for Stage 2's quoted-block normalizer |

**Output schema — none.** Stage 0 just determines the initial acquire list.

---

## Stage 1 — Acquire

**Process:** one fetcher per source kind. Each downloaded object is content-hashed, stored
at `data/artifacts/<sha256>`, and recorded in the manifest. Nothing is ever modified;
a better version of the same *logical source* gets a `supersedes` pointer. The fetch order
for historical material comes from the **liveness queue** (Stage 3 feedback): laws in the
ancestry of living law first.

**Output schema — artifact manifest record:**

```yaml
# one row per acquired object
hash:        sha256:9f2c…
logical_id:  release-point/117-58          # what this IS, independent of which copy
kind:        release-point                 # release-point | annual-edition | statute-volume
                                           # | slip-law | bill-xml | comps | metadata
                                           # | transcription | human-patch
provenance:
  url:        https://uscode.house.gov/download/releasepoints/…/xml_uscAll@117-58.zip
  fetched:    2026-07-08T14:02:11Z
  fetcher:    acquire.olrc@3
quality:     gpo-uslm                      # gpo-uslm > wikisource-proofread > llm-ocr > stub
supersedes:  null                          # or hash of the artifact this replaces
```

**Worked examples — one row per source tier (`DESIGN.md` §A.1):**

```yaml
- {logical_id: release-point/117-58,        kind: release-point,  quality: gpo-uslm}
- {logical_id: annual-edition/1996,         kind: annual-edition, quality: gpo-xhtml}
- {logical_id: statute-volume/98,           kind: statute-volume, quality: gpo-uslm}   # 98 Stat. (1984)
- {logical_id: slip-law/104-132,            kind: slip-law,       quality: gpo-text}   # AEDPA
- {logical_id: law/1937:432,                kind: metadata,       quality: stub}       # legisworks YAML only
- {logical_id: patch/t18-s1203-1994-note,   kind: human-patch,    quality: human}      # from patches/
```

---

## Stage 2 — Parse (artifacts → facts)

Each parser is a **pure function** of (artifact, parser version); its output is a fact row
keyed by `derivation_key = hash(inputs ‖ parser_id ‖ parser_version ‖ params)`
(`ARCHITECTURE.md` [2]). Five parsers:

### 2a. Snapshot parser (USC USLM / XHTML → unit tree + snapshot texts)

Walks a release point or annual edition; emits one **unit record** per section and one
**snapshot fact** per (unit, checkpoint). Keeps repealed/omitted/transferred stubs — they
are the breadcrumbs for lineage (unlike the current `cleanup.py`, which deletes them).

```yaml
# unit record
unit_id:    /us/usc/t18/s1203
kind:       section
heading:    Hostage taking
status:     operative                      # operative | repealed | omitted | transferred | reserved

# snapshot fact
fact_kind:  snapshot-text
unit_id:    /us/usc/t18/s1203
checkpoint: release-point/117-58
blob:       sha256:41ab…                   # canonical rendering of the section text
```

### 2b. Source-credit parser (USLM `sourceCredit` → the section's event list)

The credit string for § 1203 (quoted in `Notes/Notes.txt:56`):

> (Added Pub. L. 98–473, title II, §2002(a), Oct. 12, 1984, 98 Stat. 2186; amended
> Pub. L. 100–690, title VII, §7028, Nov. 18, 1988, 102 Stat. 4397; Pub. L. 103–322,
> title VI, §60003(a)(10), Sept. 13, 1994, 108 Stat. 1969; Pub. L. 104–132, title VII,
> §723(a)(1), Apr. 24, 1996, 110 Stat. 1300.)

parses to:

```yaml
fact_kind: credit-chain
unit_id:   /us/usc/t18/s1203
events:
  - {law: 98-473,  law_section: "title II §2002(a)",       date: 1984-10-12, stat: "98 Stat. 2186",  action: added}
  - {law: 100-690, law_section: "title VII §7028",         date: 1988-11-18, stat: "102 Stat. 4397", action: amended}
  - {law: 103-322, law_section: "title VI §60003(a)(10)",  date: 1994-09-13, stat: "108 Stat. 1969", action: amended}
  - {law: 104-132, law_section: "title VII §723(a)(1)",    date: 1996-04-24, stat: "110 Stat. 1300", action: amended}
```

This is the **skeleton of the section's git history** — four commits — extracted from one
modern download with zero OCR. Aggregated over all sections, credit chains also produce
the master **event timeline** and the **liveness queue** (every law cited in any credit).

### 2c. Amendment-note parser (editorial notes → reverse-applicable edit ops)

The three notes for § 1203 (also `Notes/Notes.txt`), parsed into the **edit-op schema** —
the single most important schema in the pipeline, shared by notes (2c) and law text (2d):

```yaml
# EDIT-OP SCHEMA
op:      insert | strike | substitute | redesignate | repeal | general-amend | add-unit | move
target:  <unit_id>                      # resolved by Stage 3 if given as act citation
anchor:  {type: after-text | before-text | at-end | before-period | nth-word, text: "…"}
old:     "…"                            # for strike / substitute
new:     "…"                            # for insert / substitute / add-unit (quoted block)
```

```yaml
# "1996—Subsec. (a). Pub. L. 104–132 inserted 'or conspires' after 'attempts'."
- {law: 104-132, target: /us/usc/t18/s1203/a, op: insert,
   anchor: {type: after-text, text: "attempts"}, new: "or conspires"}

# "1994—Subsec. (a). Pub. L. 103–322 inserted before period at end 'and, if the death of
#  any person results, shall be punished by death or life imprisonment'."
- {law: 103-322, target: /us/usc/t18/s1203/a, op: insert,
   anchor: {type: before-period, position: end},
   new: "and, if the death of any person results, shall be punished by death or life imprisonment"}

# "1988—Subsec. (c). Pub. L. 100–690 substituted '(c) As' for '(C) As'."
- {law: 100-690, target: /us/usc/t18/s1203/c, op: substitute, old: "(C) As", new: "(c) As"}
```

Every op is mechanically **invertible** (insert↔strike, substitute swaps old/new), which is
what makes the backward pass in Stage 4 possible. Ops that aren't invertible
(`general-amend` — "amended section generally") are recorded with `invertible: false`; they
mark exactly where full text of the older version must come from a snapshot or the law
itself. That's the work-queue boundary of `DESIGN.md` §A.6.

### 2d. Law-text parser (slip law / bill XML → forward instructions)

Same edit-op schema, parsed from the amendatory language of the law itself, using the
grammar prototyped in `Notes/BillPatterns.txt`. The example from that file:

> "Section 6103(a) of title 5, United States Code, is amended by inserting after the item
> relating to Memorial Day the following: 'Juneteenth National Independence Day, June 19.'."

```yaml
fact_kind: instruction
law:       117-17
law_provision: s1
target_ref: {kind: usc, cite: "5 USC 6103(a)"}      # unresolved reference, Stage 3 resolves
op: insert
anchor: {type: after-item, text: "Memorial Day"}
new: "Juneteenth National Independence Day, June 19."
quoted_block: false
```

Quoted blocks (new sections set out in full) pass through the **quoted-block normalizer**
(`Notes/QuotedBlock.txt`): bill-DTD tags map to USLM (`<enum>`→`<num>`, `<header>`→
`<heading>`, `<text>`→`<content>`), then to canonical text.

### 2e. Event extractor (metadata → the timeline)

From PLAW/legisworks metadata plus 2b's aggregated credits:

```yaml
event_id:  8231
ordinal:   8231
kind:      enactment          # enactment | editorial | delayed-execution | checkpoint
law:       104-132
enacted:   1996-04-24
stat_cite: 110 Stat. 1214
bill:      S. 735 (104th Congress)
title:     Antiterrorism and Effective Death Penalty Act of 1996
sponsors:  [ {name: "Sen. Bob Dole (R-KS)"} ]
```

---

## Stage 3 — Resolve (references → unit IDs; the link layer)

Amendment language rarely names a clean unit ID; it says "section 3 of the Act of June 25,
1938" or "the Social Security Act". This stage resolves every `target_ref` from Stage 2
into a `unit_id`, using three lookup tables:

**3a. Alias table** — formalizes `LawNetwork/short.json` + `dates.json`, including their
`--SEE--` redirect convention:

```yaml
- {alias: "Antiterrorism and Effective Death Penalty Act of 1996", law: 104-132, source: short.json}
- {alias: "``Kick-Back'' Racket Act", see: "Copeland Anti-Kickback Act"}     # redirect
- {alias: "Act of April 1, 1941", law: "1941:32", source: dates.json}
```

**3b. Classification map** — act section → Code location (from OLRC classification tables
and Table III; the lookup anticipated in `Notes/Notes.txt:14-18`):

```yaml
- {law: 104-132, law_provision: "title VII §723(a)(1)", classified_to: /us/usc/t18/s1203/a,
   classification: amendment}                     # amendment | note | new-section | untouched
```

**3c. Lineage table** — unit identity across renumbering/transfer, so `git mv` (Stage 7)
and `--follow` work:

```yaml
- {unit_id: /us/usc/t34/s10101, predecessor: /us/usc/t42/s3711, moved_by_event: 12744,
   kind: editorial-reclassification}              # Title 34 creation, 2017
```

**Outputs:** every Stage-2 op gets `target` filled in; the **citation graph** (formalizing
`LawNetwork/g.txt`) gets its edges; **liveness scores** are recomputed (distance from
current Code in the citation graph) and fed back to Stage 1's fetch queue.

---

## Stage 4 — Derive (facts → section version chains)

The core computation. Per unit, per the strategy in `DESIGN.md` §A.2–A.3:

```
derive(unit):
  chain = credit-chain(unit)                      # Stage 2b: the event skeleton
  V[latest] = snapshot at newest checkpoint       # ground truth seed
  # backward pass
  for event in reversed(chain):
      op = note-op(unit, event)                   # Stage 2c
      if op.invertible:  V[event-1] = apply(invert(op), V[event])   → derivation: reverse-applied
      else:              V[event-1] = older snapshot or law text     → derivation: from-snapshot / transcribed
  # forward pass (independent witness)
  for event in chain:
      op = instruction(unit, event)               # Stage 2d, where law text is in hand
      F[event] = apply(op, V[event-1])                               → candidate for Stage 5
```

**Output schema — version record** (one row per unit per touching event):

```yaml
unit_id:    /us/usc/t18/s1203/a
event_id:   8231                          # P.L. 104-132
blob:       sha256:41ab…                  # text AFTER this event
derivation: reconciled                    # from-snapshot | forward-applied | reverse-applied
                                          # | reconciled | transcribed | manual-patch
inputs:     [fact:sha256:77e0…, version:(…/s1203/a, 7590)]
confidence: exact                         # exact | proofread | reconstructed | unreconciled
status:     operative
```

**Worked example — the full chain for § 1203(a)**, derived backward from the current text
(verifiable against `Code/usc18.xml`, which contains both later insertions):

| # | After event | Text state (subsection (a), abridged) | Derivation |
|---|---|---|---|
| v4 | 104-132 (1996) | "…or attempts **or conspires** to do so… and, if the death of any person results, shall be punished by death or life imprisonment." | from-snapshot (current) |
| v3 | 103-322 (1994) | v4 minus "or conspires" | reverse-applied (invert 1996 insert) |
| v2 | 100-690 (1988) | v3 minus the death-penalty clause | reverse-applied (invert 1994 insert) |
| v1 | 98-473 (1984) | v2 (the 1988 op touched only subsec. (c)) | reverse-applied (no-op for (a)) |
| v0 | — | *(unit does not exist before 98-473)* | — |

Five version rows, four with no OCR involved. When the slip-law text of 98-473 §2002(a) is
acquired (Stage 1, liveness queue), its quoted new-section text gives an independent
**forward** witness for v1 — which Stage 5 compares against this backward-derived v1.

---

## Stage 5 — Reconcile (bracketing)

For every version where both a forward and a backward derivation exist:

- `F[event] == V[event]` → mark `derivation: reconciled`, `confidence: exact`. The two
  witnesses (law text and editorial note) are independent, so agreement is strong evidence.
- Mismatch → emit a **discrepancy record** (the human work-queue):

```yaml
unit_id:     /us/usc/t18/s1203/a
event_id:    7590                         # P.L. 103-322
forward:     sha256:aa10…                 # from AEDPA-era slip law OCR
backward:    sha256:bb27…                 # from reverse-applied 1996 note
diff:        |                            # unified diff of the two candidates, for the human
  -…any term of years or for life and, if the death of any person results,
  +…any term of years or for life, and, if the death of any person results,
suspected:   ocr-comma                    # heuristic triage tag
resolution:  null                         # later: hash of the human-patch artifact
```

A human (or a stronger model pass) resolves it by writing a **patch artifact** — a
first-class input that survives every rebuild (`ARCHITECTURE.md` [1]):

```yaml
# patches/t18-s1203-103-322.yaml
applies_to: {unit_id: /us/usc/t18/s1203/a, event_id: 7590}
verdict:    backward                      # backward | forward | neither (with corrected text)
reason:     "Slip-law OCR inserted a spurious comma; 108 Stat. 1969 image confirms no comma."
checked:    {source: statute-volume/108, page: 1969, by: benb116, date: 2026-07-09}
```

---

## Stage 6 — Validate (checkpoint fidelity)

Replay every unit's chain to each checkpoint date and diff against the actual snapshot
(annual editions 1994+, release points 2013+). **Output schema — fidelity report row:**

```yaml
checkpoint:  annual-edition/1996
title:       18
units_total: 3117
exact:       3081        # reconstructed text byte-identical to snapshot
formatting:  22          # differs only under canonical re-serialization
divergent:   9           # real text mismatch → auto-filed as discrepancies
missing:     5           # unit in snapshot but not derivable (usually general-amend gaps)
fidelity:    0.9886
```

Published with the content repo so users know per-title, per-era, exactly how much to
trust `git blame` (`DESIGN.md` §B.5). Every `divergent` row auto-files a Stage-5
discrepancy.

---

## Stage 7 — Emit (version store → git history)

Walk events in ordinal order; for each event, collect all version rows citing it; render
each affected unit to its file; stream to `git fast-import`.

**Rendered file** (the canonical serialization — the only place text is formatted, which
eliminates the whitespace-churn diffs visible in commit `780bd5c`, where re-wrapped XML
produced diff hunks with zero legal meaning):

```markdown
---
identifier: /us/usc/t18/s1203
status: operative
added-by: 98-473
---
# § 1203. Hostage taking

(a) Except as provided in subsection (b) of this section, whoever, whether inside or
outside the United States, seizes or detains and threatens to kill, to injure, or to
continue to detain another person…
```

**Commit** (one per event; trailers per `DESIGN.md` §B.3):

```
117-44: Surface Transportation Extension Act of 2021

Public-Law: 117-44
Bill: H.R. 5434 (117th Congress)
Enacted: 2021-10-02
Stat: 135 Stat. 382
Change-Type: statutory
```

**fast-import stream fragment** (what the emitter actually writes):

```
commit refs/heads/master
author Congress (104th) <congress@legis.gov> 830332800 -0400
committer uscode-pipeline <build@…> 1783000000 +0000
data 214
104-132: Antiterrorism and Effective Death Penalty Act of 1996
…trailers…
M 100644 :41ab usc/t18/ch55/s1203.md
```

**Emit-cache record** (what makes re-emission incremental):

```yaml
event_id:              8231
cumulative_state_hash: sha256:c9d4…   # hash of every unit's blob as of this event
commit_sha:            e5f2a91…
```

On rebuild: find the first event whose `cumulative_state_hash` changed; reuse every commit
before it verbatim (`fast-import` resumes `from` that commit); re-emit the rest. History
before the change is byte-stable; history after it is rewritten — by construction, not by
surgery.

**Scale check:** the largest recent law in this repo's history, 117-58 (IIJA), touched 22
title files with ~78,000 inserted lines as whole-title XML. Under per-section emission the
same event is one commit touching the ~600 section files it actually amends — a diff a
human can actually read.

---

## Stage 8 — Publish

Force-push (`--force-with-lease`) the content repo; tag; write the build manifest:

```yaml
build_id:         2026-07-08T15:00Z#412
pipeline_version: 0.4.0
inputs:           {artifacts: 9412, patches: 137}
events_emitted:   14730
commits_reused:   14726        # incrementality, made visible
commits_new:      4
first_dirty:      event 14727
fidelity:         {overall: 0.994, report: reports/fidelity-412.json}
tags:             [rp/119-21, build/412]
```

---

## Incrementality summary (what each change costs)

| Change | Dirty set | Stages that run | Emitted |
|---|---|---|---|
| New law enacted | 1 event, its sections | 1,2d,2e,3,4,7,8 | commits appended, none rewritten |
| GPO ships SAL vol. 98 in USLM | facts from vol. 98; chains citing its laws (e.g., § 1203 v1) | 1,2d,4,5,7 | history rewritten from earliest affected event (1984) |
| Note-parser bug fix | all note facts reparse; only *changed* outputs cascade (early cutoff) | 2c,4,5,7 | usually a handful of commits |
| Human patch lands | one (unit, event) version | 4,5,7 | rewritten from that event |
| Renderer tweak | every blob re-serializes | 7 only (derivations untouched) | full re-emit (minutes) |

---

## Suggested build order

1. **2a + 2b on one unstripped title** (Title 18 release point): unit records, snapshots,
   credit chains. Proves acquisition + the event skeleton.
2. **2c + 4 backward pass on § 1203**: reproduce the worked example above mechanically.
3. **7 on the 117th Congress**: re-emit what this repo already has, per-section and
   canonical — the existing 50 commits become the regression fixture.
4. **5 + 6 against the 1994–1996 annual editions**: first fidelity report.
5. Widen: all titles, then backward through eras per the liveness queue.
