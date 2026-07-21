# QMD Upstream Investigation — 2026-07-20

**Source:** /design run `10d616f8` (PR-3, secondary track).
**Time spent:** ~15 minutes (PyPI metadata inspection + GitHub fetch).
**Outcome:** Upstream identified; upstream has been rewritten with a different API; filing issues against 0.1.1 bugs is not useful.

## Concrete checks performed (per design §2.4)

### Check 1: PyPI wheel `METADATA` and `RECORD`

Wheel: `qmd-0.1.1-py3-none-any.whl` (74,541 bytes), downloaded via `pip download qmd==0.1.1 --no-deps`.

`METADATA` fields of interest:

- `Name: qmd`
- `Version: 0.1.1`
- `Author: Chengzhang Yu`
- `Project-URL: Homepage, https://github.com/chengzhag/qmd-py`
- `Project-URL: Repository, https://github.com/chengzhag/qmd-py`
- `Project-URL: Issues, https://github.com/chengzhag/qmd-py/issues`

`chengzhag` is a near-match for the author's name `Chengzhang Yu` (likely a typo or alternate romanization in the GitHub handle). However, `https://github.com/chengzhag/qmd-py` returns HTTP 404 as of 2026-07-20. Either the user was renamed, deleted, or the handle was a typo at publish time.

The README inside the wheel's METADATA tells a different story:

```markdown
## Development

git clone https://github.com/iomgaa-ycz/qmd-py.git
cd qmd-py
pip install "qmd[mvp,mcp,dev]"
pytest tests/ -v
```

So the README in the published wheel points to a different repository (`iomgaa-ycz`) than the `Project-URL` field (`chengzhag`). This is inconsistent metadata — the publish was made with a wrong/dated Project-URL but the README was updated to point at the real repo.

### Check 2: Source-distribution git URL hints

Source distribution (`*.tar.gz`) was not downloaded separately — the wheel's METADATA README already contained the `iomgaa-ycz/qmd-py` URL, which is the canonical source pointer.

### Check 3: Web fetch of `iomgaa-ycz/qmd-py`

Repository exists and is publicly accessible. **111 commits.** MIT licensed. `pypi.org/project/qmd/` linked from the repo's "About" section, confirming this is the canonical source for the published package.

**However:** the upstream repository has been **completely rewritten** since 0.1.1 was published. The current `main` branch describes a different API:

- **0.1.1 (installed):** CLI-first. `qmd add`, `qmd search`, `qmd query`, `qmd embed`, `qmd update`. Default embedding via `sentence-transformers` (originally `paraphrase-multilingual-MiniLM-L12-v2`, patched locally to `all-mpnet-base-v2`).
- **Current upstream:** Python-API-first. `from qmd import connect`, `client.collection("notes")`, `col.add_document()`, `col.hybrid_search(top_k=5, rerank=True)`. Default embedding is `Qwen3-Embedding-0.6B` (1024-dim). Reranker is `Qwen3-Reranker-0.6B`.

The CLI command shape, the embedding default model, the reranker backend, and the import surface (`qmd.connect` vs `qmd.create_store` / `qmd.search`) are all different. The original 0.1.1 API (`qmd.create_store`, `qmd.search`, `qmd.create_llm_backend`, `SentenceTransformerBackend`) appears to no longer exist on `main`.

## Implications

### For PR-3's stated goal

The design's PR-3 description said: *"file two issues (patch 1 + patch 2) on the upstream repo."* **This is no longer useful.** The bugs patches 1 and 2 fix live in code that has been rewritten on upstream `main`. The upstream maintainer would respond with "fixed in rewrite" or "won't fix — 0.1.1 is abandoned." Filing the issues adds noise without value.

### For the design's §13 Upgrade Playbook

The "upgrade to 0.2.0" workflow in §13 is more accurately described as a **migration to a new API**, not a version bump:

- The CLI commands change shape (`qmd search` → `python -m qmd search` with different args)
- The default models change (`all-mpnet-base-v2` → `Qwen3-Embedding-0.6B`)
- The DB schema likely changes (different vector dimensions: 768 vs 1024)
- All 6 workspace call sites (`wiki_after_write.py`, `wiki_ingest.py`, `wiki_search.py`, `wiki_contradiction_scan.py`, `wiki_signal_dispatch.py`, `qmd_update_wrapper.ps1`) would need migration

The design's §13.0 default ("stay on 0.1.1, do nothing") is strongly reinforced by this finding.

### For the critical friend's R2 follow-up

The inline critical friend (see `grok-design-critique-10d616f8.md`) flagged that the design has no exit ramp if upstream is dead. This investigation refines the picture: **upstream is not dead — it's divergent.** It's actively maintained (111 commits, public) but on a different trajectory than 0.1.1. The "exit ramp" should explicitly cover "upstream exists but is a different API" — which is materially different from "upstream is dead."

A future evaluation that considers migration to current upstream should weigh:

- **Cost:** rewriting all 6 workspace call sites; rebuilding the DB with new embeddings; learning the new Python-API-first interface.
- **Benefit:** Qwen3-Embedding-0.6B may be materially stronger than `all-mpnet-base-v2` (different model class, larger); access to upstream bug fixes; no more `.patch` maintenance.
- **Trigger criteria:** R2 follow-up suggests "if upstream remains unreachable for M months." Given upstream IS reachable, the trigger should instead be "if patch set grows to N+1 sites" or "if a new model would deliver materially better retrieval quality."

## Recommendation

1. **Do NOT file issues against `iomgaa-ycz/qmd-py` for the 0.1.1 bugs.** They are not actionable upstream.
2. **Update the wiki concept** `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md` to reflect that upstream is divergent (not dead). Currently the concept says "upstream is unreachable"; this is partially incorrect — the *publish URL* is unreachable but the *actual repo* is publicly accessible.
3. **Defer migration evaluation** to a separate session. The current Option I (extend patch convention) remains the right answer for the immediate durability question.
4. **Refine the §13 Upgrade Playbook** (R2 follow-up) to distinguish three scenarios: (a) upstream publishes a 0.1.x bugfix — apply; (b) upstream publishes 0.2.0 with new API — migrate with cost; (c) upstream never publishes again — Option I holds indefinitely.

## Files

- Wheel extracted at: `P:/tmp/qmd-clean-20260720-221502/` (will be reaped by temp cleanup)
- PyPI: <https://pypi.org/project/qmd/>
- Upstream repo (current main): <https://github.com/iomgaa-ycz/qmd-py>
- Stale Project-URL (404): <https://github.com/chengzhag/qmd-py>
- Original inspiration (not a Python port): <https://github.com/tobi/qmd>
