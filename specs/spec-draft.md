# Desktop Proofreading Assistant — Specification

Version: 0.1  
Platform: Windows desktop  
Status: Draft

---

<a id="SPEC-000"></a>
## SPEC-000 — Purpose

The application is a lightweight Windows desktop assistant for proofreading and lightly editing short English texts through an LLM API.

Its primary use case is proofreading text selected in arbitrary desktop applications, especially:

- Firefox;
- Discord;
- Telegram Desktop;
- text editors;
- IDEs;
- other applications where text can be selected and copied.

The application must avoid the current workflow of creating a new ChatGPT web conversation for every proofreading request.

The default interaction model is **not a chat UI**. Each proofreading request is treated as an independent text-processing operation.

---

<a id="SPEC-001"></a>
## SPEC-001 — Primary user workflow

The default workflow is:

1. The user selects text in any desktop application.
2. The user presses a global hotkey.
3. The application copies the selected text.
4. The application gathers lightweight contextual metadata about the source application.
5. The application combines:
   - the selected text;
   - the selected processing profile;
   - automatically collected context;
   - application-wide settings.
6. The application sends a stateless request to the LLM API.
7. The application receives:
   - a list of proposed corrections;
   - the final corrected version.
8. The result is shown to the user and/or copied to the clipboard according to the configured action.

---

<a id="SPEC-002"></a>
## SPEC-002 — Stateless request model

The default request model is stateless.

Each request must be independently understandable by the model and must contain all instructions and context required for the current operation.

The application must not require:

- `previous_response_id`;
- a persistent conversation object;
- chat history;
- a visible chat interface.

Persistent or session-linked conversations may be added later as an optional mode, but they are outside the MVP.

Rationale:

- proofreading requests are normally independent;
- old context can unintentionally influence later edits;
- stateless requests are easier to debug and reproduce;
- there is no conversational UI requiring continuity.

---

<a id="SPEC-003"></a>
## SPEC-003 — Architecture overview

The application should initially consist of two cooperating components:

### Automation layer

Recommended implementation: AutoHotkey v2.

Responsibilities:

- register global hotkeys;
- identify the active window;
- copy selected text;
- invoke the application backend;
- optionally paste or restore clipboard contents.

### Application/backend layer

Recommended initial implementation: Python.

Responsibilities:

- load configuration;
- load processing profiles;
- normalize contextual metadata;
- build the API request;
- call the LLM API;
- parse the response;
- display or copy results;
- handle errors;
- optionally log diagnostic information.

The automation layer should remain thin and contain as little business logic as possible.

---

<a id="SPEC-004"></a>
## SPEC-004 — Separation of concerns

The implementation should keep the following concerns separate:

1. Windows automation.
2. Context collection.
3. Profile selection.
4. Prompt/request construction.
5. API access.
6. Response parsing.
7. Result presentation.
8. Configuration.
9. Logging.

A processing profile must not depend on how the text was technically captured.

Global application settings must not contain proofreading-specific language rules.

---

<a id="SPEC-005"></a>
## SPEC-005 — Configuration files

The application should use at least two human-editable configuration files:

- `settings.json`
- `profiles.json`

Their responsibilities must remain distinct.

`settings.json` describes **how the application operates**.

`profiles.json` describes **how the model should process text**.

---

<a id="SPEC-006"></a>
## SPEC-006 — `settings.json` responsibility

`settings.json` contains application-wide operational configuration.

It may contain:

- API configuration;
- model selection;
- timeout values;
- default profile;
- clipboard behavior;
- UI behavior;
- context collection policy;
- logging policy;
- file paths;
- concurrency policy;
- retry policy.

It must not contain proofreading-specific instructions such as grammar rules, desired tone, or rewriting policy.

---

<a id="SPEC-007"></a>
## SPEC-007 — API settings

The API section of `settings.json` should support at least:

- model name;
- API key source;
- timeout;
- optional output-token limit;
- optional retry count.

