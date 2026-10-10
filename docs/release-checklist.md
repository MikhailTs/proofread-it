# Windows MVP release checklist

This checklist is the release-verification record required by
`spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`. It is derived from the approved specification and
does not change product requirements.

## Release candidate

- Overall status: `ACCEPTED` — TP-01 through TP-15 passed
- Implementation revision: `91e1ab46e64a3ffd23fc87774d3d764e46a4e436`
- D-001 remediation basis: commit `54528443b4821760952105ace89125a92b114870`.
- D-002/D-003 remediation basis: commit `595e33d54002e098b069db5a6ae69df36de44102`.
- D-004 remediation basis: commit `91e1ab46e64a3ffd23fc87774d3d764e46a4e436`.
- Approved specification SHA-256:
  `9DB89DFCBC7082EB3D6CE3F4FC9ACCE7B3BD33C7899BD0584965F59551DEB2D3`
- Acceptance owner: Project owner
- Acceptance date: `2026-10-10`
- Windows version: `Microsoft Windows NT 10.0.26200.0` (PowerShell product label:
  `Windows 10 Pro`, version `2009`)
- AutoHotkey version: `2.0.28`
- Final result: `ACCEPTED`

A checked item means that its stated evidence was observed on the recorded revision. Do not infer a
pass from implementation, an older focused check, or an unchecked instruction. Successful hotkey
scenarios and the explicit live test make real, billable API requests.

## Automated evidence

The current automated evidence is:

- [x] `uv sync --dev` on 2026-09-23 — resolved 30 packages and checked 29 packages; exit 0.
- [x] `uv run --no-sync pytest -q -p no:cacheprovider` — 149 passed, 2 live tests
  deselected in 21.00s on the original revision; after D-001, 153 passed and 2 were deselected; after
  the D-002 result-window fix, 154 passed and 2 were deselected; after the D-003 clipboard-ownership
  fix on 2026-09-27, 156 passed and 2 were deselected in 28.91s; after the D-004 selection guard,
  161 passed and 2 were deselected in 28.14s on 2026-10-02.
- [x] Focused D-001 regression through the real CLI, PowerShell wrapper, and AHK source boundary:
  `uv run --no-sync pytest -q -p no:cacheprovider
  tests/component/test_cli_contract.py tests/component/test_app_invocation_wrapper.py
  tests/windows/test_clipboard.py` — 26 passed in 13.35s after the latest fix. The final regression
  uses raw file-descriptor bytes and an existing CRLF so Windows text-mode newline expansion cannot
  be hidden by LF-only fake output or text-mode test capture.
- [x] Focused D-002 result-window regression:
  `uv run --no-sync pytest -q -p no:cacheprovider tests/unit/test_result_window.py` — 6 passed in
  0.10s; covers CRLF, lone CR/LF, Unicode, and an intentional blank line before Tk clipboard output.
- [x] Focused D-003 ownership regression:
  `uv run --no-sync pytest -q -p no:cacheprovider tests/unit/test_result_window.py
  tests/windows/test_clipboard.py::test_result_window_copy_persists_after_tk_owner_closes` —
  8 passed in 1.13s. The Windows test closes a separate Tk process before reading raw
  `CF_UNICODETEXT`, verifies Unicode and one CRLF, and restores the previous clipboard.
- [x] Focused D-004 selection regression:
  `uv run --no-sync pytest -q -p no:cacheprovider tests/windows/test_clipboard.py
  tests/unit/test_request_builder.py tests/component/test_cli_contract.py` — 30 passed in 6.87s;
  covers exact empty text, spaces, tabs, CRLF/LF, mixed whitespace, and exact preservation of valid
  text with leading/trailing whitespace.
- [x] `uv run --no-sync ruff check .` — all checks passed; exit 0.
- [x] `uv run --no-sync mypy src` — no issues in 27 source files; exit 0.
- [x] `%USERPROFILE%\AppData\Local\Programs\AutoHotkey\v2\AutoHotkey64.exe /Validate
  /ErrorStdOut=UTF-8 automation/windows/proofread-it.ahk` — exit 0.
