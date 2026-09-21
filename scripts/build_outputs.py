#!/usr/bin/env python3
"""Build the corrected text and the change log from a marked-up rewrite, then check them.

The source file is the REWRITE, copied verbatim, with edits marked in CriticMarkup:

  {--text--}        cut from the rewrite
  {++text++}        inserted (bold in the corrected text)
  {~~old~>new~~}    substituted: old is cut, new is inserted (bold)
  {>>note<<}        note for the change log; never appears in the corrected text
  @@WORDCOUNT@@     replaced by the word count of the counted range

Insertions with no letters or digits (a space, a comma) are mechanical fixes and
are not bolded. A paragraph that is only a note becomes a bullet at the top of the log.

Usage:
  python build_outputs.py source.txt --name my-essay \
      [--out-dir /mnt/user-data/outputs] [--rewrite rewrite.txt] [--original original.txt] \
      [--ban-file banned.txt] [--require-file required.txt] \
      [--count-from "## Introduction" --count-to "## Works Cited"] [--allow-em-dash]

Exit code 0 = all hard checks passed, 1 = at least one failed (files are written either way).
"""
import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

TOKEN = re.compile(r'\{--(.*?)--\}|\{\+\+(.*?)\+\+\}|\{~~(.*?)~>(.*?)~~\}|\{>>(.*?)<<\}', re.S)
SENT_SPLIT = re.compile(r'(?:(?<=[.?!])|(?<=[.?!][”"’)\]]))((?:\x01\d+\x01)*)\s+(?![(a-z])')


def split_sentences(p):
    """Split a paragraph into sentences. Stashed notes (\\x01n\\x01) right after the full stop
    stay with the sentence they comment on instead of blocking the split."""
    out, start = [], 0
    for m in SENT_SPLIT.finditer(p):
        out.append(p[start:m.start()] + (m.group(1) or ''))
        start = m.end()
    out.append(p[start:])
    return [x for x in out if x]
MACRO = '@@WORDCOUNT@@'


def has_alnum(s):
    return any(c.isalnum() for c in s)


def bold(text):
    """Bold the alphanumeric core of each line. Edge punctuation and spaces stay outside
    the markers, so every span is valid Markdown wherever it lands."""
    out = []
    for line in re.split(r'(\n)', text):
        if line == '\n' or not has_alnum(line) or line.lstrip().startswith('#'):
            out.append(line)
            continue
        i = next(k for k, c in enumerate(line) if c.isalnum())
        j = len(line) - next(k for k, c in enumerate(reversed(line)) if c.isalnum())
        out.append(line[:i] + '**' + line[i:j] + '**' + line[j:])
    return ''.join(out)


def render(s, mode):
    """mode='final' -> corrected text with bold; mode='rewrite' -> the rewrite as it was."""
    out, pos = [], 0
    last = '\n'
    for m in TOKEN.finditer(s):
        chunk = s[pos:m.start()]
        if chunk:
            out.append(chunk)
            last = chunk[-1]
        pos = m.end()
        cut, ins, old, new, _note = m.groups()
        if mode == 'final':
            rep = bold(ins) if ins is not None else bold(new) if new is not None else ''
        else:
            rep = cut if cut is not None else old if old is not None else ''
        if rep:
            out.append(rep)
            last = rep[-1]
            continue
        # Something was removed: tidy the seam so "a {--b--} c" does not leave two spaces
        # and "a {--b--}, c" does not leave a space before the comma.
        nxt = s[pos:pos + 1]
        if nxt == ' ' and last in ' \n':
            pos += 1
        elif nxt and nxt in ',.;:?!' and last == ' ' and out:
            out[-1] = out[-1][:-1]
            last = out[-1][-1:] or '\n'
    out.append(s[pos:])
    text = ''.join(out)
    return text.replace('****', '') if mode == 'final' else text


