---
name: rewrite-fidelity-repair
description: Repair a rewritten version of a text so it says exactly what the original says, while keeping the rewrite's own wording as close to verbatim as possible. Use this whenever the user supplies two versions of the same text, says which one is the ORIGINAL (the source of truth for meaning) and which is the REWRITE (the base text to keep), and wants the rewrite fixed, e.g. a paraphrase, a translation or back-translation, a friend's or editor's pass, or a simplified version that reverted claims, changed names, titles, quotations, numbers or citations, or used imprecise terminology. Trigger on phrasing like "fix the rewrite so it says the same as my original", "keep it verbatim", "minimal edits", "cuts over insertions over rewordings", "bold what you changed", "give me the full text back", even when the user does not name this skill. Not for proofreading a single text, and not for free rewriting or polishing.
---

# Rewrite fidelity repair

## The contract

```
repair(ORIGINAL, REWRITE) -> CORRECTED
```

- ORIGINAL decides what the text **means**: claims, names, titles, quotations, numbers, citations, terminology.
- REWRITE decides how the text is **worded**. It is the base. Everything in it that is faithful to ORIGINAL stays exactly as it is, including wording that is flat, awkward, or weaker than the original's.
- CORRECTED is REWRITE plus the smallest set of edits after which it says what ORIGINAL says.

Edit budget, cheapest first: **cuts > insertions >>> rewordings**.

The user has chosen the rewrite's wording on purpose (someone else's voice, a translation they have to keep, a version a collaborator already approved). Every word you add is a word that came from neither text unless you take it from ORIGINAL. So this is repair, not improvement. If the user has not said which text is which, ask before doing anything; guessing wrong inverts the whole job.

## The four edit types

1. **Cut.** Remove words from the rewrite. Nothing new enters the text. Use for duplicated blocks, claims or evaluations ORIGINAL never makes, intensifiers and hedges that change the strength of a claim, scare quotes, and filler that changes the claim ("creates a sense of powerlessness" when ORIGINAL argues for powerlessness itself).
2. **Insert.** Add words and leave the rewrite's words untouched. Use for dropped negations, hedges, qualifiers and attributions, and for sentences or steps the rewrite omitted. Take the inserted words from ORIGINAL verbatim.
3. **Substitute.** A cut and an insertion on one span. It is the only possible fix when a specific word or phrase is wrong: a name, a title, a number, a citation, a term of art, a reversed relation. Make the span as small as the error and use ORIGINAL's exact words as the replacement. When the rewrite came from translation or paraphrase, this will be the most common edit by far; the budget still applies, because it tells you to stop at the smallest span.
4. **Reword.** Changing wording that is already faithful. Do not do it. A sentence that says what ORIGINAL says is finished, however much better ORIGINAL phrased it. If you feel the pull to improve one, mention it in the report instead.

When two fixes repair the same error, take the one higher on the list. When a sentence is too garbled for span fixes, keep every run of rewrite words that still works and substitute the rest from ORIGINAL. Replacing a whole sentence is the last resort.

**Quotations sit outside the budget.** A quotation in CORRECTED must match ORIGINAL character for character: slashes, line-break marks, capitals, brackets, ellipses. If the rewrite altered any part of one, restore the entire quotation whatever it costs in edits. A paraphrase that still carries quotation marks and a page number reads as fabricated evidence, which is a far worse problem for the author than a heavily edited sentence.

## Meaning or style? The test

Fix it if a careful reader of CORRECTED would come away believing something different from a reader of ORIGINAL. Otherwise leave it.

| Fix (meaning) | Leave (style) |
|---|---|
| Names, titles, dates, numbers, units, page references, citations | Synonyms for words that are not terms of art |
| Quotations, in full | Register, rhythm, sentence length, contractions |
| Terms of art: words ORIGINAL uses consistently as technical vocabulary | Sentences split or merged, paragraph breaks moved |
| Polarity and direction: lost or added negation, swapped cause and effect, swapped subject and object | Active or passive voice when the agents survive |
| Strength and scope: hedges, modals, quantifiers, comparatives ("may", "some", "often", "to some extent") | Spelling convention, connective variety |
| Logical relation: paired or contrasted, because or although, therefore or however | Word order changes that keep every relation intact |
| Referents: who does what, "either" or "both", what a pronoun points to | Flat or clumsy phrasing that still makes the same claim |
| Additions: anything the rewrite asserts that ORIGINAL does not (cut) | |
| Omissions: claims, evidence or steps missing from the rewrite (insert) | |
| Duplicated blocks (cut the later copy) | |