Example conceptual structure:

```json
{
  "api": {
    "model": "MODEL_NAME",
    "api_key_env": "OPENAI_API_KEY",
    "timeout_seconds": 30
  }
}
```

The API key should not be stored directly in `settings.json`.

---

<a id="SPEC-008"></a>
## SPEC-008 — API credential storage

For the MVP, the API key should be obtained from an environment variable.

Example:

```text
OPENAI_API_KEY
```

A later version may use Windows Credential Manager or another OS-native secret store.

Secrets must not be written to logs.

---

<a id="SPEC-009"></a>
## SPEC-009 — Default profile

`settings.json` should specify a default processing profile.

Example:

```json
{
  "default_profile": "proofread"
}
```

If no explicit profile is selected by a hotkey or UI action, the default profile is used.

---

<a id="SPEC-010"></a>
## SPEC-010 — Context collection settings

`settings.json` should define which contextual signals the program is technically allowed to collect.

Initial signals:

- executable/process name;
- application name if derivable;
- active window title.

Possible later signals:

- browser page title;
- browser URL;
- chat/channel/workspace name;
- application-specific metadata.

Example:

```json
{
  "context": {
    "include_application": true,
    "include_process_name": true,
    "include_window_title": true
  }
}
```

---

<a id="SPEC-011"></a>
## SPEC-011 — Context minimization

Only context useful for language, tone, register, or interpretation should be sent to the model.

The application should not automatically send:

- entire webpages;
- complete chat histories;
- HTML source;
- unrelated UI text;
- large clipboard histories;
- arbitrary surrounding screen content.

Context collection should prefer small, explicit metadata fields.

---

<a id="SPEC-012"></a>
## SPEC-012 — Source context structure

Internally, context should be normalized into a structured object similar to:

```json
{
  "source": {
    "app": "Discord",
    "process_name": "Discord.exe",
    "window_title": "Discord | #general | GURPS",
    "page_title": null,
    "chat_name": "#general",
    "server_or_workspace": "GURPS",
    "message_kind": "reply"
  }
}
```

Not every field must be populated.

Unknown values should be represented as `null` or omitted.

---

<a id="SPEC-013"></a>
## SPEC-013 — Application detection

The program should attempt to derive a friendly application identifier from the active process.

Examples:

- `firefox.exe` → `Firefox`
- `Discord.exe` → `Discord`
- `Telegram.exe` → `Telegram Desktop`

This mapping should be data-driven where practical rather than hardcoded throughout the codebase.

---

<a id="SPEC-014"></a>
## SPEC-014 — Window title capture

The active window title should be captured at the moment the hotkey is invoked.

The title may be included in the request because it can provide useful context such as:

- website/page title;
- Discord server/channel;
- Telegram conversation;
- document name.

The application must tolerate applications whose window title is empty, generic, or unstable.

---

<a id="SPEC-015"></a>
## SPEC-015 — Application-specific context extraction

Application-specific parsing may be added incrementally.

Examples:

- Discord: infer server/channel names from window title or accessibility metadata.
- Telegram: infer current chat name.
- Firefox: infer page title and possibly current URL.

This functionality is optional for the MVP.

The MVP must work with only:

- selected text;
- active application;
- active window title.

---

<a id="SPEC-016"></a>
## SPEC-016 — Profile responsibility

`profiles.json` contains processing modes.

A profile defines:

- task type;
- model instructions;
- editing policy;
- output format;
- tone/register policy;
- context fields relevant to that profile.

Profiles should be declarative rather than implemented as separate code paths where possible.

---

<a id="SPEC-017"></a>
## SPEC-017 — Initial profiles

The initial design should support at least these conceptual profiles:

- `proofread`
- `proofread_discord`
- `proofread_work`

Possible future profiles:

- `rewrite_natural`
- `translate_to_english`
- `grammar_only`
- `proofread_telegram`
- `proofread_forum`
- `shorten`
- `make_more_formal`

