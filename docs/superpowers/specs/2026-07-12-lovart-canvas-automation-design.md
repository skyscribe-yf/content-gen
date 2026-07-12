# Lovart Canvas Browser Automation — Design

## Goal

Add an isolated, browser-driven helper that generates the images for one article from its `prompts/*.md` files using the article's Lovart Canvas project. It must preserve Lovart's visible UI flow, require manual login, respect the eight-image daily budget, download successful images locally, and resume without duplicate submissions.

This helper is experimental. It does not replace or modify the project's existing `apimart.ai` image-generation backend.

## Scope

The command will be:

```text
python scripts/lovart_canvas.py --article content/YYYY-MM-DD-topic
```

It will:

1. Discover and lexically order `prompts/*.md` in the article directory.
2. Derive `21:9` for a prompt whose filename begins with `00-cover`; derive `1:1` for every other prompt.
3. Name each output from the prompt stem, for example `00-cover.md` becomes `images/00-cover.png`.
4. Read the Canvas project name from `weixin.md` front-matter `title`; fall back to the article directory name.
5. Reuse a previously recorded Lovart project, or create one through the visible Lovart UI and record its ID.
6. Submit at most eight new image jobs per local calendar day and wait for each one to finish before submitting the next.
7. Download successful results to `images/` and retain durable job state for resumption.

It will not use the copied browser cookie, a private Lovart HTTP endpoint, concurrent job submission, credit-limit bypasses, CAPTCHA bypasses, or automatic image-quality regeneration.

## Architecture

### Browser driver

The automation will run Lovart in a persistent local browser profile stored outside the repository. A first run opens the browser for the author to sign in normally. Subsequent runs reuse that local profile; the profile directory is supplied by a command-line option or an environment-specific default and is never committed.

The driver interacts only with visible Canvas controls: opening/creating a project, choosing the GPT Image 2 generator, setting the aspect ratio, entering a prompt, starting generation, waiting for completion, and using the UI's download control. It should rely on stable accessibility labels and test IDs when available, with narrowly scoped text fallbacks. Any login wall, quota dialog, UI mismatch, or anti-automation challenge stops the run and records a resumable error instead of attempting a workaround.

### Article-local state

The script will maintain `lovart-canvas.json` in the article directory. Its records include:

- `project_id` and `project_name`;
- the selected Canvas URL;
- the normalized prompt, aspect ratio, and SHA-256 fingerprint for each job;
- submission date/time, status, output filename, and any error message;
- the date and number of submissions counted toward the daily cap.

The fingerprint combines the prompt body, the derived ratio, and the fixed GPT Image 2 selection. A matching job in `submitted`, `running`, or `completed` state is never submitted again. A failed job remains visible and requires an explicit retry option; it is not retried automatically.

### Prompt and output handling

Prompt Markdown is treated as the generation source. The script extracts the meaningful body while ignoring optional front matter. Empty prompts fail before opening the generator. Existing non-empty output files are treated as completed only if their matching manifest entry is completed; an orphaned file causes a clear conflict rather than being overwritten.

The script operates on one article directory per invocation. It never scans or creates projects for other articles. The project name is taken from `weixin.md` front matter when available, otherwise the directory basename, yielding a distinct Lovart project for each article.

## Control flow and failure handling

```text
article directory
  → discover prompts and validate output names
  → load manifest / reuse or create Canvas project
  → skip recorded or already-counted jobs
  → enforce eight-new-submissions-today limit
  → drive one visible GPT Image 2 generation
  → wait for completion and download image
  → atomically update manifest
  → continue or stop with a resumable status
```

The manifest is written atomically before and after external actions. If the browser or process stops after a submission, the job is left `submitted` rather than reissued. On a later run the script opens the same project, checks for the result in the visible Canvas, and either downloads it or reports that manual confirmation is needed. It never assumes a timeout means Lovart rejected the request.

## CLI surface

- `--article PATH` — required article directory.
- `--profile-dir PATH` — optional persistent browser profile location.
- `--dry-run` — prints the project name, ordered prompts, ratios, output paths, and resume decisions without opening a browser or spending credits.
- `--retry-failed` — makes explicitly failed jobs eligible for one new submission, subject to the daily cap.
- `--max-new N` — optional lower per-run ceiling; may not exceed eight.

The default is safe: eight maximum new jobs per day, no automatic retry, and no overwrite.

## Validation

Unit tests will cover prompt discovery, front-matter stripping, title fallback, ratio/output-name derivation, fingerprint stability, manifest migration/loading, daily-cap accounting, and duplicate/resume decisions. The browser driver will be dependency-injected so these tests do not open Lovart or spend credits.

Live validation is deliberately a manual smoke test: run `--dry-run`, sign in through the browser, create or reuse a test Canvas project, submit one low-risk prompt, confirm the downloaded file and manifest, then verify a second run skips the same job. The automation must stop safely if the UI is unavailable or Lovart asks for verification.

## Compatibility and security

The tool uses browser automation because public bundle inspection found internal generator routes but no documented API contract. It stores no user token, cookie, password, or session export in the repository. Its browser profile and downloaded images remain local to the author's machine. The implementation must not log authentication material or send it to other services.