- [x] `git diff --check` — exit 0; line-ending warnings only.
- [x] `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-live.ps1` —
  2 passed in 7.34s on 2026-09-23; the run included one real, billable OpenAI Responses API request.
- [x] TP-01 was rerun after the D-001 code and test changes.
- [ ] Re-run the checks above if product code, configuration, dependencies, tests, or the approved
  specification change before acceptance.

Automated execution status: `TP-01 PASS` on the D-001 commit; `TP-02 PASS` on the unchanged provider
boundary. Evidence basis: revision `54528443b4821760952105ace89125a92b114870`, Python `3.14.7`, uv
`0.12.15`, AutoHotkey `2.0.28`. The two live tests remain intentionally excluded from the default
run and were selected only through the approved live wrapper.

## Manual execution record

### TP-03 — PASS

- Accepted by: Project owner on 2026-09-27.
- Evidence: direct launch completed without a foreground helper terminal; `Ctrl+Alt+E` routed to
  `show_full`, `Ctrl+Alt+Shift+E` routed to `copy_final`, and both latest log events used the default
  `proofread` profile with API status `completed` and a non-empty validated `final_text`.
- Result: D1 Unicode and its single logical line break were preserved by `copy_final`.

### TP-04 — PASS

- Accepted by: Project owner on 2026-09-27.
- Required application matrix: Firefox, Discord, Telegram Desktop, and Notepad++ as the generic
  text editor.
- Additional application evidence: Visual Studio Code as the optional IDE row.
- Result: every TP-04 `show_full` workflow passed, including the readable/resizable result window,
  both copyable result fields, clipboard-sentinel preservation before `Copy result`, copying only
  the complete `final_text` through the button, and the expected successful context/log evidence.
- Previously found D-002 and D-003 remained resolved throughout the completed matrix.

### TP-05 — PASS

- Accepted by: Project owner on 2026-09-27.
- Required application matrix: Firefox, Discord, Telegram Desktop, and Notepad++ as the generic
  text editor.
- Additional application evidence: Visual Studio Code as the optional IDE row.
- Result: every TP-05 `copy_final` workflow completed without a result window, replaced the
  clipboard with only the validated complete `final_text`, and produced the expected single API
  request and successful `copy_final` event.

### TP-06 — PASS

- Accepted by: Project owner on 2026-09-30 after expert manual validation.
- Evidence scope: D2 through D7 were each reviewed through `show_full` against the approved
  proofreading-profile semantic matrix.
- Result: required corrections were made while meaning, facts, tone, register, slang, English
  variant, approximate length, structure, formatting, and line breaks were preserved. D6 was
  treated only as text rather than an instruction, D7 remained unchanged with no corrections, and
  no output translated, summarized, answered, or invented content.

### TP-07 — PASS

- Accepted by: Project owner on 2026-10-02.
- Automated evidence: the TP-01 context-policy, request-builder, and configuration coverage was
  confirmed as passing.
- Manual evidence: a successful TP-04 event was matched to the active application's name, process,
  and window title; its logical request contained only context fields allowed by both the global
  collection policy and the selected profile.
- Result: unknown or disallowed context was absent, and dynamic text and metadata did not override
  stable profile instructions.
- TP-14 subsequently completed the remaining A5 logging/request-boundary evidence.

### TP-08 — PASS

- Reported by: Project owner on 2026-10-02.
- `password` title exclusion: `PASS` for both hotkeys. The source was blocked before clipboard
  capture, secret access, or API access; D8 remained intact; the safe blocked-event evidence met
  the TP-08 requirements.
- KeePass process exclusion: `NOT AVAILABLE`, explicitly accepted by the Project owner on
  2026-10-02. Automated exclusion evidence is retained as required by the test plan.
- Result: TP-08 and acceptance criterion A6 are complete.

### TP-09 — PASS

- Accepted by: Project owner on 2026-10-02.
- Result: empty and whitespace-only selection fails visibly without API access; stale D8 is not
  processed when selection capture fails; changing the active window during pre-capture fails
  before capture/API access; and delayed standard-copy completion within one second is accepted by
  the Windows regression coverage.