Worked decisions:

| ORIGINAL | REWRITE | Do | Why |
|---|---|---|---|
| the speaker | the narrator | substitute, everywhere | term of art: poems have speakers |
| "tacked to your saliva grid / of approvals" (6) | "an object within your approved framework" (6) | restore the whole quotation | evidence |
| is paired with | is contrasted with | substitute one word | the relation flipped |
| may reduce | reduces | substitute | hedge lost, claim got stronger |
| fell by 12% | fell by 21% | substitute | number |
| begins to denature | starts to lose its shape | "starts to {~~lose its shape~>denature~~}" | term of art; "starts to" is faithful, so it stays |
| impedes the reader's comprehension | hinders reading comprehension | leave | same claim, flatter wording |
| does not | doesn't | leave | register only |
| one long paragraph | same content in three short ones | leave | layout only |
| (nothing) | "a dramatic collapse" | cut | evaluation ORIGINAL never makes |
| a sentence the argument depends on | (missing) | insert ORIGINAL's sentence | omission |

Mechanical damage (a missing space after a full stop, a doubled word, broken punctuation, a tense slip that makes a sentence inconsistent with its neighbours) gets the smallest possible fix. Awkwardness alone is not damage.

## Procedure

### 1. Pin down the inputs

If the texts are uploaded files, copy them into the working directory as `original.txt` and `rewrite.txt`, converting from docx or pdf to plain text first. If they were pasted into the chat there is no file to check against: build the marked-up source by copying the rewrite out of the conversation paragraph by paragraph, touching nothing outside your tokens, then spot-check five sentences spread through the text against the conversation.

### 2. Diagnose before editing

Read both texts completely, then make three working lists:

- **Alignment map.** Label each rewrite paragraph identical, faithful, damaged, duplicated, or added, and list ORIGINAL paragraphs that have no counterpart.
- **Evidence inventory.** Every quotation, name, title, number and citation in ORIGINAL, one per line in `required.txt`. The script confirms each one appears verbatim in the result.
- **Term drift glossary.** Each term of art and what the rewrite turned it into (`speaker -> narrator`, `line break -> newline character`). Apply each fix at every occurrence. Put a wrong form in `banned.txt` only if it has no legitimate use anywhere in the text.

Work out how the rewrite was produced when it shows, because the mechanism predicts where the damage is. A machine translation round trip transliterates names, swaps terms of art for near-synonyms from other fields, and paraphrases quotations while leaving the page numbers attached. Human paraphrase drops hedges and merges claims. Summarising edits drop steps. Tell the user plainly what you see, even when it contradicts how they described the rewrite.

### 3. Mark up the rewrite

Copy the rewrite into `source.txt` and express every change in CriticMarkup. Nothing outside a token may differ from the rewrite.

```
{--text--}        cut
{++text++}        insert
{~~old~>new~~}    substitute
{>>note<<}        note for the change log (never appears in the text)
@@WORDCOUNT@@     filled with the word count, for texts that state their own
```

- One error, one token, smallest span. Merge neighbouring fixes into one token only when the words between them change too. Large tokens hide how much of the rewrite survived and inflate the bold.
- Put a `{>>note<<}` straight after any edit whose reason is not obvious from the before and after: a reversed claim, a restored quotation, a reinstated sentence. A paragraph containing only a note becomes a bullet at the top of the log; use that for block-level cuts.
- Insertions made only of spaces or punctuation (`{++ ++}`, `{~~ — ~>, ~~}`) are treated as mechanical fixes and are not bolded. Use the same trick to add a Markdown heading marker without breaking the verbatim check: `{++## ++}Introduction`.
- Do not worry about the space a cut leaves behind; the script closes the seam.

Example. ORIGINAL: *Catalase activity may decrease above 40 °C because the enzyme begins to denature. In our trials, the rate fell by 12% between 40 °C and 50 °C. As Patel notes, "heat does not destroy the enzyme at once; it unfolds it" (Patel 14). We did not measure pH, so the results cannot separate the two effects.*

Marked-up rewrite:

```
Catalase activity {~~decreases~>may decrease~~} above 40 °C because the enzyme starts to {~~lose its shape~>denature~~}.{++ ++}In our trials, the rate fell by {~~21%~>12%~~} between 40 °C and 50 °C{-- — a dramatic collapse--}.{>>evaluation the original never makes<<} As {~~Patil~>Patel~~} notes, "{~~heat destroys the enzyme gradually~>heat does not destroy the enzyme at once; it unfolds it~~}" (Patel 14). We {~~measured~>did not measure~~} pH, so it isn't possible to tell the two effects apart from the results.
```