Only one generic proofreading profile is required for the earliest MVP.

---

<a id="SPEC-018"></a>
## SPEC-018 — Profile task field

Each profile should have an internal task identifier.

Example:

```json
{
  "task": "proofread_english"
}
```

The task identifier is primarily for application logic, diagnostics, and future extensibility.

It does not by itself replace model instructions.

---

<a id="SPEC-019"></a>
## SPEC-019 — Proofreading instructions

The default proofreading profile should instruct the model to:

- correct spelling;
- correct grammar;
- preserve meaning;
- preserve factual accuracy;
- preserve tone unless otherwise specified;
- avoid unnecessary rewriting;
- identify the corrections made;
- provide the final corrected text.

The instruction text should be editable without changing source code.

---

<a id="SPEC-020"></a>
## SPEC-020 — Editing policy

Profiles should support explicit editing policy rather than relying only on a broad tone label.

Potential fields include:

```json
{
  "editing": {
    "preserve_original_tone": true,
    "allow_rephrasing": "limited",
    "preserve_length": "approximately",
    "preserve_slang": true,
    "preserve_meaning": true,
    "preserve_factual_claims": true,
    "english_variant": "preserve"
  }
}
```

The exact JSON schema may be simplified during implementation.

---

<a id="SPEC-021"></a>
## SPEC-021 — Tone and register policy

A profile may include a contextual description of the expected communication environment.

Examples:

### Discord

Informal conversational English is appropriate. Preserve casual phrasing and community-specific terminology unless it is grammatically incorrect or confusing.

### Work communication

Prefer natural professional English. Avoid introducing unnecessary formality or corporate language.

The application should generally preserve the tone already present in the source text.

---

<a id="SPEC-022"></a>
## SPEC-022 — English variant preservation

The proofreading profile should avoid silently converting between English variants.

Examples:

- British spelling should normally remain British.
- American spelling should normally remain American.

A future profile setting may explicitly request a particular variant.

Default:

```json
{
  "english_variant": "preserve"
}
```

---

<a id="SPEC-023"></a>
## SPEC-023 — Output format

The default proofreading response should contain:

1. a concise list of proposed corrections;
2. the final corrected version.

This mirrors the current manual proofreading workflow.

A profile should be able to select other output modes, for example:

- corrections + final text;
- final text only;
- explanation only;
- structured machine-readable response.

---

<a id="SPEC-024"></a>
## SPEC-024 — Machine-readable response

The implementation should be designed so that the model response will be requested in a structured format.

This is particularly useful for a workflow such as:

- show corrections in the result window;
- copy only the final corrected text automatically.

---

<a id="SPEC-025"></a>
## SPEC-025 — Profile-specific context policy

A profile may specify which of the context fields collected by the application should actually be sent to the model.

Example:

```json
{
  "context": {
    "application": true,
    "window_title": true,
    "chat_name": true,
    "page_title": false
  }
}
```

This creates two distinct levels:

- `settings.json`: what the program may collect;
- `profiles.json`: what a given processing mode uses.

---

<a id="SPEC-026"></a>
## SPEC-026 — Request construction

A request should contain two conceptual layers:

### Stable instructions

Task rules that are the same for every request using a profile.

Examples:

- proofreading rules;
- editing constraints;
- output format.

### Per-request input

Dynamic information:

- source application;
- window title;
- inferred source context;
- optional manual note;
- selected text.

The exact API representation may use separate instruction and input fields.

---

<a id="SPEC-027"></a>
## SPEC-027 — Suggested request content

A normalized request may conceptually look like:

```text
Context:
- App: Discord
- Window title: Discord | #general | GURPS
- Message type: reply
- Tone hint: casual

Text:
<selected text>
```

The stable proofreading instructions should be supplied separately from this per-request context where the API permits it.

---

<a id="SPEC-028"></a>
## SPEC-028 — Context should influence tone, not facts