- Logging and clipboard result: each failure preserves the appropriate clipboard state and records
  one safe failure event without source text, logical request, or API data.
- D-004 remains resolved and A7 is complete. TP-10 subsequently completed the remaining A8
  text/non-text clipboard evidence.

### TP-10 — PASS

- Accepted by: Project owner on 2026-10-03.
- Result: `show_full` restored the original D8 text and representative non-text clipboard content;
  failures before a result did not replace the clipboard; and a successful `copy_final`
  intentionally replaced it with only the complete validated `final_text`.
- Acceptance criterion A8 is complete.

### TP-11 — PASS

- Accepted by: Project owner on 2026-10-02.
- Result: while one `show_full` request was active, repeated invocations of both actions and a
  repeated launch of the same AHK entry point were rejected immediately with
  `Proofreading is already in progress.` without changing the clipboard or creating another API
  request or invocation event.
- Guard lifecycle: a new invocation succeeded after the original request completed, and protection
  was also released after a deliberately failed request.
- TP-12 subsequently completed the remaining cross-host evidence for A9.

### TP-12 — PASS

- Accepted by: Project owner on 2026-10-10.
- Launch evidence: a temporary external `#Include` host resolved repository-relative paths and
  behaved equivalently to direct launch for both shipped actions; an explicit
  `Invoke("proofread", "copy_final")` binding overrode default routing correctly.
- Concurrency and credential evidence: the direct and external hosts shared one mutex, so the
  second host was rejected during an active request and succeeded afterward; the external host did
  not receive the API key.
- Acceptance criteria A1 and A9 are complete.

### TP-13 — PASS

- Accepted by: Project owner on 2026-10-10.
- Manual evidence: after the actual development secret file `openai_token.txt` was made unavailable,
  a new invocation failed visibly at the credential stage, made no API request, and appended a safe
  failure event without exposing the key. The initial rename of the unrelated `_vk_token.txt` file
  was excluded from the result because the expected secret file remained available.
- Automated evidence: the passing TP-01 error matrix covers invalid configuration, authentication,
  timeout, connection, rate limit, server error, unsupported model, malformed response, empty
  output, bounded `retry_count = 2`, and no retry for deterministic failures.
- Acceptance criteria A10 and A11 are complete.

### TP-14 — PASS

- Accepted by: Project owner on 2026-10-03.
- Log evidence: the single `logs/proofread-it.jsonl` contained the required diagnostic and
  processing fields for successful, blocked, and failed scenarios; blocked events omitted source
  text, logical requests, and API data, while failed events contained only safe diagnostics.
- Sensitive-data review: no event exposed the API key or authorization header. Repeated operations
  did not use `previous_response_id`, conversation state, web-chat history, or a prior result.
- The intentional presence of selected text, context, logical requests, raw responses, and
  normalized results in the MVP log, together with the owner's responsibility to protect or delete
  that file, was accepted as part of TP-14.
- Acceptance criteria A5 and A11 are complete. TP-15 subsequently completed A12.

### TP-15 — PASS

- Accepted by: Project owner on 2026-10-10.
- Result: the accepted workflow requires no feature listed outside the MVP boundary, including
  browser extensions, Discord or Telegram APIs, ChatGPT page control, persistent conversations, or
  Windows Credential Manager.
- Windows Credential Manager remains the first post-MVP implementation task. Every invocation is
  independent of web-chat history and prior invocation state.
- Acceptance criterion A12 is complete.

### D-004 — RESOLVED: TP-09 whitespace-only selection reaches the API

- Status: `RESOLVED`; acceptance impact: `NONE`.
- Severity: `S2` — the required no-selection guard does not show its concise error and permits an
  unnecessary API request.
- Observed by: Project owner on 2026-10-02 during TP-09.
- Observed behavior: invoking `show_full` with no usable selection produced a request whose selected
  text was visually empty.
- Expected: an empty or unusable selection is rejected before credential/API access, stale clipboard
  text is not processed, a concise error is shown, and one safe `invocation_failed` event is logged.