def tidy(s):
    s = re.sub(r'[ \t]+\n', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip() + '\n'


def plain(s):
    return re.sub(r'^#+\s*', '', s.replace('**', ''), flags=re.M)


def squash(s):
    return ''.join(s.split())


def typo_norm(s):
    s = unicodedata.normalize('NFKC', s)
    for a, b in (('‘', "'"), ('’', "'"), ('“', '"'), ('”', '"'), ('–', '-'), ('—', '-'), ('…', '...')):
        s = s.replace(a, b)
    return s


def count_range(text, cfrom, cto):
    """Slice of text between the two markers. Bold markers are kept (callers strip them)."""
    a = text.find(cfrom) if cfrom else 0
    b = text.find(cto, max(a, 0)) if cto else len(text)
    if a < 0 or b < 0:
        raise SystemExit('count range marker not found (markers must not contain edited words): %r / %r' % (cfrom, cto))
    return text[a:b]


def words(s):
    return len(plain(s).split())


def first_words(s, n=30):
    w = s.split()
    return ' '.join(w[:n]) + (' … [%d words in total]' % len(w) if len(w) > n else '')


def build_log(src):
    store = []

    def stash(m):
        store.append(m.group(0))
        mark = '\x01' if m.group(5) is not None else '\x00'      # notes get their own marker
        return '%s%d%s' % (mark, len(store) - 1, mark)

    def unstash(s):
        return re.sub(r'[\x00\x01](\d+)[\x00\x01]', lambda m: store[int(m.group(1))], s)

    def marked(s):
        return '\x00' in s or '\x01' in s

    notes, entries = [], []
    for para in re.split(r'\n\s*\n', TOKEN.sub(stash, src)):
        para = para.strip()
        if not marked(para):
            continue
        if re.fullmatch(r'(?:\x01\d+\x01\s*)+', para):            # paragraph of notes only
            notes += [m.group(5).strip() for m in TOKEN.finditer(unstash(para))]
            continue
        for sent in split_sentences(para):
            if not marked(sent):
                continue
            full = unstash(sent)
            inline = [m.group(5).strip() for m in TOKEN.finditer(full) if m.group(5) is not None]
            before, after = render(full, 'rewrite').strip(), render(full, 'final').strip()
            if before == plain(after).strip():               # nothing visible changed (note only, or a heading marker)
                notes += inline
                continue
            entries.append((before, after, inline))
    return notes, entries


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source')
    ap.add_argument('--name', default='corrected')
    ap.add_argument('--out-dir', default='/mnt/user-data/outputs')
    ap.add_argument('--rewrite', help='the rewrite as a file: proves the markup reconstructs it exactly')
    ap.add_argument('--original', help='the original as a file: lists inserted wording that is not in it')
    ap.add_argument('--ban-file', help='one string per line that must NOT survive (e.g. a mistranslated name)')
    ap.add_argument('--require-file', help='one string per line that MUST appear verbatim (quotes, names, titles)')
    ap.add_argument('--count-from', help='text where the counted range starts (default: start)')
    ap.add_argument('--count-to', help='text where the counted range stops (default: end)')
    ap.add_argument('--allow-em-dash', action='store_true')
    a = ap.parse_args()

    src = Path(a.source).read_text(encoding='utf-8')
    fails, warns = [], []

    # word count macro: the number is one word whatever its value, so count first, fill second
    n_final = words(count_range(tidy(render(src.replace(MACRO, '0'), 'final')), a.count_from, a.count_to))
    src = src.replace(MACRO, str(n_final))
    final = tidy(render(src, 'final'))
    rewrite = tidy(render(src, 'rewrite'))
    n_rewrite = words(count_range(rewrite, a.count_from, a.count_to)) if not a.count_from or a.count_from in rewrite else None
    flat = plain(final)

    # ---- hard checks --------------------------------------------------------------------
    left = re.findall(r'\{--|--\}|\{\+\+|\+\+\}|\{~~|~~\}|\{>>|<<\}|@@WORDCOUNT@@', final)
    if left:
        fails.append('leftover markup in corrected text: %s' % sorted(set(left)))
    if not a.allow_em_dash and '—' in final:
        ctx = [final[max(0, m.start() - 30):m.end() + 30].replace('\n', ' ') for m in re.finditer('—', final)]
        fails.append('%d em dash(es): %s' % (len(ctx), ctx[:5]))
    if a.ban_file:
        for b in filter(None, (l.strip() for l in Path(a.ban_file).read_text(encoding='utf-8').splitlines())):
            hits = [flat[max(0, m.start() - 30):m.end() + 30].replace('\n', ' ') for m in re.finditer(re.escape(b), flat)]
            if hits:
                fails.append('banned string survives: %r x%d e.g. %r' % (b, len(hits), hits[0]))
    if a.require_file:
        ws = lambda s: ' '.join(s.split())
        for r in filter(None, (l.strip() for l in Path(a.require_file).read_text(encoding='utf-8').splitlines())):
            if ws(r) in ws(flat):
                continue
            if typo_norm(ws(r)) in typo_norm(ws(flat)):
                warns.append('required string matches only after normalizing quote/dash characters: %r' % r)
            else:
                fails.append('required string missing: %r' % r)
    if a.rewrite:
        real = Path(a.rewrite).read_text(encoding='utf-8')
        if squash(real) == squash(rewrite):
            print('reconstruction: PASS (markup reproduces the rewrite exactly, ignoring whitespace)')
        elif squash(typo_norm(real)) == squash(typo_norm(rewrite)):
            warns.append('markup reproduces the rewrite only after normalizing quote/dash characters (typography was retyped)')
        else:
            sm = difflib.SequenceMatcher(None, real.split(), rewrite.split(), autojunk=False)
            hunks = [(real.split()[i1:i2], rewrite.split()[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
            fails.append('markup does NOT reproduce the rewrite: %d unmarked difference(s). First ones (rewrite file -> markup): %s'
                         % (len(hunks), [(' '.join(x), ' '.join(y)) for x, y in hunks[:8]]))
    for m in re.finditer(r'\*\*(.+?)\*\*', final, re.S):
        if not (m.group(1)[0].isalnum() and m.group(1)[-1].isalnum()) or '\n' in m.group(1):
            fails.append('invalid bold span: %r' % m.group(0)[:60])

    # ---- warnings -----------------------------------------------------------------------
    for pat, label in ((r'\S {2,}\S', 'double space'), (r' [,.;:?!](?!\.)', 'space before punctuation'),
                       (r',,|;;|\.,|,\.', 'doubled punctuation'),
                       (r'\b[Aa] \*\*[aeiouAEIOU]', 'article: "a" before a vowel'),
                       (r'\b[Aa]n \*\*[b-df-hj-np-tv-zB-DF-HJ-NP-TV-Z]', 'article: "an" before a consonant'),
                       (r'(?:[.?!][”"]?\s+)(?:\*\*)?[a-z]', 'sentence may start in lower case'),
                       (r'\b(\w+) \1\b', 'repeated word')):
        hits = [final[max(0, m.start() - 25):m.end() + 25].replace('\n', ' ') for m in re.finditer(pat, final)]
        if hits:
            warns.append('%s x%d: %s' % (label, len(hits), hits[:4]))

    # ---- statistics ---------------------------------------------------------------------
    ms = list(TOKEN.finditer(src))
    st = dict(cut=0, ins=0, sub=0, mech=0, w_cut=0, w_ins=0, w_sub_old=0, w_sub_new=0)
    inserted = []
    i = 0
    while i < len(ms):
        cut, ins, old, new, note = ms[i].groups()
        nxt = ms[i + 1] if i + 1 < len(ms) and ms[i].end() == ms[i + 1].start() else None
        if old is not None or (nxt and ((cut is not None and nxt.group(2) is not None) or (ins is not None and nxt.group(1) is not None))):
            if old is None:
                old = cut if cut is not None else nxt.group(1)
                new = ins if ins is not None else nxt.group(2)
                i += 1
            if has_alnum(new) or has_alnum(old):
                st['sub'] += 1; st['w_sub_old'] += len(old.split()); st['w_sub_new'] += len(new.split()); inserted.append(new)
            else:
                st['mech'] += 1
        elif cut is not None:
            st['cut'] += 1; st['w_cut'] += len(cut.split())
        elif ins is not None:
            if has_alnum(ins):
                st['ins'] += 1; st['w_ins'] += len(ins.split()); inserted.append(ins)
            else:
                st['mech'] += 1
        i += 1
    if a.original:
        orig = typo_norm(' '.join(Path(a.original).read_text(encoding='utf-8').split())).lower()
        strip_edges = lambda s: re.sub(r'^\W+|\W+$', '', typo_norm(' '.join(s.split())).lower())
        missing = [s.strip() for s in inserted if strip_edges(s) and strip_edges(s) not in orig]
        if missing:
            warns.append('%d of %d inserted spans are not wording from the original (fine for glue words; '
                         'anything longer should be the original\'s own phrasing): %s' % (len(missing), len(inserted), missing[:25]))

    notes, entries = build_log(src)
    bold_words = sum(len(x.split()) for x in re.findall(r'\*\*(.+?)\*\*', count_range(final, a.count_from, a.count_to), re.S))
    n_sent = len([s for p in re.split(r'\n\s*\n', flat) for s in split_sentences(p.strip())])

    # ---- write files --------------------------------------------------------------------
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    f_final = out_dir / (a.name + '-corrected.md')
    f_log = out_dir / (a.name + '-change-log.md')
    f_final.write_text(final, encoding='utf-8')
    log = ['# Change log: rewrite to corrected version', '',
           'Each entry is one sentence of the rewrite (sometimes two that run together). Bold in "After" marks inserted or '
           'replaced wording. An "After" that is shorter and has no bold is a pure cut. Spacing and punctuation-only fixes are not bolded.', '']
    log += ['- ' + n for n in notes] + ([''] if notes else [])
    for k, (b, af, inline) in enumerate(entries, 1):
        log += ['**%d.**' % k, '']
        if not af:
            log += ['Cut entirely: ' + first_words(b), '']
        elif not b:
            log += ['Inserted: ' + af, '']
        else:
            log += ['Before: ' + b, '', 'After: ' + af, '']
        log += ['Note: ' + n for n in inline] + ([''] if inline else [])
    f_log.write_text('\n'.join(log), encoding='utf-8')

    # ---- report -------------------------------------------------------------------------
    print('wrote', f_final)
    print('wrote', f_log)
    print('words in counted range: rewrite=%s corrected=%d' % (n_rewrite, n_final))
    print('bold words: %d = %.1f%% of corrected' % (bold_words, 100.0 * bold_words / max(1, n_final)))
    print('sentences touched: %d of about %d (%.0f%%)' % (len(entries), n_sent, 100.0 * len(entries) / max(1, n_sent)))
    print('edits: pure cuts=%(cut)d (%(w_cut)d words) | pure insertions=%(ins)d (%(w_ins)d words) | '
          'substitutions=%(sub)d (%(w_sub_old)d words out, %(w_sub_new)d in) | mechanical=%(mech)d' % st)
    for w in warns:
        print('WARN:', w)
    for f in fails:
        print('FAIL:', f)
    print('RESULT:', 'FAIL' if fails else 'PASS')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