Source metadata should primarily help the model infer:

- formality;
- conversational register;
- appropriate degree of rewriting;
- whether casual or technical wording should be preserved.

The model must not treat inferred context such as a window title as authoritative factual content of the message.

---

<a id="SPEC-029"></a>
## SPEC-029 — Global hotkeys

The application should expose one or more global hotkeys.

Initial proposal:

- `Ctrl+Alt+E` — proofread and show full result;
- `Ctrl+Alt+Shift+E` — proofread and copy final corrected text;
- optional future hotkeys for additional profiles.

Exact hotkeys must be configurable.

---

<a id="SPEC-030"></a>
## SPEC-030 — Selected text capture

When invoked, the automation layer should:

1. save the current clipboard contents;
2. send the standard copy command to the active application;
3. wait for clipboard update;
4. retrieve the selected text;
5. invoke the backend.

The program should not assume that the clipboard update is instantaneous.

---

<a id="SPEC-031"></a>
## SPEC-031 — Clipboard preservation

By default, the application should preserve the clipboard contents that existed before the request.

The workflow may temporarily overwrite the clipboard to capture selected text.

After capture, the previous clipboard should be restored unless:

- the selected action intentionally places corrected text in the clipboard;
- the user disables clipboard restoration.

The implementation should preserve non-text clipboard formats where feasible.

---

<a id="SPEC-032"></a>
## SPEC-032 — No-selection handling

If the program cannot obtain usable selected text, it should not send an API request.

It should display a brief error such as:

```text
No selected text was detected.
```

Possible future fallback:

- use current textual clipboard contents;
- ask the user whether to process clipboard text.

This fallback is outside the initial MVP.

---

<a id="SPEC-033"></a>
## SPEC-033 — Result actions

The program should support at least two result actions:

### Show full result

Display:

- proposed corrections;
- final corrected text.

### Copy final text

Place only the final corrected text in the clipboard.

A future version may support direct replacement of the original selection.

---

<a id="SPEC-034"></a>
## SPEC-034 — Result window

A post-MVP GUI may use a small always-on-top result window.

Suggested elements:

- source application/context summary;
- corrections section;
- final corrected text section;
- `Copy final`;
- `Copy full`;
- `Retry`;
- `Close`.

Optional later actions:

- `Replace selection`;
- `Change profile`;
- `Re-run with note`;
- `More natural`;
- `More formal`.

---

<a id="SPEC-035"></a>
## SPEC-035 — MVP user interface

The earliest MVP does not require a sophisticated GUI.

Acceptable initial presentation methods include:

- simple Python window;
- minimal Tkinter dialog;
- console during development plus clipboard output.

The implementation should not make the long-term UI architecture depend on the MVP presentation method.

---

<a id="SPEC-036"></a>
## SPEC-036 — Manual context note

A future UI may allow the user to attach a short one-off note to a request.

Examples:

- `This is a sarcastic reply.`
- `This is a message to technical support.`
- `Keep the wording deliberately blunt.`

Manual notes should be optional and should never be required for normal proofreading.

---

<a id="SPEC-037"></a>
## SPEC-037 — Multiple profiles and hotkey routing

Different hotkeys may select different profiles.

Example:

```text
Ctrl+Alt+E       → generic proofreading
Ctrl+Alt+D       → Discord-style proofreading
Ctrl+Alt+W       → professional/work proofreading
```

The backend should receive the profile name explicitly.

Profile-to-hotkey mapping may be stored in `settings.json`.

---

<a id="SPEC-038"></a>
## SPEC-038 — Automatic profile selection

Automatic profile selection based on active application may be considered later.

Example:

- Discord → `proofread_discord`
- Outlook → `proofread_work`

For the MVP, explicit hotkeys or a default profile are preferred because they are deterministic and easier to debug.

---

<a id="SPEC-039"></a>
## SPEC-039 — Request concurrency

The application must define behavior when a hotkey is pressed while a request is already running.