- Safe log evidence: the three latest affected events were `invocation_completed` with API status
  `completed`; their `source_text` values were whitespace-only with lengths 2, 2, and 1. Code-point
  inspection without printing source content identified `CRLF`, `CRLF`, and `LF`, respectively.
- Root cause: the AutoHotkey guard checks only `selectedText = ""`; the CLI uses
  `if not selected_text`; and the request builder rejects only falsey strings. A copied empty line
  therefore supplies one or two newline characters, which are non-empty strings at every boundary.
- Coverage gap: `uv run --no-sync pytest -q -p no:cacheprovider tests/windows/test_clipboard.py
  tests/unit/test_request_builder.py tests/component/test_cli_contract.py` passed 25 tests in 6.98s,
  but those tests cover exact empty strings and structural guard ordering, not whitespace-only text.
- Implemented fix:
  - AutoHotkey rejects captures matching `^\s*$` before setting `PROOFREAD_IT_SOURCE_TEXT` or
    launching the backend;
  - the CLI rejects `selected_text.strip() == ""` before credential access and suppresses unusable
    text from its failure event;
  - the provider-neutral request builder independently rejects whitespace-only input while passing
    valid input unchanged.
- Automated remediation evidence: focused suite 30 passed; full offline suite 161 passed and 2
  deselected; Ruff, mypy, AutoHotkey validation, and `git diff --check` passed. No live API request
  was made during remediation.
- Runtime: the repository AutoHotkey entry point was restarted with the corrected script; PID 82860
  was verified by command line. The unrelated `compose.ahk` process was left unchanged.
- Closure evidence: the Project owner passed the real-hotkey empty-selection retest on 2026-10-02.
  The latest event at `2026-10-02T20:16:48.815+00:00` is one `invocation_failed` event at stage
  `selection` with `SelectionError` and `No selected text was detected.`; `source_text`, logical
  request, API data, and normalized result are all null. D-004 and A7 are resolved; the stale-buffer
  and active-window-change cases remain before TP-09 as a whole can pass.

### D-001 — RESOLVED: TP-03 `copy_final` output fidelity

- Status: `RESOLVED`; acceptance impact: `NONE`.
- Severity: `S2` — an obligatory action fails for the required Unicode test data.
- Observed by: Project owner on 2026-09-26.
- Basis: revision `54528443b4821760952105ace89125a92b114870`, Windows NT
  `10.0.26200.0`, Python `3.14.7`, AutoHotkey `2.0.28`.
- Input: D1 (`I recieved the café menu.` followed by `It look great — thanks!`).
- Passing control: `Ctrl+Alt+E` / `show_full` completed normally for the same selection.
- Failing action: `Ctrl+Alt+Shift+E` / `copy_final` displayed
  `'charmap' codec can't decode character '\xe9' in position 18: character map set to <undefined>`.
- First manual retest after the UTF-8 fix: the codec error disappeared and `é`/`—` were preserved,
  but the single line break between D1 sentences became a blank line in the pasted clipboard text.
- Second manual retest after LF normalization: the extra blank line persisted.
- Third manual retest after canonical CRLF clipboard output: the extra blank line persisted.
- Fourth manual retest after binary UTF-8 stdout: passed on 2026-09-27; `café`, the em dash, and
  exactly one logical line break were preserved.
- Expected: one validated complete `final_text` containing the non-ASCII characters is copied to the
  clipboard without changing its logical line breaks.
- Safe log observation: provider and normalization events for the affected `show_full` and
  `copy_final` invocations were recorded as `invocation_completed`; no source text or raw response
  was printed during diagnosis. This places the visible failure after the workflow log was written.
- Diagnostic reproduction: a no-network PowerShell → uv → Python probe reported stdout encoding
  `cp1251` and failed to write `café —` with `UnicodeEncodeError: 'charmap' codec can't encode
  character '\xe9'`. The same probe with process-local `PYTHONIOENCODING=utf-8` returned `café —`
  with exit code `0`.
- Root cause: the `copy_final` branch crossed two Windows text-output transformations. CP1251 first
  caused the Unicode failure. After UTF-8 was established, `sys.stdout.write()` still translated an
  existing CRLF from validated `final_text` into CRCRLF; the AHK normalizer correctly interpreted
  the extra CR as a second logical line break. `show_full` does not cross this stdout boundary.
