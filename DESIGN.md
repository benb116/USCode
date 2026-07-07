# Design: Version-Controlling the Law of the United States

This document works through two foundational questions for this project:

- **[Part A](#part-a-getting-historical-law-text):** How do we get the text of laws, in raw
  machine-readable form, going as far back as possible — so that version control has real
  history to show?
- **[Part B](#part-b-representing-the-code-in-version-control):** What is the most useful
  *and faithful* representation of the US Code in a repository, given that the Code is a
  complex, editorially-maintained artifact that changes shape over time?

It builds on the ideas already sketched in `Notes/Notes.txt` and `Notes/Steps.txt`
(the "Statutes at Large folder," the "backtrack from current release point" plan, bills as
branches, sponsors as co-authors) and on the existing pipeline (OLRC release points →
`cleanup.py` → one commit per public law, currently covering the 117th Congress).

---

## Part A: Getting historical law text

### A.0 The headline finding: the PDF problem is being solved upstream

The Government Publishing Office is in the middle of a multi-year project to publish the
**entire Statutes at Large — volume 1 (1789) through volume 116 (2002) — in USLM XML** on
govinfo, the same schema family used for the current US Code and recent public laws.

- Project overview: https://www.govinfo.gov/help/statute and
  https://www.govinfo.gov/features/beta-uslm-xml
- Releases are incremental: volumes 94–104 and 106 shipped September 2025; volumes 19–28,
  36, and 64–79 shipped March 2026 (https://www.govinfo.gov/features/march-2026-release-notes).
- Volumes 65–116 (1951–2002) have long been available as digitized PDF + OCR text in the
  STATUTE collection (https://www.govinfo.gov/app/collection/statute/), with XML arriving
  volume by volume.
- Bulk download: https://www.govinfo.gov/bulkdata/

Two design consequences:

1. **Don't build a permanent OCR pipeline for material GPO will convert anyway.** Build a
   *stopgap* pipeline whose outputs are cleanly replaceable (see A.5 on provenance tiers).
2. **Design the repo as a reproducible build artifact** (Part B), because source text will
   improve over time and the history will need to be regenerated, not hand-patched.

### A.1 Source inventory by era

Best-available source for each period, from newest to oldest:

| Era | Source | Format / granularity |
|---|---|---|
| 2013 → now | OLRC release points, back to P.L. 113-21 (https://uscode.house.gov/download/download.shtml) | USLM XML, full Code snapshot after (nearly) every law — **already in use here** |
| 1995 → now | govinfo PLAW collection (public/private slip laws, 104th Congress+) | Text + PDF; USLM XML for recent Congresses |
| 2003 → now | govinfo BILLS collection (108th Congress+), incl. enrolled bills | Bill-DTD XML (note: bill XML ≠ USC USLM — see `Notes/Notes.txt`) |
| 1994 → 2013 | OLRC annual historical archive (https://uscode.house.gov/download/annualhistoricalarchives/downloadxhtml.shtml) | Full Code, one snapshot per year, XHTML |
| 1951 → 2002 | govinfo STATUTE collection, vols 65–116 | PDF + OCR text; USLM XML rolling out |
| 1789 → 1951 | GPO/Library of Congress digitization of vols 1–64 (https://www.loc.gov/collections/united-states-statutes-at-large/) | Page-image PDF, volume-level; USLM XML conversion planned/partial |
| 1789 → 1951 | **legisworks-historical-statutes** (https://github.com/unitedstates/legisworks-historical-statutes) | ~32,000 statutes: **per-statute** PDFs + YAML metadata (citation, page, topic, title) for every law through vol 64 |
| 1789 → 1875 | Century of Lawmaking (https://memory.loc.gov / LoC digital collections), vols 1–18 | Page images |
| 1873/1878 | Revised Statutes of the United States — the first official codification, and legally the *root commit* for much of today's positive law | Scans (LoC, HathiTrust, Internet Archive) |
| Selected acts | govinfo COMPS "Statute Compilations" (https://www.govinfo.gov/app/collection/comps/) | ~2,500 freestanding acts **as amended**, USLM XML — already scraped by `LawNetwork/reader.py` |
| Crowdsourced | Wikisource Statutes at Large transcription project (https://en.wikisource.org/wiki/United_States_Statutes_at_Large) | Human-proofread text, partial coverage |
| Checkpoints | US Code editions: 1926, 1934 + supplements, every 6 years thereafter (HeinOnline, HathiTrust, Internet Archive scans); 1994+ machine-readable | Validation anchors, not primary sources |

### A.2 Strategy 1 — Reverse-reconstruction: the Code encodes its own history

This is the highest-leverage idea, and it requires **no OCR at all**. It generalizes the
"backtrack from current release point" plan in `Notes/Notes.txt`.

Every section of the current Code carries two machine-parseable historical records:

1. **Source credit** — the full citation chain of every law that ever touched the section:

   > (Added Pub. L. 98–473, title II, §2002(a), Oct. 12, 1984, 98 Stat. 2186; amended
   > Pub. L. 100–690, title VII, §7028, Nov. 18, 1988, 102 Stat. 4397; …)

2. **Editorial amendment notes** — a per-law description of *what changed*, precise since
   roughly the 1990s:

   > 1996—Subsec. (a). Pub. L. 104–132 inserted "or conspires" after "attempts".

An amendment note is a diff. Running it **backward** ("delete 'or conspires' after
'attempts'") produces the prior version of the section. Applied recursively across every
section, this synthesizes point-in-time snapshots of the whole Code going back decades —
for positive-law titles, all the way back to their enactment (e.g., 1948 for Title 18) —
from a single modern download.

Practical notes:

- Precision degrades with age. Modern notes quote exact strings; older ones say things like
  "amended section generally," which means "full text replacement — go fetch the old text."
  So reverse-reconstruction gets ~80% of section-versions for free and produces an exact
  work-queue of the remainder (see A.4).
- The reconstruction is *validated*, not trusted: every reconstructed year is diffed against
  the corresponding annual-edition checkpoint (A.1). Where they match, confidence is
  mechanical. Where they diverge, either the note parser or the note itself is wrong — both
  are worth knowing, and there is a real (small) error rate in the editorial notes.
- ⚠️ **`cleanup.py` currently deletes exactly this data.** `removeTags` includes `note`,
  `notes`, and `sourceCredit`, and sections with `repealed`/`omitted`/`transferred` status
  are dropped entirely. That is discarding the project's single most valuable dataset — and
  repealed/renumbered stubs are precisely the breadcrumbs needed to follow section identity
  through time. Keep them out of the *diffed text* if desired (Part B moves them to parallel
  files), but never destroy them.

### A.3 Strategy 2 — Two-sided reconciliation ("bracketing")

Every historical section-version can be derived from two independent directions:

- **Forward:** take the text of the amending law (OCR or GPO XML) and execute its
  instructions against the previous version.
- **Backward:** take the next-later known-good version and reverse-apply the amendment note
  (A.2).

When both derivations agree, the version is almost certainly correct even if the OCR was
noisy — OCR errors and note-parsing errors are statistically independent and won't produce
the same wrong answer. When they disagree, a human (or a stronger model) reviews one
specific, small conflict instead of proofreading a volume.

The annual editions act as **keyframes** (in the video-compression sense): ground-truth
full snapshots every year from 1994, every six years before that, with the laws as deltas
between keyframes. Reconstruction never has to survive more than a few years of compounding
error before hitting an anchor it must reconcile with.

### A.4 Strategy 3 — Liveness-prioritized acquisition

Do not transcribe all 32,000 pre-1951 statutes. Most are private laws, one-shot
appropriations, and long-superseded provisions that no living law depends on. Instead, walk
backward from the present:

1. Harvest every citation in the current Code's source credits and notes (plus the COMPS
   compilations). This is the **ancestry of living law** — the only laws whose full text is
   needed to make `git blame` on today's Code resolve all the way down.
2. The `LawNetwork` graph already built in this repo (laws referencing laws) extends the
   frontier: a law matters at depth *n+1* if it amended a law that matters at depth *n*.
3. Everything else enters the repo as a **metadata stub** from the legisworks YAML
   (citation, date, title, link to page image) — present in history, upgradeable to full
   text on demand.

This turns an ocean into a bounded, prioritized backlog: on the order of thousands of laws,
not tens of thousands, with the per-statute PDFs already split and named by legisworks.

### A.5 Strategy 4 — Vision-LLM transcription for the remainder, with provenance tiers

For laws in the priority queue that GPO hasn't yet converted: 2026-era vision models
transcribe 18th/19th-century statute typography (long-s, marginal notes, small-caps section
heads) far better than classical OCR, and can emit lightweight structural markup (section
boundaries, enumeration levels) in the same pass. Validation comes from dual-model
consensus plus the bracketing check in A.3 — a transcription that round-trips through the
amendment chain is correct in every character the law's history actually touches.

Wikisource's proofread volumes are a third independent witness where they exist, and worth
importing outright (public domain).

Because sources will keep improving, **every law file carries provenance metadata**:

```yaml
source: gpo-uslm | wikisource-proofread | llm-ocr | legisworks-stub
source_url: ...
quality: exact | proofread | machine | metadata-only
```

When GPO ships a better volume, the pipeline swaps the source and regenerates history
(Part B makes regeneration cheap). The repo's *content* improves monotonically without
anyone pretending the first OCR pass was gospel.

### A.6 How far back is "as far back as possible"?

Realistically three horizons:

1. **1994 → now: exact.** Machine-readable snapshots + release points + slip-law text.
   Fully mechanical.
2. **~1926 → 1994: reconstructable.** Code editions as keyframes + amendment notes +
   STATUTE-collection text. High fidelity, mechanically validated, with a known and
   shrinking exception list.
3. **1789 → 1926: curatable.** No Code exists yet; the repo's `/stat` layer (Part B) is the
   natural home — an append-only ledger of session laws, populated from GPO XML, Wikisource,
   and LLM transcription in liveness order, with the Revised Statutes of 1874 as the one
   great codification event of the era. Version control here shows *accumulation* (and the
   1874 recodification) rather than in-place amendment, which is historically accurate:
   that's what the law actually was like before the Code.

---

## Part B: Representing the Code in version control

### B.0 The core insight: the Code is a view, not the source of truth

The legal reality this repo must not paper over:

- The **Statutes at Large is the law**. The Code is an editorial *projection* of it,
  maintained by the Office of the Law Revision Counsel (OLRC).
- For the ~27 **positive-law titles**, Congress enacted the projection itself, and it
  *became* the law (the underlying acts were repealed).
- For **non-positive-law titles**, the Code is only *prima facie* evidence; the organic acts
  remain authoritative, and the OLRC's arrangement of them is a subjective, revisable
  editorial choice.
- Some enacted law is **never codified** (appropriations, private laws), or codified only as
  statutory notes.

A repo that contains only `usc*.xml` files silently claims the Code is primary. The faithful
model is **three layers in one repository**, mirroring the actual ontology:

```
/stat/            The Statutes at Large layer — ground truth, append-only
  117/pl-58.md       one file per law, filed on enactment, NEVER subsequently edited
  117/pl-58.yaml     metadata: citations, dates, bill number, sponsors, provenance (A.5)
                     (uncodified law lives here and only here — this formalizes the
                      "Statutes at Large folder" idea from Notes/Notes.txt)

/acts/            The compilation layer — freestanding acts "as amended" (COMPS-style)
  social-security-act/...
                     amended in place as later laws modify them; classification maps
                     (act section → Code location) live alongside as metadata.
                     When Congress enacts a title as positive law, the affected act
                     compilations are repealed/removed here — exactly as in real life.

/usc/             The codification layer — the view
  t18/ch55/s1203.md  one file per SECTION
                     positive-law titles: this file IS the law
                     non-positive titles: a maintained projection of /acts
```

This resolves the question in `Notes/Steps.txt` ("How to include Enactment of code titles
into PL?"): positive-law enactment is a single commit in which a new title's files appear in
`/usc`, the superseded compilations disappear from `/acts`, and the enacting law is filed in
`/stat` — a `git mv`/rewrite whose diff *is* the recodification.

### B.1 One file per section, not per title

The section is the atomic unit of amendment — laws say "Section 1203 of title 18 is
amended…". Per-section files mean:

- `git log --follow usc/t18/ch55/s1203.md` = the complete legislative history of one section;
- `git blame` = "which Congress wrote this clause?";
- diffs of a public-law commit touch only the sections it actually amended;
- renumbering/transfer = `git mv` (history follows), instead of an opaque churn inside a
  3 MB blob.

The current layout (title-sized XML, `Code/usc42.xml` alone being tens of MB) makes every
diff unreadable and every commit rewrite a huge blob. Both production-grade precedents —
DC's official code (DCCouncil/law-xml) and France's Archéo-Lex — use fine-grained files for
exactly this reason. A few hundred thousand small files is well within git's comfort zone
(the Linux kernel is ~80k files; git handles far more).

### B.2 A line-oriented text format as the *diffed* representation

USLM XML is the right interchange format (it's what OLRC and GPO publish, and what the
pipeline should parse), but XML is a poor *diff surface*: attribute noise, one-line
elements, pretty-printer churn. Since human-meaningful diffs are the entire point of this
project, the repo should store a **deterministic, line-oriented rendering** derived from
USLM:

```markdown
---
identifier: /us/usc/t18/s1203
status: operative
enacted-by: 98-473
---
# § 1203. Hostage taking

(a) …whoever, whether inside or outside the United States, seizes or detains and
threatens to kill, to injure, or to continue to detain another person…

  (1) …
```

Rules: one addressable unit (subsection/paragraph/clause) per line-block; indentation
mirrors depth; stable, canonical serialization (same input ⇒ byte-identical output — the
current `toprettyxml()` in `cleanup.py` does not guarantee this). Archéo-Lex and
nickvido/us-code both converged on Markdown-with-frontmatter for the same reason.

**Notes and source credits are moved, not deleted** — to parallel files
(`s1203.notes.md`), keeping the main diff surface clean while preserving them, because
(1) statutory notes are law, and (2) source credits are the reconstruction dataset (A.2).

### B.3 Commit semantics — the "faithful history" rules

**One commit per public law** on the main timeline (as this repo already does), enriched:

```
117-58: Infrastructure Investment and Jobs Act

<full official title>

Public-Law: 117-58
Bill: H.R. 3684 (117th Congress)
Enacted: 2021-11-15
Stat: 135 Stat. 429
Co-authored-by: Rep. Peter DeFazio (D-OR) <...>
```

- **Author date = enactment date** (git's author/committer date split exists for exactly
  this: author date = when the change was "written" i.e. enacted; committer date = when the
  pipeline built it). `git log` then reads as a legislative timeline.
- **Two author identities.** Statutory changes are authored by `Congress (117th)`;
  classification, editorial reclassification, renumbering in non-positive titles,
  typo corrections, and recodification mechanics are authored by
  `Office of the Law Revision Counsel` with a `Change-Type: editorial` trailer. This makes
  the *subjectivity of codification itself* a visible, filterable stream:
  `git log --author=OLRC -- usc/t42/` shows every judgment call the editors made about
  Title 42. This is the direct answer to "the US code is collected by people through
  subjective processes" — don't hide the subjectivity; give it its own author.
  (It also implements the note in `Notes/Notes.txt` about squashing classification commits:
  don't squash them — label them.)
- **Tags** at every OLRC release point (`rp/117-58`) and annual edition (`ed/1994`), so
  "the Code as of date X" is `git checkout`, and validation against checkpoints (A.3) is
  `git diff ed/1994 <reconstructed>`.
- **Effective date ≠ enactment date.** Git has one timeline; the law has many (delayed
  effectiveness, contingent amendments, retroactivity — see the P.L. 117-44 / 117-52
  self-reverting example preserved in `Notes/Notes.txt`). Canonical ordering is by
  **enactment**; a delayed or contingent amendment is committed *when it executes*, with a
  trailer citing the authorizing law (`Executes: 117-44 §201(d)`). "What text was in force
  on date X" is therefore a *query over frontmatter status fields*, not a position in git
  history — encoding in-force-ness positionally is what produces unrepresentable states
  like the 117-44 revert.
- **Bills as branches** (the idea in `Notes/Notes.txt:31-43`) remains a good *overlay*, with
  one amendment: create branches retroactively for **enacted** bills only (branch from the
  pre-enactment commit, commits per chamber action, merge = presidential signature), rather
  than a live branch per introduced bill — Congress introduces ~15,000 bills per cycle and
  enacts ~2–3% of them; the dead branches would drown the repo. Live tracking of pending
  bills fits better as a separate staging repo/fork.

### B.4 The repo is a build artifact

The content repo should be **generated deterministically** by a pipeline from the source
layers (`/stat` texts + amendment instructions + classification data), for three reasons:

1. **Source text improves** (A.5): when GPO ships volume 40 in XML, regenerate; the
   simulated history gets better without hand-surgery on old commits.
2. **Parser bugs are inevitable**: a bug fix means re-run, not archaeology.
3. **Trust**: anyone can audit `pipeline(sources) == repo` instead of trusting accumulated
   manual edits.

Practical split: **tooling repo** (scrapers, parsers, generator — the code currently at the
root here: `cleanup.py`, `billParser.py`, `LawNetwork/`) and **content repo** (the generated
`/stat`, `/acts`, `/usc` history). Force-pushing a regenerated content repo is acceptable
precisely because it is a build artifact; tags mark generator versions.

For the pipeline architecture that makes this reproducible and incremental, see
`ARCHITECTURE.md`.

### B.5 Validation

The pipeline is correct when it can reproduce known ground truth:

- Reconstruct 1994→2013 year by year (from annual XHTML + slip laws) and diff each year
  against the next annual edition: divergence report per title.
- Replay 2013→now from release points (mechanical; this is the segment the repo already
  covers for Congress 117 — those commits become the regression test for the newest
  pipeline stage).
- For pre-1994, every reconstructed keyframe (A.3) is scored against the scanned edition
  via fuzzy match; per-title fidelity metrics are published in the repo so users know
  exactly how much to trust `git blame` in each era.

### B.6 Prior art worth studying (and stealing from)

| Project | What it proves / what to take |
|---|---|
| **DCCouncil/law-xml** + Open Law Library (https://github.com/DCCouncil/law-xml) | A US jurisdiction officially maintains its code in git: one commit per law, XML, public PRs. The closest existing system to this project's end-state; study their act→codification tooling. |
| **Archéo-Lex** (https://github.com/Legilibre/Archeo-Lex) | French codes as git: Markdown, one file per article, one commit per consolidated version, author = "Législateur". Validates B.1/B.2 at national scale. |
| **legislation.gov.uk** | The most mature point-in-time legislation system anywhere. Its key abstraction — a database of "effects" (amendment instructions) applied to base texts — is exactly the `/stat` + instructions → view architecture of B.0/B.4. |
| **publicdocs/uscode**, **nickvido/us-code** (https://github.com/publicdocs/uscode, https://github.com/nickvido/us-code) | Release-point-per-commit US Code repos from 2013+. Proves the easy segment is solved; this project's differentiators are the pre-2013 history and the three-layer ontology. |
| **govinfo COMPS** | The federal government already maintains act-level "as amended" compilations — `/acts` is not an invention, it's an adoption. |
| **unitedstates/legisworks-historical-statutes** | The per-statute index of everything 1789–1951; the skeleton of `/stat`. |

### B.7 Phased roadmap

1. **Stop the bleeding:** change the ingest step to *preserve* source credits, notes, and
   repealed/renumbered stubs (parallel files), and make serialization deterministic.
   (`cleanup.py`: `removeTags` / `removeStatus` behavior.)
2. **Re-platform the layout:** per-section files + line-oriented format + `/stat` layer;
   regenerate the existing 117th-Congress history in the new shape (the current repo
   becomes the regression fixture).
3. **Prove reconstruction on known ground:** run source-credit/amendment-note
   reverse-reconstruction from a current release point back to 2013, and validate against
   actual release points; then extend to 1994 against annual editions.
4. **Go historical:** ingest GPO's Statutes at Large USLM volumes as they ship + legisworks
   stubs for everything; run the liveness queue (A.4) and bracketed transcription (A.3/A.5)
   for the pre-conversion remainder; add `/acts` from COMPS.
5. **Overlays:** retroactive bill branches, sponsors as co-authors, effective-date status
   queries, and the browse frontend from `Notes/Notes.txt`.

---

## Summary

**(a)** The raw-text problem is smaller than it looks and shrinking: exact sources cover
1994→now today; GPO is converting all of 1789–2002 to XML on a rolling basis; and the
Code's own source credits + amendment notes let most of the 20th century be *reconstructed
and cross-validated* rather than transcribed. What remains is a bounded, liveness-ordered
transcription queue over legisworks' per-statute PDFs, with provenance tiers so every text
upgrades gracefully.

**(b)** Represent the law as it actually is: an append-only statute ledger (`/stat`),
act-level compilations (`/acts`), and the Code as an explicitly-derived view (`/usc`) —
per-section files in a deterministic line-oriented format, one commit per public law
authored by "Congress" at enactment date, editorial judgment calls authored by "OLRC" so
codification's subjectivity is visible instead of hidden, tags at every checkpoint, and the
whole history generated reproducibly so it can be rebuilt as sources and parsers improve.
