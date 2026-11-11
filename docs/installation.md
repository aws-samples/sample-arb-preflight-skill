# Installation

The skill itself is host-neutral: a folder, `skill/arb-preflight/`, holding a `SKILL.md`
plus reference files and three standard-library Python scripts. Installing it means
putting that folder where your agent host looks for skills. `install.sh` does that for
you; run it from the root of your copy of this repository:

```bash
./install.sh <target> [options]
```

| Target | Command | Installs to |
|---|---|---|
| Kiro (workspace) | `./install.sh kiro --dest <workspace>` | `<workspace>/.kiro/skills/arb-preflight` |
| Kiro (user-wide) | `./install.sh kiro --global` | `~/.kiro/skills/arb-preflight` |
| Claude Code (project) | `./install.sh claude --dest <project>` | `<project>/.claude/skills/arb-preflight` |
| Claude Code (user-wide) | `./install.sh claude --global` | `~/.claude/skills/arb-preflight` |
| Amazon Quick | `./install.sh quick` | builds `dist/arb-preflight.zip` for upload |
| Any other host | `./install.sh dir --dest <skills-folder>` | `<skills-folder>/arb-preflight` |

Add `--force` to overwrite an existing install without being asked. The script uses only
`bash`, `tar` and `zip`, downloads nothing, and never copies a `reviews/` folder.

On Windows without bash, copy `skill/arb-preflight/` into the host's skills folder by hand;
the result is identical.

---

## Amazon Quick

Use **Amazon Quick on desktop**, which can read local files, run code and orchestrate
agents. The browser experience cannot run the extractor or write the output folder.

1. Build the package: `./install.sh quick` → `dist/arb-preflight.zip`.
2. In Quick, open **Customize › Skills › Create**, then either:
   - **From file** and choose `dist/arb-preflight.zip`, or
   - **From folder** and choose `skill/arb-preflight/` (the folder with `SKILL.md` at its
     root, as Quick expects).
3. Review the imported skill, save it, and use **Try it** for the smoke test below.
4. Optional: `./install.sh quick --profile <name>` also copies the folder into
   `~/.quickwork/profiles/<name>/skills/`. This follows the layout used in the AWS samples
   Quick knowledge hub rather than the user guide, so prefer the Create flow if the two
   differ. Restart Quick desktop afterwards.

Reference: [Amazon Quick — Skills](https://docs.aws.amazon.com/quick/latest/userguide/skills-desktop.html).

If Quick rejects the zip, use **From folder**. The zip contains the `arb-preflight/` folder
at its root, and hosts differ on whether they expect that wrapper.

---

## Smoke test (any host)

Run these in order after installing. Each one isolates a capability the review depends on.

1. **Activation and nested files** — "List the rule IDs in the arb-preflight skill's
   `rubric/security.md`." Expect 36 IDs. If subfolders are unreachable, flatten them
   (`rubric-security.md` …) and update the paths in `SKILL.md`.
2. **Code execution** — run the extractor on any `.pptx`:
   `python3 <skill-folder>/scripts/extract_submission.py deck.pptx --out ./extracted`.
   Expect a `words: … slides: …` line. Drop `--convert` off macOS.
3. **Vision** — "Describe `extracted/media/<one-of-the-images>.png`." **This is the
   dealbreaker.** Most contradictions come from diagrams, and a text-only run misses them.
4. **Fan-out** — ask for the seven domain reviewers. If the host cannot run isolated
   subagents in parallel, have it run them sequentially. Do not let it merge the domains
   into a single pass.
5. **Write access** — confirm it creates `reviews/<app>/<date>/` with
   `preflight-report.md`, `board-pack.md` and `findings.json`.

---

## Customise after installing

The installed copy is yours to edit. Replace the starter content in `standards/` with your
own policy (see `skill/arb-preflight/AUTHORING.md` and `docs/adoption-guide.md`), then
check integrity:

```bash
python3 tools/validate.py
```

If you maintain your standards in a fork of this repository, re-run `install.sh` after each
change instead of editing installed copies.