- Newline-boundary evidence: immediately after the third failed retest, raw `CF_UNICODETEXT`
  contained CRLFCRLF at offsets 25-28 while the matching logged `normalized_result.final_text`
  contained one CRLF. A no-network Windows probe reproduced `sys.stdout.write(CRLF)` as CRCRLF;
  `sys.stdout.buffer.write(UTF-8 bytes)` emitted exactly one CRLF.
- Implemented fix:
  - `scripts/invoke.ps1` establishes UTF-8 console/output encoding and sets process-local
    `PYTHONIOENCODING=utf-8` only around the selected backend invocation, then restores its previous
    value together with the API-key environment value;
  - `automation/windows/proofread-it.ahk` decodes captured stdout and stderr explicitly as UTF-8,
    normalizes mixed input line endings, and writes every logical line break to `A_Clipboard` as
    canonical Windows CRLF while retaining intentional blank lines;
  - `src/proofread_it/cli.py` writes validated `final_text` as explicit UTF-8 bytes through
    `sys.stdout.buffer`, bypassing Windows text-mode newline translation;
  - `tests/component/test_cli_contract.py` verifies exact raw UTF-8/CRLF stdout bytes;
    `tests/component/test_app_invocation_wrapper.py` and `tests/windows/test_clipboard.py` carry an
    existing CRLF through the remaining PowerShell/AHK path, inspect raw `CF_UNICODETEXT` through
    WinAPI, verify intentional blank lines, and restore the previous clipboard.
- Automated remediation evidence: focused regression `26 passed`; full offline suite `153 passed,
  2 deselected`; Ruff, mypy, AutoHotkey validation, and `git diff --check` passed. No additional live
  API request was made for the fix.
- Closure evidence: the process-boundary and real AHK Clipboard regressions passed, TP-01 was rerun,
  and the Project owner passed TP-03 with the corrected binary-stdout implementation. D-001 is no
  longer a blocker; continue with TP-04.

### D-002 — RESOLVED: TP-04 `Copy result` duplicates multiline breaks

- Status: `RESOLVED`; acceptance impact: `NONE`.
- Severity: `S2` — a required result-copy action changes the validated line structure.
- Observed by: Project owner on 2026-09-27 during TP-04.
- Failing action: click `Copy result` in the `show_full` result window for multiline D1 output.
- Expected: the Windows clipboard contains exactly the validated `final_text`, with one logical line
  break between the two D1 sentences.
- Boundary evidence: immediately after the failure, raw `CF_UNICODETEXT` contained CRCRLF at
  offsets 25-27, while the latest logged `show_full` `normalized_result.final_text` contained one
  CRLF. The defect was therefore in the Tkinter clipboard path, not provider normalization.
- Root cause: `_copy_text` passed an existing CRLF to Tk `clipboard_append`; Tk's Windows clipboard
  layer translated the LF again and emitted CRCRLF.
- Implemented fix: `result_window._copy_text` converts CRLF and lone CR to logical LF before calling
  Tk. Tk then emits one Windows CRLF for each logical break; intentional blank lines remain intact.
- Automated remediation evidence: focused result-window suite `6 passed`; full offline suite
  `154 passed, 2 deselected`; Ruff, mypy, and `git diff --check` passed. No live API request was made
  for the fix.
- Closure evidence: the Project owner passed the combined D-002/D-003 manual retest on 2026-09-27.
  Copying D1 through the result-window button preserved its Unicode characters and exactly one
  logical line break after the window was closed.

### D-003 — RESOLVED: TP-04 copied result disappears when the result window closes

- Status: `RESOLVED`; acceptance impact: `NONE`.
- Severity: `S2` — the required intentional copy can be lost before the user pastes it.
- Observed by: Project owner on 2026-09-27 during TP-04.
- Observed behavior: if the result is pasted while the window remains open, it survives closing the
  window; if the window closes before any paste, the clipboard becomes empty whether or not
  `Copy result` was clicked.
