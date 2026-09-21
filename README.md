# fidelity-repair

A [Claude Code / Hermes](https://claude-code.nousresearch.com/docs) skill that repairs a **rewritten** version of a text so it says exactly what the **original** says, while keeping the rewrite's own wording as close to verbatim as possible.

```
repair(ORIGINAL, REWRITE) -> CORRECTED
```

Useful whenever you have two versions of the same text — a paraphrase, a translation or back-translation, an editor's or friend's pass, a "simplified" version — and the rewrite drifted from the original's meaning: reverted claims, changed names/titles/quotations/numbers/citations, or imprecise terminology swapped in for terms of art.

- **ORIGINAL** decides what the text *means*.
- **REWRITE** decides how the text is *worded* — it's the base, and everything in it that's already faithful stays untouched, however flat or awkward.
- **CORRECTED** is the rewrite plus the smallest possible set of edits needed to make it say what the original says.

Edit budget, cheapest first: **cuts > insertions >>> rewordings.** This is repair, not rewriting or polishing — see "What this skill does not do" in [SKILL.md](SKILL.md).

## Why this is useful for humanization

A very common reason people reach for a paraphrase/rewrite tool is to make AI-drafted or stiff text read more naturally — but every such rewrite risks quietly changing what the text *says*: dropped hedges, swapped terms of art, altered numbers, mangled quotations. This skill is the fidelity-repair step that comes after that rewrite: it diffs the rewrite against the true original and surgically restores meaning with the minimum possible edit footprint, so the humanized voice survives untouched wherever it was already accurate. It explicitly refuses to "tune" text for AI detectors — it only restores fidelity — which is what actually protects an author (see the skill's stance on this).

## What's in this repo

- `SKILL.md` — the full skill: contract, edit taxonomy (cut/insert/substitute/reword), the meaning-vs-style test table, worked examples, the CriticMarkup procedure, and reporting format.
- `scripts/build_outputs.py` — builds the corrected text and a change log from a CriticMarkup-annotated source file, and runs verbatim/fidelity/banned-term/required-term checks.

## Usage

This is written as an [Agent Skill](https://docs.anthropic.com/en/docs/claude-code) (Claude Code / Hermes format — a `SKILL.md` with YAML frontmatter describing when to trigger it). Drop the `rewrite-fidelity-repair/` directory into your skills folder, or point an agent at this repo.

Manual use of the build script:

```bash
python scripts/build_outputs.py source.txt --name <slug> \
    --rewrite rewrite.txt --original original.txt \
    --ban-file banned.txt --require-file required.txt \
    [--count-from "## Introduction" --count-to "## Works Cited"] [--allow-em-dash]
```

See [SKILL.md](SKILL.md) for the full procedure: pinning down inputs, diagnosing before editing, marking up the rewrite in CriticMarkup, building/checking, and the report format.

## License

MIT
