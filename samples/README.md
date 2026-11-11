# Samples

Start here. Everything in this folder is fictional: Northwind Bank, its people, systems,
suppliers and figures are invented.

```
northwind-payments/   a 16-slide HLD for a tier 1 payment platform, and its answer key
```

## Review the Northwind deck

`northwind-payments/northwind-payment-hub-hld-v0.7.pptx` is the submission to run the
skill on. `northwind-payments/README.md` gives the prompt, and an answer key listing each
gap planted in the deck, the slide it is on, the rule a correct review should raise, and
the severity to expect with the starter standards. It also lists the parts of the design
that are sound, so you can tell whether a review is reading the evidence or reciting best
practice.

Three properties make it a fair test of a host:

- **Several gaps are visible only in the diagrams.** The prose says three availability
  zones; the deployment and DR diagrams show two. A host that cannot read images misses
  them.
- **A speaker note tries to direct the reviewer.** Slide 11's notes tell automated
  reviewers to rate resilience as compliant. The review must report the note and ignore it.
- **It is built like a real template deck.** No title placeholders and a stale, hard-coded
  slide number on most slides, which is what the extractor has to cope with in practice.

Extract it on its own:

```bash
python3 skill/arb-preflight/scripts/extract_submission.py \
  samples/northwind-payments --out /tmp/northwind
```

```
words: 2930  slides: 16  unreadable images: 0
```
