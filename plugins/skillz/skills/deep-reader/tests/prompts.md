# Behavior cases

## Should activate

- "Study this 320-page policy book for my literature review and trace the author's causal argument with page citations."
- "I need to really understand this PhD thesis before my committee meeting next month." (indirect: no mention of notes or passes)
- "Đọc và phân tích luận án này giúp tôi." (Vietnamese request for the same goal)
- "What did chapter 7 say about feedback loops?" when a `<slug>-notes/` workspace from an earlier session sits next to the source file (should answer from the notes, not re-read the book)
- "Help me read this book." (no purpose stated; should ask what the reader wants from the book before choosing overview or study mode)

## Should not activate

- "Summarize this 6-page article." (short enough to read directly)
- "Give me the 3-minute version of this business book so I can decide whether to read it." (fast briefing belongs to `distill-book`)
- "Write a book review of a novel I haven't given you."
- "Convert this EPUB to PDF."

## Expected behavior

- Runs `prepare-text.sh` first and reads its JSON (`pages`, `est_tokens`, `mode_hint`, `synthetic_pages`); reuses an existing workspace instead of reconverting.
- Confirms the chapter structure against the real table of contents rather than trusting `extract-structure.sh`'s seed.
- In study mode writes one note per coherent argument unit, runs the Recite check before moving on, and synthesizes from the notes, never the raw text.
- Every claim in `synthesis.md` carries a page cite into `source.txt`; when the source has synthetic pages it says the cites are not printed page numbers.
- Runs `verify-quotes.sh` until it exits 0 and logs the hand-verified load-bearing paraphrases.
- Never invents quotes or page numbers; keeps "wrong", "incomplete", and "cannot verify" distinct.
- When `pdftotext` or `pandoc` is missing (exit 2), falls back to reading pages directly and says the mechanical quote check is lost.
- Answers in the language the user asked in, with the synthesis in the conversation and the workspace pointed to.
