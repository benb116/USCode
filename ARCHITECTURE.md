# Architecture: Incremental Build System for Section-Version Derivation

This document describes the **pipeline system** that executes the strategies outlined in
`DESIGN.md`, producing section-version text strings incrementally and redoably, so that:

- Adding one new law or fixing one OCR error does not recompute the entire history.
- Better sources, parser fixes, and human corrections can invalidate and regenerate any
  part — including rewriting the emitted git history.

The core insight: **separate memoized computation from disposable emission**. The version
store is the real product; the git repository is a materialized view you can regenerate
and force-push at will.

---

## The five-component architecture

### [1] Source store (append-only, content-addressed)

Raw artifacts: release-point USLM XML, annual XHTML archives, GPO Statutes at Large XML,
PDFs, OCR output, Wikisource transcriptions, legisworks YAML metadata, human patches.

**Invariants:**
- Each artifact stored as `artifacts/<sha256_of_content>` with a manifest entry:
  - `hash` (SHA256)
  - `kind` (release-point | annual-edition | statute-volume | bill-slip | ocr-text |
    transcription | metadata | human-patch)
  - `provenance` (URL, fetch date, quality tier per DESIGN §A.5: `gpo-uslm` > 
    `wikisource-proofread` > `llm-ocr` > `stub`)
  - `superseded_by` (hash of newer artifact, if available — e.g., when GPO ships XML for a
    volume already OCR'd)
- Never edited; history is immutable append-only ledger.
- Human corrections are **first-class input artifacts** (files in `patches/` checked into
  git): format = YAML + unified-diff hunks, tied by derivation fact to the error they fix.
  This ensures corrections survive rebuilds.

### [2] Fact store (derived, structured)

Parser outputs: amendment instructions, parsed amendment notes, source-credit chains,
snapshot texts, classification maps, the event timeline.

**Invariants:**
- Each fact = `(derivation_key, output_json)` where:
  ```
  derivation_key = hash(
    concat(input_artifact_hashes)
    ‖ parser_id
    ‖ parser_version
    ‖ parser_params
  )
  ```
- Bumping a parser's version invalidates exactly that parser's output, nothing else
  (cleanly scoped recomputation).
- Fact rows include `confidence` (computed vs. human-confirmed) and `discrepancy_id`
  (if reconciliation flagged it).

**Fact kinds:**
- `amendment-instructions` — (law, section_target) → instruction text ("inserted X after
  Y"), parsed from bill XML and SAL legislation.
- `amendment-notes` — (section_id, effective_date) → human-readable note from the Code
  ("1996—Subsec. (a). Pub. L. 104–132 inserted…"), parsed from USLM XML.
- `source-credits` — (section_id) → ordered list of (public_law, statute_citation,
  enactment_date), parsed from `sourceCredit` elements.
- `snapshots` — (title, date, section_id) → text extracted from annual edition or release
  point, at timestamp T.
- `events` — (ordinal, kind, pl_number, dates, metadata) — the legislative timeline.
- `lineage` — (unit_id, moved_by_event, new_path) — records renumbering and transfers so
  section identity survives `git mv`.

### [3] Version store (the core product)

**The row:** `section_version(unit_id, event_id, blob_hash, derivation, confidence, status)`

- `unit_id` — stable identifier surviving renumbering; maintains lineage table.
- `event_id` — the event that produced or modified this version (foreign key to events).
- `blob_hash` — content-addressed reference to the section text (deduplication is free).
- `derivation` ∈ {from-snapshot, forward-applied, reverse-applied, reconciled, transcribed,
  manual-patch} — records *how* the text was obtained and from which input fact.
- `confidence` ∈ {exact, proofread, reconstructed, unreconciled} — drives validation
  (DESIGN §A.3).
- `status` ∈ {operative, repealed, omitted, transferred, reserved} — legal status at that
  event, independent of git commit order (handles delayed/contingent amendments per
  DESIGN §B.3).

**Dependency structure:**
- `version(unit_id, event_n)` depends only on:
  - `version(unit_id, event_{n-1})` (the prior version of this section), AND
  - one instruction/note fact (what changed)
  
  This means **invalidation propagates only along a single unit's event chain**, not
  globally. Fixing 1789 section text doesn't trigger recomputation of 2024 sections.

### [4] Reconciler / validator

Runs the two-sided bracketing strategy (DESIGN §A.3):

1. **Forward pass:** for each section version, try to apply its amendment instruction to
   the prior version → `forward_blob`.
2. **Backward pass:** for each section, reverse-apply the next-later amendment note →
   `backward_blob`.
3. **Compare:** if `forward_blob == backward_blob`, status = `reconciled`. Else emit a
   discrepancy fact (human work-queue).
4. **Checkpoint diff:** for annual editions (1994+) and release points (2013+), compare the
   reconstructed state at date T against the ground-truth snapshot → per-title fidelity
   metrics.
5. **Close the loop:** human resolutions (facts correcting parser bugs or OCR) enter as
   patch artifacts in [1]; next rebuild picks them up.

Output: `discrepancies` table (unit_id, event_id, forward_blob, backward_blob,
resolution_artifact_hash), queryable as a live dashboard.

### [5] Emitter (git materialization)

Walks the event timeline in order; for each event, gathers all section versions citing it;
renders the line-oriented file format (DESIGN §B.2); streams to `git fast-import`.

**Incremental emission cache:** `(event_id, cumulative_state_hash) → commit_sha`

- On rebuild, reuse the commit chain up to the first event whose cumulative state changed.
- Re-emit only events after it. This is cheap (git fast-import runs in minutes even for
  hundreds of thousands of commits) and lets incremental pipeline runs emit incrementally.
- Tag every emission with `pipeline-v<N>` and build ID.
- Output is a separate repo (DESIGN §B.4, build artifact), force-pushed with `--force-if-includes`.

---

## Incremental build algorithm (per run)

```
1. ACQUIRE
   - Fetch new/updated source artifacts (govinfo API, LoC, Wikisource, etc.)
   - Update manifest: new hashes, supersede pointers
   - Apply human patches from patches/ directory

2. PLAN
   - Recompute event timeline fact (memoized)
   - Emit dirty-event list: events whose inputs changed

3. DERIVE (topological walk)
   - Mark derivation nodes dirty iff:
     * Input artifact hash changed (superseded source)
     * Parser version changed
     * Input from dirty fact
   - Recompute dirty facts only; cache unchanged ones

4. RECONCILE / VALIDATE
   - Run bracketing reconciler over versions
   - Diff against checkpoints; emit fidelity report
   - Add discrepancies to work-queue

5. EMIT
   - Find first dirty event
   - Reuse cached commits up to event_{n-1}
   - `git fast-import` only events from n onward
   - Force-push; tag with pipeline version + build ID
```

---

## Invalidation examples (worked through)

### Example 1: New public law enacted

**Event:** Congress signs 118-42 (Infrastructure Act Redux). Acquire step adds the slip-law
XML artifact.

**Propagation:**
- Event timeline fact dirty ⇒ recomputes; new event 14729 added.
- Amendment-instructions parser dirty (new event, new law to parse) ⇒ parses 118-42.
- Only sections 118-42 explicitly amends → their versions computed.
- Cumulative state changes only at event 14729 ⇒ emit cache reuses commits 0..14728,
  re-emits from 14729 onward (one new commit).

**Cost:** O(sections-in-118-42), not O(USC).

### Example 2: GPO ships USLM XML for Statutes at Large volume 40 (1918–1919)

**Event:** Volume 40 XML artifact supersedes older PDF+OCR.

**Propagation:**
- Artifact manifest: supersede pointer updated.
- Facts parsed from volume 40 sources → those fact keys change.
- Sections whose versions derive from those facts (e.g., via reverse-reconstruction from
  amendment notes citing 1919 laws) → dirty.
- Amendment-instructions for laws in vol. 40 recomputed (often producing identical
  instructions ⇒ no cascade).
- Only section chains touching those laws recompute; emit cache finds the earliest affected
  event, reuses prior commits, re-emits after.

**Cost:** O(laws-in-vol-40 × sections-per-law), not O(USC).

### Example 3: Amendment-note parser bug fixed

**Event:** Note parser version bumped; bug fix produces different output for ambiguous
"generally amended" language.

**Propagation:**
- Amendment-notes facts dirty; reparse all notes.
- Most produce identical output ⇒ derivation keys unchanged ⇒ downstream versions unchanged
  ⇒ **early cutoff** (key property of content addressing).
- Only sections where the note's output actually changed → versions dirty.
- If the fix is a true bug, note outputs become *more* useful (higher confidence).
- Emit cache reuses all commits where no version state changed.

**Cost:** O(sections-affected-by-bug-fix), often O(1).

---

## Concrete tech stack (modest, pragmatic)

- **SQLite** (`data/build.sqlite`) — single-file ACID database for manifest, facts,
  versions, events, emit cache, discrepancies. Transactional, queryable, zero ops. Schema
  at end of doc.
- **Content-addressed blob store** (`data/blobs/<sha256_prefix>/`) — or use bare git
  objects (`data/.git/objects/`) since git's loose-object model is exactly a CAS.
- **Python pipeline** — fits the existing `cleanup.py`, `billParser.py`, `LawNetwork/`
  heritage. Organized: `pipeline/acquire/ → parse/ → derive/ → reconcile/ → emit/`.
- **`git fast-import`** — built for generating histories. Full re-emit of 100k+ commits is
  minutes, so worst-case rebuild is acceptable. Streaming input means bounded memory.
- **Separate repos** per DESIGN §B.4: this repo is the *tooling repo* (pipeline code,
  human patches, docs); generated content is a separate *content repo* (versioned,
  force-pushable, no hand-edits).

---

## Directory layout (gitignore-guarded)

```
USCode/
├── DESIGN.md              # Strategies and representation
├── ARCHITECTURE.md        # This file
├── pipeline/
│   ├── __main__.py        # Entry point: run() orchestrates all five phases
│   ├── acquire.py
│   ├── parse.py
│   ├── derive.py
│   ├── reconcile.py
│   ├── emit.py
│   └── db.py              # SQLite schema + transaction helpers
├── patches/               # Human corrections (checked in)
│   └── *.yaml             # Format: artifact_hash, derivation_key, hunk diffs
├── data/                  # gitignored; accumulates build artifacts
│   ├── artifacts/         # Downloaded sources by SHA256
│   ├── blobs/             # Section text CAS
│   └── build.sqlite       # Manifest, facts, versions, events, emit cache
├── out/                   # gitignored; content repo lives here
│   └── uscode-history/    # Generated: stat/, acts/, usc/ + .git (force-pushable)
└── ...
```

---

## SQLite schema sketch

```sql
CREATE TABLE artifacts (
  hash TEXT PRIMARY KEY,           -- SHA256
  kind TEXT,                       -- release-point | annual-edition | ...
  provenance_url TEXT,
  fetch_date TEXT,
  quality TEXT,                    -- gpo-uslm | wikisource-proofread | llm-ocr | stub
  superseded_by TEXT REFERENCES artifacts(hash)
);

CREATE TABLE facts (
  derivation_key TEXT PRIMARY KEY, -- hash(inputs ‖ parser_id ‖ version ‖ params)
  parser_id TEXT,
  parser_version TEXT,
  input_artifact_hashes TEXT,      -- JSON array
  input_fact_keys TEXT,            -- JSON array
  output_json TEXT,                -- parser-specific; deserialized on use
  confidence TEXT                  -- computed | human-confirmed
);

CREATE TABLE units (
  unit_id TEXT PRIMARY KEY,        -- /us/usc/t18/s1203 or /us/stat/117/pl-58
  kind TEXT,                       -- section | law
  lineage_parent TEXT REFERENCES units(unit_id),  -- if moved
  moved_by_event INT REFERENCES events(event_id)
);

CREATE TABLE versions (
  unit_id TEXT,
  event_id INT,
  blob_hash TEXT,                  -- reference to data/blobs/
  derivation TEXT,                 -- from-snapshot | forward-applied | ...
  derivation_fact_key TEXT REFERENCES facts(derivation_key),
  confidence TEXT,                 -- exact | proofread | reconstructed | ...
  status TEXT,                     -- operative | repealed | ...
  PRIMARY KEY (unit_id, event_id),
  FOREIGN KEY (unit_id) REFERENCES units(unit_id),
  FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE TABLE events (
  event_id INT PRIMARY KEY,
  ordinal INT,                     -- chronological order
  kind TEXT,                       -- enactment | amendment | reclassification | ...
  pl_number TEXT,                  -- 117-58
  enacted_date TEXT,               -- ISO 8601
  effective_date TEXT,             -- may differ from enacted_date
  metadata TEXT                    -- JSON (title, bill, sponsors, etc.)
);

CREATE TABLE discrepancies (
  unit_id TEXT,
  event_id INT,
  forward_blob TEXT,               -- result of forward-applying amendment
  backward_blob TEXT,              -- result of reverse-applying next note
  resolution_artifact_hash TEXT REFERENCES artifacts(hash),
  PRIMARY KEY (unit_id, event_id),
  FOREIGN KEY (unit_id, event_id) REFERENCES versions(unit_id, event_id)
);

CREATE TABLE emit_cache (
  event_id INT PRIMARY KEY,
  cumulative_state_hash TEXT,      -- hash of all section states up to this event
  commit_sha TEXT,                 -- the corresponding git commit
  FOREIGN KEY (event_id) REFERENCES events(event_id)
);
```

---

## How this composes with DESIGN.md's phased roadmap

- **Phase 1 (preserve notes):** Acquire step skips `sourceCredit`/`note` deletion; store as
  artifact metadata or fact JSON.
- **Phase 2 (per-section split):** Emit step renders `versions` rows into per-section
  files; `git mv` tracks lineage.
- **Phase 3 (1994→2013 validation):** Annual-edition snapshots in artifact store; reconcile
  phase diffs against them; fidelity metrics per title.
- **Phase 4 (historical):** Acquire expands to GPO SAL XML volumes, legisworks PDFs, LLM
  transcription. Version store grows backwards. Emit re-runs.

---

## Properties this architecture enables

1. **Incremental:** new law → O(sections-in-law) work; GPO XML volume → O(laws-in-volume ×
   sections-per-law) work; parser fix → O(sections-affected) work.
2. **Redoable:** any derivation can be invalidated; discrepancies are work-queue, not
   hidden. Human patches are versioned.
3. **Auditable:** every version cell shows derivation (where did this text come from?),
   confidence (how much to trust it?), and lineage (is it the same section or a renamed
   one?).
4. **Reproducible:** `pipeline(artifacts, patches) = version_store = git repo`. No
   hand-editing; all state is data.
5. **Resilient to source changes:** better sources don't corrupt history, they improve it
   (via supersede pointers and regeneration).

---

## Next steps (not part of this change)

1. Implement scaffolding: `pipeline/__main__.py` entry point, `db.py` schema + helpers,
   `emit.py` streaming interface.
2. Implement `parse/amendment_notes.py` (reverse-reconstruction from notes per DESIGN §A.2).
3. Implement `derive/` forward-apply + backward-apply reconciler.
4. Wire acquire → emit on a test subset (e.g., 118th Congress, one section).