Recommended MVP behavior:

- allow only one active request at a time;
- ignore or reject duplicate invocation with a short notification.

A later version may support a small request queue.

---

<a id="SPEC-040"></a>
## SPEC-040 — Duplicate invocation protection

The automation layer should guard against accidental double hotkey activation.

Possible implementation:

- debounce hotkeys for a short interval;
- backend lock file or single-instance mutex;
- reject a new request while an identical one is in flight.

---

<a id="SPEC-041"></a>
## SPEC-041 — API errors

The application should handle at least:

- missing API key;
- authentication failure;
- network timeout;
- connection failure;
- rate limiting;
- malformed API response;
- unsupported model;
- empty model output.

The user-facing error should be concise.

Detailed diagnostic information may be written to logs.

---

<a id="SPEC-042"></a>
## SPEC-042 — Retry behavior

Automatic retries should be conservative.

Potentially retryable errors:

- transient network failures;
- rate limits;
- temporary server errors.

Non-retryable errors:

- invalid credentials;
- invalid configuration;
- malformed request;
- unsupported model.

Retry count and timeout should be configurable.

---

<a id="SPEC-043"></a>
## SPEC-043 — Logging

Logging should be optional.

Diagnostic logs may include:

- timestamp;
- selected profile;
- source application;
- request duration;
- API status;
- error details;
- model name.

By default, logs should avoid storing the full selected text or model output unless explicitly enabled.

---

<a id="SPEC-044"></a>
## SPEC-044 — Privacy-sensitive logging

Configuration should independently control whether logs store:

- source text;
- corrected text;
- window titles;
- application identifiers.

The safest default is:

- diagnostic metadata: enabled;
- input/output text logging: disabled.

---

<a id="SPEC-045"></a>
## SPEC-045 — Sensitive context filtering

The application should have a mechanism to suppress context collection for particular applications or title patterns.

Examples:

- password managers;
- banking applications;
- private administrative tools.

This may initially be implemented as an exclusion list in `settings.json`.

---

<a id="SPEC-046"></a>
## SPEC-046 — Browser context

For Firefox, the MVP may use the browser window title as page context.

A future version may obtain additional browser-specific metadata, such as:

- page title;
- current URL.

Any browser integration should be optional and should not be required for the core application to function.

---

<a id="SPEC-047"></a>
## SPEC-047 — Discord context

For Discord, useful context may include:

- Discord application identity;
- server name;
- channel/thread name;
- whether the text is probably a reply or standalone message.

The initial implementation may rely only on information available in the active window title.

Deeper UI parsing should be deferred until there is evidence that it materially improves proofreading quality.

---

<a id="SPEC-048"></a>
## SPEC-048 — Telegram context

For Telegram Desktop, useful context may include:

- Telegram application identity;
- current conversation name if available;
- generic message context.

The implementation should not depend on Telegram APIs or bot integration.

---

<a id="SPEC-049"></a>
## SPEC-049 — No dependency on service APIs

The application should not require Discord, Telegram, or browser service APIs for the basic workflow.

The assistant operates on text selected by the user and local desktop context.

This keeps the tool:

- application-agnostic;
- local in interaction;
- easy to extend;
- independent of third-party account permissions.

---

<a id="SPEC-050"></a>
## SPEC-050 — No browser UI automation dependency

The system should not depend on driving the ChatGPT web UI.

In particular, it should not require:

- opening ChatGPT pages;
- finding a specific existing chat;
- reproducing private web requests;
- DOM automation of ChatGPT;
- browser extensions tied to ChatGPT UI internals.

The LLM interaction should use the public API.

---

<a id="SPEC-051"></a>
## SPEC-051 — Prompt caching compatibility

Stable instructions should be kept as consistent as practical between requests.

This improves reproducibility and may permit API-side prompt caching where supported.

Dynamic context and selected text should appear after the stable instruction prefix.

Caching must be treated as an optimization only; application correctness must not depend on it.