Note what was spared: "starts to" and the whole clumsy last clause, contraction included. They are faithful, so they stay.

### 4. Build and check

```bash
python scripts/build_outputs.py source.txt --name <slug> \
    --rewrite rewrite.txt --original original.txt \
    --ban-file banned.txt --require-file required.txt \
    [--count-from "## Introduction" --count-to "## Works Cited"] [--allow-em-dash]
```

It writes `<slug>-corrected.md` (inserted and replaced wording in bold) and `<slug>-change-log.md` (before and after for every touched sentence, which is the only way pure cuts become visible) to `/mnt/user-data/outputs`, then reports:

- `--rewrite`: whether the markup reproduces the rewrite exactly. A FAIL here means you reworded something without marking it. Fix the markup, not the check.
- `--original`: inserted wording that does not occur in ORIGINAL. Glue words are fine; anything longer should have been ORIGINAL's own phrasing.
- leftover markup, em dashes, banned strings that survived, required strings that are missing.
- warnings for seams: double spaces, space before punctuation, a/an before a changed word, lower-case sentence starts, repeated words.
- scale: sentences touched, share of words in bold, and the mix of cuts, insertions and substitutions.

Omit the flags whose files you do not have. If `scripts/build_outputs.py` is missing (the skill was installed as a bare SKILL.md), write an equivalent script from the token rules above before trying this by hand; hand-applied bold drifts out of step with the text on anything longer than a page.

### 5. Read the result

Read CORRECTED once from start to finish as a reader would. Check every seam: subject and verb agreement after a substitution, articles, capital letters after a cut, tense consistency, a sentence that no longer parses. Make fixes in `source.txt` and rebuild. Never hand-edit the output files, because the text and the log would stop matching.

### 6. Report

Present the corrected file first, then the change log. In the chat, keep it short and cover:

1. What kind of rewrite this looks like and the worst damage, with three to six concrete before and after examples.
2. Scale, from the script's numbers.
3. What changed, by category, and what you deliberately left alone, so the user knows the flat phrasing was seen and spared on purpose.
4. What they must check by hand: quotations against the primary source (this skill restores to ORIGINAL; if ORIGINAL misquotes, so does CORRECTED), formatting Markdown cannot carry such as italics and footnotes, and the word count in their own tool under their own institution's counting rule.
5. An honest verdict. When a large share of sentences needed repair (as a rough guide, more than a third) or the rewrite altered evidence, say directly that ORIGINAL is the stronger text and that every untouched sentence is accurate, not better. The user gets the repair they asked for in full, and also the truth about what it produced.

## Output defaults

- Return the full text. Never excerpts, never "rest unchanged".
- Bold every inserted or replaced word. Headings, spacing and punctuation-only fixes are not bolded.
- No em dashes anywhere in CORRECTED. Turn the rewrite's em dashes into commas (or a colon or full stop where the sentence needs one) and never add one in an insertion. The one exception is inside a restored quotation: the quotation wins, so run with `--allow-em-dash` and mention it in the report.
- No placeholders, brackets or comments in the text itself.
- Keep the rewrite's paragraphing, sentence breaks, contractions and spelling convention.
- Update statements about the text that your edits made false, such as a stated word count.
- If the user wants Word output, build the `.md` first, then convert it by following the docx skill so the bold carries over as bold runs.

The user's instructions in the conversation override any of these.

## What this skill does not do

- **It does not improve the prose.** That is a different job and the user has ruled it out.
- **It does not verify facts.** ORIGINAL is assumed to be right. If you notice that ORIGINAL itself is wrong (a misspelled name, a sum that does not add up), do not fix it silently in either direction; carry ORIGINAL's version and flag it in the report.
- **It does not tune text for AI detectors.** Users sometimes want this repair because they hope the rewrite will read as more human to a detector. The repair is identical either way: choose edits by fidelity and by the budget above, never by how a span might score. Do not add deliberate errors, "humanising" noise or odd phrasing, and do not predict or promise any detector result. If the user raised that goal, say so in a sentence or two in the report, together with what actually protects an author from a false flag: version history, dated drafts, and being able to explain the work. For assessed work, the institution's own rules on AI assistance and acknowledgment are what count.