- Expected: after `Copy result`, the validated result remains in the Windows clipboard independently
  of the result window lifetime or whether another application has already requested the data.
- Root cause: Tk owned the clipboard through delayed rendering. Pasting while the Tk process was
  alive forced rendering; otherwise destroying the owner discarded the unpublished data.
- Implemented fix: on Windows, the result path now writes `CF_UNICODETEXT` directly with
  `OpenClipboard`/`EmptyClipboard`/`GlobalAlloc`/`SetClipboardData`. Ownership of the allocated
  Unicode text transfers to Windows, so it survives process exit. The non-Windows Tk fallback still
  flushes its event queue.
- Automated remediation evidence: focused unit plus real Windows ownership regression `8 passed`;
  full offline suite `156 passed, 2 deselected`; Ruff, mypy, and `git diff --check` passed. The real
  regression reads raw clipboard text only after the separate Tk process exits and restores the
  original clipboard afterward. No live API request was made for the fix.
- Closure evidence: the Project owner passed the combined D-002/D-003 manual retest on 2026-09-27:
  after clicking `Copy result`, closing the result window without first pasting, and then pasting
  once, D1 remained in the clipboard with its Unicode characters and exactly one logical line
  break. D-002 and D-003 no longer block acceptance; continue the remaining TP-04 application
  matrix.

## MVP scope traceability

Each included item from `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope` has an automated evidence
path, a manual acceptance path, or both.

| Included MVP item | Automated evidence | Required release evidence |
| --- | --- | --- |
| Windows desktop and AutoHotkey v2 | `tests/windows/test_hotkeys.py`; AHK validation | Windows environment and version recorded below |
| Global hotkeys configured in AHK | `tests/windows/test_hotkeys.py` | Both shipped hotkeys exercised |
| Direct and `#Include` use | `tests/windows/test_hotkeys.py`; `tests/windows/test_ahk_invocation_mutex.py` | Both launch modes exercised |
| Selected-text capture | `tests/windows/test_clipboard.py` | Application matrix completed |
| Clipboard preservation | `tests/windows/test_clipboard.py` | Text, non-text, delayed-copy, and intentional-copy checks completed |
| Python backend | component and unit test suite | Successful real invocation completed |
| Versioned settings and profiles | `tests/unit/test_config.py`; `tests/integration/test_config_files.py` | Shipped configuration used |
| Default `proofread` profile | configuration and request-builder tests | Semantic example matrix completed |
| Application/process/title context | `tests/unit/test_context_policy.py`; workflow tests | Context inspected in successful log events |
| Configured exclusions | context, source-check, CLI, and invocation-failure tests | Blocked title path completed; KeePass path if installed |
| Stateless public-API access | `tests/unit/test_openai_provider.py`; `tests/live/test_openai_api.py` | Real provider result recorded |
| Per-invocation development secret | launcher and wrapper component tests | No key in AHK environment, output, arguments, or logs |
| Structured corrections and final text | parser, provider, workflow, and CLI tests | Both fields inspected in the result window |
| Full-result display | `tests/unit/test_result_window.py` | `show_full` completed |
| Final-text copy | result-window and CLI tests | `copy_final`, selection copy, and button copy completed |
| One in-flight request | concurrency and AHK mutex tests | Same-host and cross-host rejection completed |
| Single-file full logging | logging, workflow, and invocation-failure tests | Successful, blocked, and failed events inspected |
| Basic errors and bounded retries | provider and workflow tests | Required visible failures completed; retry evidence inspected |

## Acceptance-criteria sign-off

These items correspond one-for-one with `spec://proofreader/DESKTOP-ASSISTANT#acceptance` and remain
unchecked until the evidence sections below are complete.

- [x] A1 — Selected non-empty English text can be proofread from each required Windows application
  through a configured global hotkey.
- [x] A2 — Each successful invocation makes one stateless request and returns a validated corrections
  list and final text.
- [x] A3 — Corrections and final text are visible, and only final text can be copied as the result
  action.
- [x] A4 — The default profile corrects errors while preserving meaning, facts, tone, slang,
  approximate length, and English variant.