---

<a id="SPEC-052"></a>
## SPEC-052 — Deterministic configuration

Given:

- the same selected text;
- the same profile;
- the same captured context;
- the same settings;

the request builder should produce the same logical request structure.

This is important for testing and debugging.

Model output itself is not required to be byte-for-byte deterministic.

---

<a id="SPEC-053"></a>
## SPEC-053 — Testable request builder

Prompt/request construction should be implemented as a pure or near-pure function where practical.

Example conceptual interface:

```python
build_request(
    text,
    profile,
    source_context,
    settings
) -> request
```

This component should be independently unit-testable without:

- invoking AutoHotkey;
- using the clipboard;
- making network requests.

---

<a id="SPEC-054"></a>
## SPEC-054 — Testable context normalization

Raw Windows information should be normalized before it reaches prompt construction.

Example:

```text
Raw:
process = "Discord.exe"
title   = "Discord | #gurps-guns | GURPS"

Normalized:
app = "Discord"
window_title = "Discord | #gurps-guns | GURPS"
```

Normalization should have unit tests for known applications and fallback behavior.

---

<a id="SPEC-055"></a>
## SPEC-055 — API abstraction

The API client should be isolated behind a small interface.

Example conceptual operation:

```python
proofread(request) -> response
```

or more generally:

```python
generate(request) -> response
```

This prevents Windows automation, UI, and configuration code from depending directly on SDK-specific details.

---

<a id="SPEC-056"></a>
## SPEC-056 — Response normalization

The raw model response should be converted into an internal result structure.

Example:

```json
{
  "corrections": [
    "..."
  ],
  "final_text": "...",
  "raw_response": "..."
}
```

UI and clipboard operations should consume this normalized structure rather than parse the API response independently.

---

<a id="SPEC-057"></a>
## SPEC-057 — MVP scope

The MVP should include:

- Windows desktop support;
- AutoHotkey global hotkey;
- selected text capture;
- clipboard preservation;
- Python backend;
- `settings.json`;
- `profiles.json`;
- one proofreading profile;
- application/process detection;
- active window title capture;
- stateless API call;
- corrections + final corrected text;
- ability to copy the final text;
- basic error handling.

---

<a id="SPEC-058"></a>
## SPEC-058 — Explicitly out of MVP scope

The following should not be required for the first version:

- persistent conversations;
- chat UI;
- browser extension;
- Discord API integration;
- Telegram API integration;
- OCR;
- automatic reading of surrounding chat messages;
- sophisticated application-specific UI scraping;
- tray application;
- installer;
- cloud synchronization;
- direct replacement of selected text;
- Windows Credential Manager integration;
- multiple simultaneous requests.

---

<a id="SPEC-059"></a>
## SPEC-059 — Post-MVP capabilities

Candidate post-MVP features:

- multiple profiles;
- configurable hotkeys;
- tray icon;
- structured model output;
- direct `Replace selection`;
- application-aware profile selection;
- manual context notes;
- Firefox URL acquisition;
- richer Discord/Telegram context;
- local history;
- Windows Credential Manager;
- request queue;
- session-linked editing mode;
- additional actions such as translation and rewriting.

---

<a id="SPEC-060"></a>
## SPEC-060 — Suggested initial project layout

A possible initial layout:

```text
proofreader/
├── ahk/
│   └── proofread.ahk
├── app/
│   ├── main.py
│   ├── config.py
│   ├── context.py
│   ├── request_builder.py
│   ├── api_client.py
│   ├── response_parser.py
│   └── ui.py
├── config/
│   ├── settings.json
│   └── profiles.json
├── tests/
│   ├── test_context.py
│   ├── test_request_builder.py
│   └── test_response_parser.py
└── logs/
```

The exact layout may change, but the logical separation should remain.

---

<a id="SPEC-061"></a>
## SPEC-061 — Example `settings.json` shape

Illustrative only:

