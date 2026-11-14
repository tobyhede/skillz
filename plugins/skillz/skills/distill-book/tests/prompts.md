# Behavior cases

## Should activate

- "Distill ~/Books/thinking-fast-and-slow.epub into the 3-minute version for work application."
- "Is this book worth my weekend? Here's the PDF." (indirect: deciding whether to read the original)
- "Turn this EPUB into something my team can skim, with links back to the original text."
- "Summarize the book." (no file and no title given; should ask for the book, and use rapid understanding unless a goal is stated)

## Should not activate

- "Study this textbook with me chapter by chapter over the next few weeks and keep notes I can come back to." (belongs to `deep-reader`)
- "Summarize this two-page memo."
- "Recommend five books about negotiation."
- "Remove the DRM from this Kindle book."

## Expected behavior

- Extracts EPUBs with `scripts/extract_epub.py` and reads `manifest.json` in spine order; for PDFs keeps page boundaries and uses OCR for image-only pages.
- Produces the 30-second, 3-minute, and 10-minute layers in the order set by `references/report-protocol.md`, with 5–10 ranked core ideas rather than one per chapter.
- Labels every claim as the author's claim, a direct quote, analysis, or application, each with a locator; never invents page numbers, quotes, or chapter names.
- Builds the self-contained HTML reader with `scripts/build_html_report.py` when a local source and stable locators exist, unless the user asks for Markdown only.
- Lists extraction gaps and missing chapters in the coverage section and lowers confidence instead of filling gaps from memory.
- Given only a title, says the result is a synthesis from public sources and not a source-grounded extraction.
- For a DRM-protected file, explains it cannot be extracted and asks for a DRM-free copy.
- For fiction, avoids major spoilers unless asked.