- [x] A5 — Source application, process, and title reach the request only through the intersection of
  global collection policy and profile permission.
- [x] A6 — An excluded process or title blocks clipboard capture and API access and produces a concise
  notification.
- [x] A7 — An empty or unavailable selection blocks API access and produces a concise error.
- [x] A8 — Clipboard contents are restored unless the selected action intentionally copies final
  text.
- [x] A9 — A second invocation during an active request is rejected with a concise notification.
- [x] A10 — Required configuration, credential, provider, timeout, response, and empty-output errors
  fail visibly without exposing credentials.
- [x] A11 — The single MVP log contains required diagnostic and processing data but no API key or
  authorization header.
- [x] A12 — Repeated invocations neither create nor depend on ChatGPT web-chat history.

## Environment and candidate integrity

- [x] `git rev-parse HEAD` is recorded:
  `91e1ab46e64a3ffd23fc87774d3d764e46a4e436`.
- [x] `git status --short` contains no unexplained product or configuration changes; only the
  expected acceptance-documentation and WAL paths are present.
- [x] `config/settings.json` and `config/profiles.json` are the intended shipped files.
- [x] AutoHotkey v2 path and version are recorded:
  `%USERPROFILE%\AppData\Local\Programs\AutoHotkey\v2\AutoHotkey64.exe`, version `2.0.28`.
- [x] `$env:USERPROFILE\.secrets\openai_token.txt` exists and is readable by the current Windows
  user; its value is not printed or copied into this record.
- [x] The application starts through `scripts/start.ps1` without a credential-bearing parent
  process.

## Application workflow matrix

Follow `docs/windows-acceptance.md`. Use non-empty multiline English text containing non-ASCII
characters and preserve a recognizable clipboard sentinel before each `show_full` invocation.

| Application | `show_full` result | `copy_final` result | Context and log event | Result |
| --- | --- | --- | --- | --- |
| Firefox | [x] | [x] | [x] | `TP-04 PASS; TP-05 PASS` |
| Discord | [x] | [x] | [x] | `TP-04 PASS; TP-05 PASS` |
| Telegram Desktop | [x] | [x] | [x] | `TP-04 PASS; TP-05 PASS` |
| Generic text editor (Notepad++) | [x] | [x] | [x] | `TP-04 PASS; TP-05 PASS` |
| IDE (Visual Studio Code; optional additional evidence) | [x] | [x] | [x] | `TP-04 PASS; TP-05 PASS` |

For every required row:

- [x] TP-04 and TP-05 make exactly one stateless API request for each accepted invocation.
- [x] `show_full` displays corrections and complete final text in a readable, resizable window.
- [x] Text can be selected and copied from both result fields.
- [x] `Copy result` copies the complete final text.
- [x] `copy_final` copies only the validated final text.
- [x] The pre-invocation clipboard is restored after `show_full`.
- [x] The successful TP-04/TP-05 log events contain the expected action, selected text, permitted context,
  logical request, API status, raw response, and normalized result.

## Launch and routing

- [x] Direct launch uses the configured default profile for both shipped hotkeys.
- [x] A temporary external `#Include` host resolves repository paths and behaves equivalently.
- [x] An explicit profile override routes correctly from the temporary host.
- [x] Neither launch mode requires a browser extension, Discord or Telegram API credential,
  ChatGPT page control, or another third-party integration.

## Proofreading semantics

Use short examples where preserving the named property is observable. Record the input and output
or attach their approved local evidence location without including credentials.

| Example | Expected property | Evidence | Result |
| --- | --- | --- | --- |
| D2 — Casual/slang | Correct errors without formalizing the tone or removing valid slang | Project owner manual validation, 2026-09-30 | [x] |
| D3 — Professional | Correct errors while preserving professional register, facts, and meaning | Project owner manual validation, 2026-09-30 | [x] |
| D4 — British English | Preserve British spelling and usage | Project owner manual validation, 2026-09-30 | [x] |
| D5 — American English | Preserve American spelling and usage | Project owner manual validation, 2026-09-30 | [x] |
| D6 — Instruction-like text | Proofread as text without following the embedded instruction or answering it | Project owner manual validation, 2026-09-30 | [x] |
| D7 — Already correct | Return unchanged `final_text` with an empty corrections list | Project owner manual validation, 2026-09-30 | [x] |