```json
{
  "api": {
    "model": "MODEL_NAME",
    "api_key_env": "OPENAI_API_KEY",
    "timeout_seconds": 30,
    "retry_count": 1
  },

  "default_profile": "proofread",

  "hotkeys": {
    "proofread_show": "Ctrl+Alt+E",
    "proofread_copy": "Ctrl+Alt+Shift+E"
  },

  "context": {
    "include_application": true,
    "include_process_name": true,
    "include_window_title": true
  },

  "clipboard": {
    "restore_previous_contents": true
  },

  "ui": {
    "show_result_window": true,
    "always_on_top": true
  },

  "logging": {
    "enabled": true,
    "store_input_text": false,
    "store_output_text": false
  }
}
```

---

<a id="SPEC-062"></a>
## SPEC-062 — Example `profiles.json` shape

Illustrative only:

```json
{
  "proofread": {
    "task": "proofread_english",

    "instructions": [
      "Correct spelling and grammar.",
      "Preserve meaning and factual accuracy.",
      "Preserve the original tone.",
      "Avoid unnecessary rewriting."
    ],

    "editing": {
      "preserve_original_tone": true,
      "allow_rephrasing": "limited",
      "preserve_length": "approximately",
      "preserve_slang": true,
      "english_variant": "preserve"
    },

    "output": {
      "include_corrections": true,
      "include_final_text": true
    },

    "context": {
      "application": true,
      "window_title": true
    }
  }
}
```

The schema should remain intentionally small until additional profiles demonstrate a real need for more fields.

---

<a id="SPEC-063"></a>
## SPEC-063 — Configuration schema evolution

Configuration files should include a schema/version field once the format becomes stable enough to require migration.

Example:

```json
{
  "schema_version": 1
}
```

The application should fail clearly on unsupported configuration versions rather than silently misinterpret them.

---

<a id="SPEC-064"></a>
## SPEC-064 — Conservative schema design

Do not create configuration fields merely because they might be useful someday.

A field should be added when:

- it supports an implemented feature; or
- it represents a clear extension point that would otherwise require breaking the configuration format.

The initial configuration should remain readable and manually editable.

---

<a id="SPEC-065"></a>
## SPEC-065 — Portability

Although the initial target is Windows, the backend should avoid unnecessary Windows-specific dependencies.

Windows-specific operations should primarily remain in:

- AutoHotkey;
- the context/clipboard adapter layer.

The model interaction, configuration, request builder, and response parser should be portable enough to reuse later on another desktop platform.

---

<a id="SPEC-066"></a>
## SPEC-066 — User control over submitted data

Before sending a request, the system should be able to determine exactly which fields will be transmitted.

The request builder should not implicitly read unrelated local data.

All transmitted context should originate from:

- selected text;
- configured context collectors;
- explicitly selected profile;
- optional user-supplied note.

---

<a id="SPEC-067"></a>
## SPEC-067 — Principle for future application-specific integrations

Application-specific integrations should only be added when they provide substantial additional context quality.

Preferred order:

1. generic process/window metadata;
2. deterministic parsing of already available metadata;
3. official local accessibility/UI interfaces;
4. deeper integration only if justified.

Fragile screen scraping should be avoided where possible.

---

<a id="SPEC-068"></a>
## SPEC-068 — Success criteria for MVP

The MVP is successful if the user can:

1. select an English message in Firefox, Discord, or Telegram Desktop;
2. invoke one global hotkey;
3. receive a proofreading result without opening ChatGPT manually;
4. see both corrections and the corrected version;
5. copy the corrected version for immediate use;
6. perform repeated requests without creating ChatGPT web-chat history entries;
7. obtain tone-aware results using at least the source application and active window title.

---

<a id="SPEC-069"></a>
## SPEC-069 — Design principle

The product should be treated as a **desktop text transformation tool backed by an LLM**, not as a miniature chat client.

This principle should guide MVP decisions unless a later feature explicitly requires conversational state.