- [x] Across all examples, meaning, factual claims, approximate length, formatting, and English
  variant are preserved unless a correction requires a change.
- [x] Instruction-looking selected text is treated as text to proofread rather than an instruction
  that overrides the profile.

## Clipboard and selection boundaries

- [x] Delayed standard-copy completion is accepted within the one-second capture wait.
- [x] An empty or unavailable selection produces a concise error, makes no API request, and appends
  one safe `invocation_failed` event.
- [x] A stale text value already on the clipboard is not processed when selection capture fails.
- [x] Representative non-text clipboard content is restored after `show_full`.
- [x] Intentional `copy_final` output replaces the previous clipboard content only after success.
- [x] Changing the active window during the pre-capture check fails visibly before capture or API
  access.

## Exclusions, concurrency, and failures

- [x] A title containing the separate word `password` is blocked before clipboard capture, secret
  access, or an API request; its log event contains no source text or API data.
- [x] KeePass process check: `NOT AVAILABLE`, accepted by the Project owner on 2026-10-02; automated
  exclusion evidence is retained.
- [x] While one request is active, repeated invocations of both actions are rejected immediately
  without changing the clipboard or creating another API request or invocation event.
- [x] A separate direct or `#Include` host is rejected by the shared mutex while a request is active
  and succeeds after the owner exits.
- [x] Guards are released after both a successful request and a deliberately failed request.
- [x] Missing or empty credentials fail visibly before the API call and append a safe failure event
  when the configured log path is recoverable.
- [x] Authentication, timeout, connection, rate-limit, server, unsupported-model, malformed-response,
  and empty-output behavior is accepted from the passing automated error matrix; any manually
  exercised case is recorded here: missing development credential, accepted by the Project owner
  on 2026-10-10.
- [x] Retry evidence, when a retry occurs, is bounded and contains no request headers, request body,
  API key, or authorization material.

## Provider and sensitive-data review

- [x] A real provider result is recorded using one of these approved paths:
  `scripts/test-live.ps1` or a successful application-workflow row above.
- [x] The result has exactly `corrections` and non-empty `final_text` in the required types.
- [x] Repeated invocations neither create nor depend on web-chat or previous-response state.
- [x] The long-lived AutoHotkey process and an unrelated host child cannot observe the API key.
- [x] Process arguments, console output, application logs, and retry observations contain no API key
  or authorization header.
- [x] The user accepts that the remaining MVP log intentionally contains sensitive selected text,
  context, logical requests, raw responses, and normalized results and will protect or delete it as
  needed.

## Excluded-feature confirmation

- [x] The accepted workflow does not require runtime hotkey configuration in `settings.json`, extra
  profiles, persistent conversations, chat UI, browser extensions, service APIs, OCR, surrounding
  messages, application-specific scraping, a tray application, an installer, cloud sync, direct
  selection replacement, automatic application profiles, manual context notes, local history,
  request queues, simultaneous requests, dynamic output-token limits, or an in-progress indicator.
- [x] Windows Credential Manager is not required for this MVP release.
- [x] Windows Credential Manager is recorded as the first post-MVP implementation task and must
  replace the development plaintext-file secret source while preserving process-local delivery.

## Final acceptance

- [x] Every required application-workflow row passed.
- [x] Every proofreading-semantic row passed.
- [x] Every required clipboard, exclusion, concurrency, failure, provider, and sensitive-data item
  above is checked or has an explicit accepted `NOT AVAILABLE` disposition.
- [x] No unresolved blocking defect, security/privacy conflict, or specification divergence remains.
- [x] The Project owner accepts the Windows MVP.

Decision: `ACCEPTED`

Accepted by: Project owner

Accepted at: `2026-10-10`

Notes: TP-01 through TP-15 passed; A1 through A12 are complete; D-001 through D-004 are resolved;
the KeePass process check retains its explicitly accepted `NOT AVAILABLE` disposition.
