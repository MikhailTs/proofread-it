# Desktop Proofreading Assistant

- Status: `APPROVED`
- Owner: `Project owner`
- Approval authority: `Project owner`
- Supersedes: `NONE`
- Superseded by: `NONE`
- Updated: `2026-10-10`

## Contract Summary {#summary}

This specification governs the Windows MVP of a lightweight desktop tool that proofreads short English text selected in another application. A user invokes a global hotkey, the tool captures the selection and minimal allowed source context, sends one independent request to a public LLM API, validates a machine-readable response, and lets the user inspect the corrections or copy the corrected text without opening a ChatGPT web conversation.

The product is a desktop text-transformation tool, not a chat client. Every request is independent, and the MVP does not maintain conversation state.

## Critical Constraints {#constraints}

- The MVP operates on Windows and uses an AutoHotkey v2 automation layer with a Python backend -> `spec://proofreader/DESKTOP-ASSISTANT#architecture`.
- An invocation from an excluded application or window sends no data to the LLM API -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- API credentials are read directly by the short-lived Python backend from one explicitly configured local source and never written to configuration, process environment, arguments, or logs -> `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`.
- Every model response used by the MVP conforms to the structured result contract -> `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.
- The MVP writes full operational data, source text, request, and response data to one local log file, except credentials and authorization material -> `spec://proofreader/DESKTOP-ASSISTANT#logging`.
- Correctness never depends on prompt caching, model-output determinism, application-specific service APIs, or ChatGPT browser automation -> `spec://proofreader/DESKTOP-ASSISTANT#request-construction` and `spec://proofreader/DESKTOP-ASSISTANT#integration-boundary`.

## Acceptance Criteria {#acceptance}

- [ ] On Windows, the user can select non-empty English text in Firefox, Discord, Telegram Desktop, a text editor, an IDE, or another application that supports standard copy, then invoke proofreading with one configured global hotkey.
- [ ] A successful invocation makes one stateless LLM request and produces a validated result containing a corrections list and final corrected text.
- [ ] The user can see both the corrections and final text and can copy only the final text.
- [ ] The default proofreading profile corrects spelling and grammar while preserving meaning, factual claims, tone, slang, approximate length, and the detected English variant unless correction requires otherwise.
- [ ] The request can include the source application, process name, and active-window title only when both global collection policy and the selected profile permit them.
- [ ] An excluded application or title pattern prevents clipboard capture and prevents any API request; the user receives a concise blocked-action notification.
- [ ] An empty or unavailable selection prevents any API request and produces a concise user-facing error.
- [ ] Clipboard contents are restored after capture unless the selected action intentionally places corrected text on the clipboard.
- [ ] A second invocation while a request is active is rejected with a concise notification.
- [ ] Missing credentials, invalid configuration, authentication failures, timeouts, connection failures, rate limits, server failures, unsupported models, malformed responses, and empty model output fail visibly without exposing credentials.
- [ ] The shipped configuration reads one generic credential directly from Windows Credential Manager; an explicitly selected or legacy schema-version-1 file source remains usable without automatic fallback between sources.
- [ ] The single MVP log contains diagnostic events, captured context, source text, complete logical requests, raw responses, normalized results, and errors, but contains no API key or authorization header.
- [ ] Repeated invocations do not create or depend on ChatGPT web-chat history.

## Product boundary and MVP workflow {#product-workflow}

**Normative:** The MVP MUST implement the following workflow:

1. Receive a configured global-hotkey invocation and identify the active process and window.
2. Apply the exclusion policy before capturing selected text.
3. If allowed, capture the selected text through the standard copy operation and gather configured source metadata.
4. Resolve the explicitly selected profile or the configured default profile.
5. Build a deterministic logical request from the selected text, profile, permitted context, and application settings.
6. Send one stateless request through the LLM API abstraction.
7. Validate and normalize the machine-readable response.
8. Perform the invoked result action: show the full result or copy the final text.

The MVP MUST support short English text and MUST NOT require a visible or persistent chat interface.

**Rationale:** This flow replaces the repeated manual creation of ChatGPT web conversations while remaining usable from arbitrary desktop applications.

**Verification:** End-to-end tests or manual acceptance on Windows demonstrate every acceptance path above in Firefox, Discord, and Telegram Desktop, plus at least one generic text editor.

**Alternatives:** A chat-first interface and a ChatGPT browser-automation workflow were rejected because they add irrelevant state and depend on web UI behavior.

**Reconsider when:** A future product requirement depends on multi-turn editing, long-form document state, or a supported platform that cannot expose standard copy behavior.

**Traceability:** Source proposal `specs/spec-draft.md` sections `SPEC-000`, `SPEC-001`, `SPEC-050`, `SPEC-068`, and `SPEC-069`; code and tests `UNKNOWN`.

## Stateless request lifecycle {#stateless-lifecycle}

**Normative:** Each proofreading request MUST contain all instructions, context, and input needed for that operation. The MVP MUST NOT require `previous_response_id`, a persistent conversation object, previous messages, or any other session-linked model state. Failure or cancellation of one request MUST NOT change the semantic input of a later request.

**Rationale:** Proofreading operations are normally independent; excluding prior conversation state reduces accidental cross-request influence and makes requests reproducible.

**Verification:** Unit tests build equivalent logical requests before and after unrelated invocations, and API-client tests verify that no conversation or previous-response identifier is sent.

**Alternatives:** Persistent and session-linked conversations are deferred beyond the MVP.

**Reconsider when:** An approved feature requires iterative refinement whose value cannot be achieved by an explicit one-off note or a new independent request.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`; source proposal `SPEC-002`; code and tests `UNKNOWN`.

## Component architecture {#architecture}

**Normative:** The Windows MVP MUST consist of:

- a thin AutoHotkey v2 automation layer responsible for global hotkeys, active-window identification, selected-text capture, backend invocation, and clipboard restoration or replacement; and
- a Python backend responsible for configuration and profile loading, context normalization, request construction, API access, response validation and normalization, result presentation, error handling, and logging.

Windows automation, context collection, profile selection, request construction, API access, response normalization, presentation, configuration, and logging MUST remain separate concerns. Proofreading profiles MUST NOT depend on the capture mechanism. Windows-specific behavior SHOULD remain in the automation and adapter boundaries so that the request builder, API layer, profile handling, and response handling remain portable.

The shipped AutoHotkey automation MUST support both direct execution as the application entry point and loading from another AutoHotkey v2 script through `#Include`. Both modes MUST register the same configured hotkeys and preserve the same capture, exclusion, backend-invocation, notification, and clipboard behavior. Included operation MUST resolve repository-owned paths relative to the included automation file rather than the host script or current working directory, and MUST NOT require the host to duplicate internal setup.

**Rationale:** Thin platform adapters and isolated business logic make the core behavior testable and permit later reuse on another desktop platform. Include-compatible automation lets the user compose proofreading hotkeys into an existing personal AutoHotkey script without maintaining a second behavioral implementation.

**Verification:** Architecture review confirms separate modules or interfaces for the listed concerns; core request and response tests run without AutoHotkey, clipboard access, or network access. Windows acceptance launches the automation directly and from a temporary host script located outside the repository that uses `#Include`, then verifies equivalent hotkey routing and repository-path resolution in both modes.

**Alternatives:** A single AutoHotkey implementation and a monolithic Python application were rejected because they couple automation to model behavior and reduce testability. Supporting only direct execution was rejected because it prevents composition with an existing AutoHotkey host script.

**Reconsider when:** A measured implementation constraint shows that the two-process boundary materially harms reliability or distribution.

**Traceability:** Source proposal `SPEC-003`, `SPEC-004`, `SPEC-053`, `SPEC-055`, `SPEC-056`, `SPEC-060`, and `SPEC-065`; code and tests `UNKNOWN`.

## Configuration boundary {#configuration}

**Normative:** The application MUST load two distinct, human-editable JSON files:

- `settings.json` defines operational behavior: schema version, API model and credential source, timeouts and retries, default profile, context allow/exclusion policy, concurrency behavior, logging behavior, and relevant paths.
- `profiles.json` defines model-processing behavior: schema version, task identifier, editable instructions, editing policy, output policy, tone/register guidance, and the subset of globally permitted context fields used by each profile. In schema version `1`, `profiles` MUST be an object keyed by profile name, and each profile MUST contain exactly `task`, `instructions`, and `context_fields`. `task` and `instructions` MUST be non-empty strings. `instructions` MUST contain the complete stable model prompt; editing, output, and tone/register policy MUST be expressed there instead of duplicated as independent control fields. `context_fields` MUST be an array of unique names drawn only from `application_name`, `process_name`, and `window_title`.

Operational settings MUST NOT contain proofreading-specific language rules. Profiles MUST NOT contain capture, credential, concurrency, file-path, or logging mechanics. Each file MUST contain `schema_version`; profiles remain at integer version `1`, while settings versions `1` and `2` are supported. Unsupported versions MUST fail clearly rather than be interpreted silently. Configuration fields MUST be added only for implemented behavior or a demonstrated extension point that would otherwise require a breaking format change.

MVP hotkey bindings and their action/profile routing MUST be configured in the AutoHotkey automation source, not in `settings.json`. A binding MAY omit the profile so that `settings.default_profile` selects it. Editing those declarations is the accepted MVP customization mechanism and MUST NOT require Python source changes.

For legacy settings schema version `1`, `settings.api` MUST contain exactly `model`, `api_key_env`, `timeout_seconds`, `max_output_tokens`, and `retry_count`. `api_key_env` MUST remain a valid non-empty environment-variable name so existing documents continue to validate, but it MUST NOT be used to deliver the credential at runtime; schema version `1` selects the fixed legacy file source defined by `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`.

For settings schema version `2`, `settings.api` MUST contain exactly `model`, `timeout_seconds`, `max_output_tokens`, and `retry_count`, and the root MUST contain `credential`. `credential.source` MUST be either `windows_credential_manager` or `file`. A Windows Credential Manager source MUST contain exactly `source` and a non-empty, trimmed `target`; a file source MUST contain exactly `source`. The shipped settings MUST use schema version `2`, target `ProofreadIt/OpenAIApiKey`, and source `windows_credential_manager`.

In both settings versions, `model` MUST be a non-empty trimmed string; `timeout_seconds` and `max_output_tokens` MUST be positive integers; and `retry_count` MUST be a non-negative integer. The shipped API values MUST remain `gpt-5.6-luna`, `30`, `2048`, and `2`, respectively. The application MUST apply the fixed configured output-token limit to every request. Computing a dynamic output-token limit from the selected-text length is deferred until after MVP.

For schema version `1`, `settings.context` MUST contain exactly `fields` and `exclusions`. `exclusions` MUST contain exactly `process_names` and `window_title_words`, each an array of unique, non-empty strings. Process-name entries are matched case-insensitively against the executable basename; window-title entries are matched case-insensitively as whole words. The shipped configuration MUST initially contain `KeePass.exe` in `process_names` and `password` in `window_title_words`. Users MAY add, remove, or edit entries in either list without changing source code.

**Rationale:** Separating operation from language policy keeps configuration understandable and prevents profile selection from changing technical permissions.

**Verification:** Configuration-schema tests load both supported settings versions and the shipped `proofread` profile, accept the two exact schema-version-2 credential forms, map schema version `1` to the legacy file source, reject unsupported versions and invalid or cross-boundary fields, and identify the failing field in the user-facing configuration error. Static or Windows automation tests verify that AHK bindings route actions with either the configured default profile or an explicit profile without Python source changes.

**Alternatives:** A single combined configuration file and profile-specific code paths were rejected because they blur authority and increase duplication. Runtime hotkey routing in `settings.json` is deferred beyond the MVP because editing the AutoHotkey bindings is sufficient for the intended user.

**Reconsider when:** Configuration growth makes two files less understandable than a versioned hierarchical format or when profiles require independently distributable packages.

**Traceability:** Source proposal `SPEC-005` through `SPEC-007`, `SPEC-009`, `SPEC-016` through `SPEC-018`, and `SPEC-061` through `SPEC-064`; `config/profiles.json`; profile-loading code and tests `UNKNOWN`.

## API access and credentials {#api-access}

**Normative:** The backend MUST access the LLM through a small provider-facing API abstraction. `settings.json` MUST select the model, credential source, request timeout, output-token limit when used, and retry count. The short-lived Python backend MUST resolve the API key directly according to `spec://proofreader/DESKTOP-ASSISTANT#credential-storage` and pass it directly to the provider adapter.

The MVP provider adapter MUST use the official OpenAI Python SDK and its Responses API. It MUST map the provider-neutral instruction, structured-output contract, and serialized dynamic input to distinct Responses API fields; request strict JSON Schema output; set `store` to `false`; apply the configured model, timeout, output-token limit, and SDK retry count; and omit conversation and previous-response identifiers.

The long-lived AutoHotkey automation, any external script that loads it through `#Include`, the PowerShell launchers, and the `uv` parent process MUST NOT read or receive the key. Starting the automation and invoking explicitly selected live tests MUST NOT require a credential-bearing parent launcher. The key and authorization material MUST NOT be stored in repository files or `settings.json`, placed in a process environment, included in the logical request, exposed in process arguments or output, or written to logs.

The core workflow MUST use a public LLM API and MUST NOT drive the ChatGPT web UI or reproduce private browser requests.

**Rationale:** Isolating the provider SDK reduces coupling. Direct credential resolution in the one short-lived Python process avoids exposing the key to PowerShell, `uv`, ambient environment inspection, a long-lived automation host, or unrelated child processes.

**Verification:** API-client unit tests use a fake provider. Credential-resolver tests use sentinel file and native-adapter fakes to cover both sources and all failure modes without reading a real user credential. Launcher tests demonstrate that AutoHotkey, PowerShell, `uv`, arguments, output, and process environments contain no sentinel key. A separately selected Windows integration test uses a unique temporary generic credential and deletes it in all outcomes. Log tests find neither the sentinel API key nor authorization material.

**Alternatives:** A credential-bearing AutoHotkey or PowerShell process, environment-variable delivery, automatic fallback between stores, direct SDK calls throughout the application, keys in project configuration, command-line key arguments, and ChatGPT DOM automation are rejected.

**Reconsider when:** The application becomes cross-platform, organization-managed credentials are required, or a distribution model can provide a narrower application identity than the current Windows user.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`, `docs/development.md`; source proposal `SPEC-007`, `SPEC-008`, `SPEC-050`, and `SPEC-055`; Project owner decisions on 2026-09-02, 2026-09-09, and 2026-10-10; launchers, provider adapter, and credential tests.

## Post-MVP credential storage {#credential-storage}

**Normative:** Settings schema version `2` MUST explicitly select exactly one credential source. `windows_credential_manager` MUST read a `CRED_TYPE_GENERIC` credential with the configured target from the current Windows user's credential set by calling `CredReadW` directly from Python. The shipped target MUST be `ProofreadIt/OpenAIApiKey`. The returned native allocation MUST be released with `CredFree` in every outcome. Credentials written by the supplied management command MUST use `CRED_PERSIST_LOCAL_MACHINE`.

The `file` source and every schema-version-1 settings document MUST read `$env:USERPROFILE\.secrets\openai_token.txt` directly from Python. The file MUST NOT be committed and SHOULD be readable only by the current Windows user. A missing `USERPROFILE`, missing or unreadable source, empty credential, malformed generic-credential blob, or Windows Credential Manager error MUST fail before an API request. The selected source MUST NOT fall back to another source.

Credential resolution MUST occur only after configuration, concurrency, source-exclusion, profile, and non-empty-selection checks pass. The secret MAY exist in Python-managed memory and the provider SDK for the duration required by the request, but MUST NOT be copied into a process environment, command line, configuration document, log, logical request, or user-visible diagnostic. The supplied credential-management command MUST accept the key only through a hidden interactive prompt and MUST support setting/replacing and removing the configured generic credential. Manual creation through the Windows Credential Manager UI MUST remain supported.

**Rationale:** Windows Credential Manager protects the secret at rest for the current Windows user, while direct Python access minimizes the number of processes and transport surfaces that observe it. Explicit source selection prevents a forgotten plaintext file from silently defeating the chosen store.

**Verification:** Unit tests inject file-system and native-store adapters to cover source selection, decoding, cleanup, missing and empty values, and no-fallback behavior. CLI and launcher tests prove that credential access occurs after all preflight gates and that no key enters environment variables, arguments, output, or logs. Management-command tests cover create, replace, and remove without accepting a command-line secret. An explicitly selected Windows test creates a unique temporary generic credential, reads it through the production adapter, and removes it in `finally`.

**Alternatives:** PowerShell retrieval with child-process environment injection, automatic file fallback, project configuration secrets, persistent environment variables, and automatic migration or deletion of the legacy file are rejected.

**Reconsider when:** A non-Windows platform is supported, Windows provides an application-scoped secret facility suitable for this distribution model, or managed enterprise identity replaces a user-held API key.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#testability`; Project owner decision on 2026-10-10; Python credential resolver and management CLI, credential-free PowerShell launchers, and credential tests.

## Proofreading profile contract {#proofreading-profile}

**Normative:** The MVP MUST ship with a generic profile named `proofread` and use it when no profile is explicitly selected. Its editable instructions MUST require the model to:

- correct spelling and grammar, including punctuation and capitalization when required for correctness;
- preserve meaning and factual claims;
- preserve the original tone, register, slang, idioms, and community or technical terminology unless they are incorrect or confusing;
- make only the minimum necessary changes, avoid style-only rewriting, and keep length, structure, formatting, and line breaks approximately unchanged unless a correction requires otherwise;
- preserve the source English variant instead of silently converting between British and American conventions;
- avoid translating, summarizing, answering, or executing the selected text; and
- return the correction list and final corrected text required by `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.

The profile MUST express editing policy declaratively rather than require a separate implementation code path. The complete accepted wording MUST reside in `profiles.proofread.instructions` in `config/profiles.json`, and request construction MUST use that value verbatim without a source-code fallback copy. `profiles.proofread.task` MUST be `proofread_english`, and `profiles.proofread.context_fields` MUST list `application_name`, `process_name`, and `window_title`; actual transmission remains limited to the intersection required by `spec://proofreader/DESKTOP-ASSISTANT#context-policy`. Additional named style or application profiles, including `casual`, `professional`, work-specific, Discord-specific, and grammar-only profiles, are outside the MVP and MUST NOT be required for MVP acceptance.

**Rationale:** Explicit editing constraints produce more predictable proofreading than a broad tone label and keep policy editable without source changes.

**Verification:** Profile-schema tests load `proofread` with the fixed task, prompt, and context-field list; request-builder snapshots contain the prompt verbatim and each required policy; semantic acceptance examples cover casual, professional, slang-heavy, British, and American inputs.

**Alternatives:** Free-form prompts embedded in source code and automatic application-selected profiles were rejected for the MVP. Shipping separate casual, professional, application-specific, or grammar-only profiles is deferred until usage demonstrates that the generic `proofread` profile is insufficient.

**Reconsider when:** Real usage demonstrates a need for separate Discord, work, translation, rewriting, or grammar-only profiles.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#configuration`; source proposal `SPEC-009`, `SPEC-016` through `SPEC-023`, `SPEC-037`, and `SPEC-038`; `config/profiles.json`; request-builder and profile-schema code and tests `UNKNOWN`.

## Context collection, minimization, and exclusions {#context-policy}

**Normative:** At hotkey time, the automation layer MUST obtain the active process identity and active-window title locally, normalize them into an optional structured source object, and evaluate configured application and title-pattern exclusions before copying selected text. If an exclusion matches, the application MUST NOT capture or transmit the selected text, MUST NOT call the LLM API, and MUST notify the user that processing is blocked for the active source.

The schema-version-1 exclusion lists and matching rules are defined by `spec://proofreader/DESKTOP-ASSISTANT#configuration`. When more than one rule matches, the first matching process-name rule takes precedence over title-word rules, and otherwise list order determines the reported match. Missing process or title values do not match. A blocked invocation MUST use the existing local logging boundary and MUST NOT read or require the API credential.

For an allowed source, `settings.json` defines the maximum context fields the application may collect, and the selected profile defines the subset that may be transmitted. The intersection of those policies is the only source context included in the logical request. The MVP context fields are friendly application name, process name, and active-window title. Missing or unusable values MUST be represented as `null` or omitted and MUST NOT fail the request.

The application MUST NOT automatically collect or send whole webpages, URLs, chat histories, HTML, unrelated UI text, clipboard history, arbitrary surrounding screen content, or deeper application metadata. A data-driven mapping SHOULD convert known executable names such as `firefox.exe`, `Discord.exe`, and `Telegram.exe` to friendly names, with deterministic fallback for unknown applications.

**Rationale:** Small explicit metadata can improve register selection while reducing unnecessary disclosure; fail-closed exclusions prevent requests from sensitive applications.

**Verification:** Unit tests cover known and unknown process mapping, empty titles, global/profile policy intersection, case-insensitive executable-basename exclusions, case-insensitive whole-word title exclusions and their non-matches, and deterministic rule precedence. Component and Windows-boundary tests prove that a blocked invocation is logged without source text, does not read a credential, and never invokes clipboard capture or the API backend.

**Alternatives:** Sending selected text without metadata from excluded applications was explicitly rejected; broad screen scraping and implicit context collection were rejected as disproportionate and fragile.

**Reconsider when:** Measured quality improvements justify an explicit, reviewed collector for browser, accessibility, or application-specific metadata.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#request-construction`; source proposal `SPEC-010` through `SPEC-015`, `SPEC-025`, `SPEC-045` through `SPEC-048`, `SPEC-066`, and `SPEC-067`; authorized human decision on 2026-09-01; code and tests `UNKNOWN`.

## Request construction and trust boundary {#request-construction}

**Normative:** Request construction MUST be a pure or near-pure operation with the conceptual interface:

```python
build_request(text, profile, source_context, settings) -> request
```

The logical request MUST place stable profile instructions and the structured-output contract before dynamic per-request input. Dynamic input MAY contain only the selected text, permitted normalized source context, and an optional user-supplied note when that post-MVP feature exists. Selected text, source metadata, and manual notes MUST be treated as untrusted data to transform or interpret, not as authoritative instructions that override the profile contract. Source metadata MAY influence tone, register, and degree of rewriting but MUST NOT be treated as factual content of the selected message.

For the MVP, the provider-neutral logical request MUST have the following exact typed structure. `ProofreadingResultSchema` is the single canonical schema defined by `spec://proofreader/DESKTOP-ASSISTANT#structured-result`; it is referenced here rather than redefined.

```text
LogicalRequest := {
  parts: [
    { kind: "instructions", text: ProfileInstructions },
    { kind: "output_contract", schema: ProofreadingResultSchema },
    {
      kind: "input",
      media_type: "application/json",
      text: SerializedDynamicInput
    }
  ]
}

ProfileInstructions := the verbatim profiles.<profile-name>.instructions string
SerializedDynamicInput := a JSON serialization of DynamicInput
```

The dynamic input object MUST have exactly the two top-level fields shown below before serialization. Context members marked `?` are optional; when present, their values MUST be a string or `null`.

```text
DynamicInput := {
  source_context: {
    application_name?: string | null,
    process_name?: string | null,
    window_title?: string | null
  },
  selected_text: non-empty string
}
```

`source_context` MUST always be an object and MUST contain only fields permitted by both global settings and the selected profile. A permitted but unavailable value MUST be `null`, while a disallowed field MUST be omitted. `selected_text` MUST preserve the captured non-empty string exactly. The builder MUST create the `input` part's `text` with a JSON serializer from structured values and MUST NOT interpolate dynamic values into instructions or hand-build JSON. A provider adapter MAY map the three parts to provider-specific instruction, structured-output, and input fields, but MUST preserve their separation and authority order. Regardless of provider capabilities, the local response boundary MUST enforce `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.

Given identical selected text, profile, normalized context, and settings, the builder MUST produce the same logical request structure. Model output need not be byte-for-byte deterministic. Stable instruction prefixes SHOULD remain consistent to improve reproducibility and permit provider-side caching, but correctness MUST NOT depend on caching.

**Rationale:** A deterministic, explicit request boundary is independently testable, auditable, and resistant to accidental mixing of instructions with application metadata.

**Verification:** Snapshot or structural unit tests compare repeated builds; verify the exact ordered three-part envelope, output schema, and verbatim profile prompt; reject undeclared context fields; verify policy-intersection filtering and `null` handling; round-trip quotes, backslashes, Unicode, line breaks, and instruction-looking selected text through JSON serialization; preserve stable/dynamic authority ordering; and verify that no local data is read implicitly by the builder.

**Alternatives:** Request construction inside the API client, implicit local-data reads, free-form dynamic prompt concatenation, hand-built JSON, and correctness dependent on provider prompt caching were rejected.

**Reconsider when:** A provider API requires a different representation while preserving the same logical contract, or approved conversational behavior introduces explicit state.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`; source proposal `SPEC-026` through `SPEC-028`, `SPEC-051` through `SPEC-053`, and `SPEC-066`; `config/profiles.json`; request-builder code and tests `UNKNOWN`.

## Structured model result {#structured-result}

**Normative:** The canonical `ProofreadingResultSchema` for every MVP model request and accepted response is:

```json
{
  "type": "object",
  "properties": {
    "corrections": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "final_text": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "corrections",
    "final_text"
  ],
  "additionalProperties": false
}
```

`corrections` MUST be an array of strings and MAY be empty when no correction is needed. `final_text` MUST be a string and MUST contain the complete usable result, including unchanged input when no correction is needed. The API/response boundary MUST validate the response before exposing a normalized internal result to UI or clipboard operations. Missing fields, wrong types, invalid structured data, or an empty `final_text` MUST be handled as malformed API responses and MUST NOT overwrite the clipboard with a partial result. The raw response MAY be retained only for logging and diagnostics.

**Rationale:** A small enforced structure reliably separates explanatory corrections from the text that may be copied automatically.

**Verification:** Parser tests accept valid objects with populated and empty correction lists; reject missing, additional, mistyped, malformed, and empty-final-text cases; and verify UI and clipboard consumers receive only normalized results.

**Alternatives:** Parsing free-form prose and deferring structured output until after the MVP were explicitly rejected.

**Reconsider when:** The UI requires source spans, typed edits, confidence, localization, multiple result shapes, or explicit result-schema versioning and migration.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#request-construction`; source proposal `SPEC-023`, `SPEC-024`, `SPEC-033`, and `SPEC-056`; Project owner decisions on 2026-09-01 and 2026-09-03; code and tests `UNKNOWN`.

## Selected-text and clipboard behavior {#clipboard}

**Normative:** For an allowed invocation, the automation layer MUST preserve the existing clipboard, issue the active application's standard copy command, wait for a clipboard update with a bounded timeout, and pass a non-empty textual selection to the backend. It MUST NOT assume an instantaneous update or reuse stale clipboard text as a selection fallback.

If no usable selection is obtained, the application MUST make no API request and MUST show a concise error such as `No selected text was detected.` After successful capture, the previous clipboard MUST be restored, including non-text formats where feasible. Restoration MUST NOT occur when the invoked result action intentionally copies corrected text.

**Rationale:** Clipboard-based capture works across target applications but requires explicit stale-data and restoration safeguards.

**Verification:** Automation tests or Windows manual tests cover delayed copy, no selection, stale clipboard, text and representative non-text clipboard restoration, and intentional final-text copy.

**Alternatives:** Processing existing clipboard text when no selection is detected and direct replacement of the original selection are outside the MVP.

**Reconsider when:** Accessibility APIs provide a more reliable cross-application selection interface or users explicitly request clipboard fallback/direct replacement.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`; source proposal `SPEC-030` through `SPEC-032`; code and tests `UNKNOWN`.

## Hotkeys, actions, and result presentation {#interaction}

**Normative:** Hotkeys MUST be configurable by editing clear binding declarations in the AutoHotkey automation script and MUST route a result action and an optional explicit profile name to the backend. An invocation without an explicit profile, whether from a hotkey, per-invocation wrapper, backend CLI, or source-check CLI, MUST use `settings.default_profile`; an explicit profile MUST take precedence. Hotkey bindings and routing MUST NOT be required in `settings.json` for the MVP. The MVP MUST expose:

- `show_full`: display the corrections and final corrected text; and
- `copy_final`: place only normalized `final_text` on the clipboard.

The initial defaults SHOULD be `Ctrl+Alt+E` for `show_full` and `Ctrl+Alt+Shift+E` for `copy_final`. The presentation MAY be a minimal Python window, a Tkinter dialog, or a development console plus clipboard behavior, but it MUST expose both result fields for `show_full` and MUST NOT bind the long-term architecture to that presentation technology. A dynamic in-progress indicator shown after hotkey handling begins and before a result or error is available is deferred until after MVP.

**Rationale:** Two explicit actions cover inspection and fast replacement workflows without requiring a sophisticated GUI. Omitting the profile lets the shipped hotkeys follow the configured default while retaining named-profile overrides.

**Verification:** CLI, wrapper, and source-check tests verify that omitted profiles resolve to `settings.default_profile` and explicit profiles take precedence. Windows acceptance tests invoke each AHK-configured hotkey in both direct and `#Include` modes, verify default-profile/action routing and an explicit-profile override, inspect both fields for `show_full`, and compare clipboard contents for `copy_final`.

**Alternatives:** Runtime hotkey configuration through `settings.json`, direct selection replacement, automatic application-based profile selection, a dynamic in-progress indicator, tray UI, and a full chat UI are deferred beyond the MVP.

**Reconsider when:** User testing supports a single combined interaction or justifies direct replacement and richer result controls.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`; source proposal `SPEC-029`, `SPEC-033` through `SPEC-038`; code and tests `UNKNOWN`.

## Concurrency and duplicate invocation {#concurrency}

**Normative:** The MVP MUST permit at most one active request. A hotkey invocation received while a request is active MUST be rejected without capturing a new selection or changing the clipboard and MUST produce a concise notification. The automation/backend boundary MUST also prevent accidental double activation through a debounce, single-instance mutex, backend lock, or an equivalently testable mechanism.

**Rationale:** A single in-flight request avoids ambiguous clipboard restoration and result ordering.

**Verification:** Concurrency tests hold one fake request open, invoke both actions repeatedly, and verify exactly one API call, one result, unchanged clipboard state for rejected invocations, and a visible rejection notification.

**Alternatives:** Queuing and multiple simultaneous requests are outside the MVP.

**Reconsider when:** Measured demand for batching or slow provider latency outweighs the additional clipboard and presentation complexity.

**Traceability:** Source proposal `SPEC-039`, `SPEC-040`, `SPEC-058`, and `SPEC-059`; code and tests `UNKNOWN`.

## Errors, timeouts, and retries {#errors}

**Normative:** The application MUST distinguish and handle missing credentials, invalid configuration, authentication failure, network timeout, connection failure, rate limiting, transient server failure, unsupported model, malformed structured response, and empty output. User-facing errors MUST be concise and MUST NOT expose credentials; the full available diagnostic detail MUST be logged subject to `spec://proofreader/DESKTOP-ASSISTANT#logging`.

Timeout and retry count MUST be configurable. The OpenAI adapter MUST use the official SDK's built-in bounded retry mechanism with the configured `retry_count`. The accepted SDK retry policy includes connection failures, request timeouts, HTTP 409 conflicts, rate limits, and temporary server failures. Invalid credentials, invalid configuration, malformed requests, unsupported models, and invalid model responses MUST NOT be retried automatically.

**Rationale:** Conservative retry behavior improves recovery without multiplying deterministic failures or hiding configuration problems.

**Verification:** API fake tests exercise every error category, exact retry limits, no-retry categories, concise notification behavior, and credential redaction.

**Alternatives:** Unbounded retries and retrying every failure were rejected.

**Reconsider when:** Provider-specific idempotency and retry guidance permits a more precise policy or offline queuing is approved.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`; source proposal `SPEC-041` and `SPEC-042`; code and tests `UNKNOWN`.

## MVP logging policy {#logging}

**Normative:** The MVP MUST enable logging and MUST write one local log file containing all available application-level diagnostic and processing information for each invocation, including timestamp, selected profile and action, model name, source application, process name, window title, matched context policy, selected source text, complete logical request, request duration and API status, raw model response, normalized result, retry events, and error detail.

The log MUST NOT contain the API key, authorization headers, or unrelated environment-variable contents. A blocked invocation MUST be logged with the locally observed application/window identity and matched exclusion rule; because text capture and API access do not occur, it has no source text, request, or response to log. `settings.json` MUST configure the log file path. Disabling logging, field-level redaction, and separate request/response files are deferred.

The documentation and example configuration MUST warn that the MVP log contains potentially sensitive text and context and must be protected and deleted by the user according to their needs.

**Rationale:** Full single-file logging is simple to implement and preserves evidence useful for early debugging and evaluation, at the explicit cost of local privacy and disk usage.

**Verification:** Integration tests perform successful, blocked, retried, and failed requests and assert the required fields are present in the one configured file; sentinel credential tests assert secrets and authorization headers are absent.

**Alternatives:** Metadata-only default logging and separate diagnostic/request/response files were rejected for the MVP. Configurable field-level logging, redaction, rotation, retention, and split files are post-MVP candidates.

**Reconsider when:** The MVP leaves personal use, logs grow materially, sensitive-data handling requirements change, or a debugging/evaluation workflow needs separate machine-readable request records.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`; source proposal `SPEC-043` and `SPEC-044`; authorized human decision on 2026-09-01; code and tests `UNKNOWN`.

## External integration boundary {#integration-boundary}

**Normative:** The basic workflow MUST NOT require Discord, Telegram, browser, or other third-party service APIs; browser extensions; account permissions for source applications; ChatGPT page control; DOM automation; OCR; surrounding-message capture; or sophisticated application-specific UI scraping. Firefox context MAY use its normal window title. Discord and Telegram context MAY use only the generic process identity and active-window title in the MVP.

Future application-specific collectors MUST remain optional and MUST be introduced in this order of preference: generic process/window metadata, deterministic parsing of already available metadata, official local accessibility/UI interfaces, and only then a justified deeper integration. The core selection workflow MUST continue to function without any such integration.

**Rationale:** The generic local boundary keeps the tool application-agnostic, avoids external account permissions, and limits fragile dependencies.

**Verification:** End-to-end acceptance succeeds with no browser extension and no Discord or Telegram API credentials; dependency review finds no ChatGPT browser-automation integration.

**Alternatives:** Service-specific APIs and deep UI scraping were rejected for the MVP.

**Reconsider when:** Quality measurements show that a specific optional integration provides substantial improvement and its security/privacy behavior receives explicit approval.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#context-policy`; source proposal `SPEC-015`, `SPEC-046` through `SPEC-050`, and `SPEC-067`; code and tests `UNKNOWN`.

## Testability boundaries {#testability}

**Normative:** Context normalization, request construction, credential resolution, API access, and response normalization MUST each be independently testable. Unit tests MUST NOT require AutoHotkey, the Windows clipboard, live network access, or a real API credential to cover those components. The default test run MUST NOT read `$env:USERPROFILE\.secrets\openai_token.txt` or the shipped Windows Credential Manager target. Native credential-store access MUST be isolated behind a replaceable adapter. The API abstraction MUST support a fake implementation, and UI/clipboard consumers MUST receive normalized results rather than parse raw provider responses.

Live API tests MUST be separately marked, excluded from the default test run, and selected explicitly. They MUST resolve the credential directly in their Python process through `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`. A native Windows Credential Manager integration test MUST also be selected explicitly, use a unique temporary target and sentinel value, avoid the shipped target, and remove its credential in every outcome.

Windows integration coverage MUST separately exercise active-window observation, clipboard capture/restoration, hotkey routing, and single-request concurrency.

**Rationale:** Pure core components provide fast deterministic evidence while narrow Windows integration tests cover the platform boundary.

**Verification:** The project test runner can execute core unit tests offline with the development secret file and shipped generic credential absent; component tests demonstrate fake API injection and normalized result consumption; the default run excludes live API and native-store tests; Windows acceptance commands are documented and reproducible. Launcher tests prove their processes remain credential-free, and resolver tests use only injected sentinel sources without exposing them in output.

**Alternatives:** End-to-end-only verification was rejected because it makes provider and clipboard failures hard to isolate.

**Reconsider when:** The implementation language or packaging model changes while preserving equivalent isolation and evidence.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `docs/development.md`; source proposal `SPEC-052` through `SPEC-056`; Project owner decisions on 2026-09-02, 2026-09-09, and 2026-10-10; credential, launcher, and live-test tests.

## Explicit MVP scope {#mvp-scope}

**Normative:** The MVP includes Windows desktop support; AutoHotkey v2 global hotkeys configured in the automation source; direct execution and `#Include` use of the shipped automation; selected-text capture; clipboard preservation; a Python backend; versioned `settings.json` and `profiles.json`; the `proofread` profile; application/process detection; active-window-title capture; configured exclusions; stateless public-API access; development-time per-invocation secret loading from `$env:USERPROFILE\.secrets\openai_token.txt` into only the selected Python backend process tree, never the long-lived AutoHotkey process; structured corrections plus final text; full-result display; final-text copy; one in-flight request; full single-file logging; and basic errors and bounded retries.

The MVP explicitly excludes hotkey routing through `settings.json`; separate casual, professional, work-specific, application-specific, grammar-only, or other additional profiles; persistent conversations; chat UI; browser extensions; Discord and Telegram APIs; OCR; surrounding-message capture; sophisticated application-specific UI scraping; tray application; installer; cloud synchronization; direct replacement of selected text; Windows Credential Manager; automatic application-based profile selection; manual context notes; local history; request queues; multiple simultaneous requests; dynamic output-token limits derived from selected-text length; and a dynamic in-progress indicator between hotkey handling and the terminal result or error.

Windows Credential Manager integration MUST be the first post-MVP implementation task and is defined by `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`: it becomes the shipped default while the explicitly selected and schema-version-1 legacy file source remains available. All other items excluded from the MVP are candidates only; this document does not authorize or require their implementation.

**Rationale:** The boundary contains the smallest end-to-end workflow that replaces manual web-chat proofreading while retaining inspectable results, privacy controls, and diagnostic evidence.

**Verification:** The historical release checklist maps every included MVP item to a passing test or recorded Windows manual acceptance. Post-MVP credential acceptance separately verifies the default Windows Credential Manager source and retained explicit file mode.

**Alternatives:** A richer initial GUI, application-specific integrations, and Windows Credential Manager within the MVP were rejected to keep the first implementation focused.

**Reconsider when:** The credential-storage increment is accepted; other post-MVP candidates may then be prioritized independently.

**Traceability:** All decisions in this specification; `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`; source proposal `SPEC-057` through `SPEC-059`; Project owner decisions on 2026-09-02, 2026-09-09, and 2026-10-10; code and tests `UNKNOWN`.

## Cross-Cutting Invariants {#invariants}

- One invocation maps to at most one independent LLM request -> `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle` and `spec://proofreader/DESKTOP-ASSISTANT#concurrency`.
- Technical collection permission and profile usage permission are separate; transmitted context is their intersection -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- Exclusion decisions occur before selection capture and cause zero API transmission -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- Dynamic text and source metadata cannot override stable proofreading and output instructions -> `spec://proofreader/DESKTOP-ASSISTANT#request-construction`.
- Only a validated normalized result may reach result presentation or clipboard output -> `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.
- Credentials never enter configuration, logical requests, model-visible input, or logs -> `spec://proofreader/DESKTOP-ASSISTANT#api-access` and `spec://proofreader/DESKTOP-ASSISTANT#logging`.
- Credentials never enter PowerShell, command arguments, or process environments, and the configured source never falls back implicitly -> `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`.
- Platform automation remains outside profile and model-processing policy -> `spec://proofreader/DESKTOP-ASSISTANT#architecture` and `spec://proofreader/DESKTOP-ASSISTANT#configuration`.

## Semantic changelog {#changelog}

- 2026-09-01 — authorized human request — `spec://proofreader/DESKTOP-ASSISTANT#summary`, `spec://proofreader/DESKTOP-ASSISTANT#constraints`, `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`, `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle`, `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, `spec://proofreader/DESKTOP-ASSISTANT#errors`, `spec://proofreader/DESKTOP-ASSISTANT#logging`, `spec://proofreader/DESKTOP-ASSISTANT#integration-boundary`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`, `spec://proofreader/DESKTOP-ASSISTANT#invariants`:
  `NONE -> initial DRAFT proposal consolidated from specs/spec-draft.md and the user's clarifications`; reason: `establish one reviewable protocol-compliant product contract`; invalidates: `NONE (initial specification; implementation and tests are UNKNOWN)`; review: `NONE`.
- 2026-09-01 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#summary`, `spec://proofreader/DESKTOP-ASSISTANT#constraints`, `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`, `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle`, `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, `spec://proofreader/DESKTOP-ASSISTANT#errors`, `spec://proofreader/DESKTOP-ASSISTANT#logging`, `spec://proofreader/DESKTOP-ASSISTANT#integration-boundary`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`, `spec://proofreader/DESKTOP-ASSISTANT#invariants`:
  `DRAFT proposal -> APPROVED normative specification`; reason: `explicit approval by the declared Project owner in the current conversation`; invalidates: `pre-approval specification verification evidence; implementation and test conformance remain UNKNOWN`; review: `NONE`.
- 2026-09-02 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`:
  `named runtime environment variable with unspecified local secret source; Credential Manager only deferred -> fixed MVP-development file source with process-local injection; credential-free default tests and explicit live tests; Credential Manager required as the first post-MVP task`; reason: `limit ambient credential exposure on the local development machine without blocking MVP work`; invalidates: `previous semantic verification for the affected anchors; launcher, backend, and live-test implementation remain UNKNOWN`; review: `NONE`.
- 2026-09-03 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`:
  `abstract profile and request requirements with no stored default prompt -> fixed schema-version-1 profile fields, accepted generic proofreading policy, an exact ordered three-part logical request with serialized untrusted input, and one canonical strict result schema`; reason: `make the base request reproducible and store its editable prompt before request-builder implementation`; invalidates: `previous semantic verification for the affected anchors and any profile-schema, request-builder, or response-schema snapshots; profile loading, request building, and response parsing remain UNKNOWN`; review: `NONE`.
- 2026-09-04 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#errors`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`:
  `provider and API settings unspecified; retry policy provider-neutral; dynamic output sizing and in-progress feedback unclassified -> official OpenAI Python SDK Responses adapter with shipped model gpt-5.6-luna, 30-second timeout, fixed 2048-token output limit, two SDK-managed retries, and both dynamic output sizing and a dynamic in-progress indicator explicitly deferred until after MVP`; reason: `establish an implementable sending boundary while retaining two requested improvements outside MVP scope`; invalidates: `previous semantic verification for the affected anchors and API configuration, provider, retry, and interaction artifacts`; review: `NONE`.
- 2026-09-05 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`:
  `hotkeys configured through settings.json, additional profiles merely optional, and direct-launch-only AHK behavior unspecified -> hotkeys configured by editing AHK bindings, named casual/professional and similar profiles explicitly outside MVP, and equivalent direct and #Include automation behavior required with repository-relative path resolution`; reason: `match the accepted personal AutoHotkey workflow and keep the MVP profile surface minimal`; invalidates: `previous semantic verification for the affected anchors, AutoHotkey path/bootstrap behavior, automation tests, Windows acceptance documentation, and the MVP release checklist`; review: `NONE`.
- 2026-09-09 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`:
  `development launcher injects the API key into the long-lived AutoHotkey application process tree -> a short-lived per-invocation wrapper injects the key only into the selected Python backend process tree, while the AutoHotkey automation and any external host never receive it`; reason: `prevent a long-lived personal AutoHotkey host and its unrelated child processes from inheriting the API credential`; invalidates: `credential launcher and wrapper implementation, AutoHotkey backend invocation, credential-scope tests, development and Windows acceptance documentation, and prior credential-related manual acceptance`; review: `NONE`.
- 2026-09-10 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`:
  `configured exclusions with unspecified schema, matching rules, and shipped values -> editable process-name and window-title-word lists with deterministic case-insensitive matching, initially containing KeePass.exe and password, enforced before clipboard capture without credential access`; reason: `provide an immediately useful privacy denylist that remains user-configurable`; invalidates: `settings schema and shipped configuration, context-policy implementation, AutoHotkey invocation order, blocked-event logging, configuration and Windows-boundary tests, and customization documentation`; review: `NONE`.
- 2026-09-17 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`:
  `hotkeys require explicit profile names and invocation boundaries reject omitted profiles -> profile omission selects settings.default_profile while an explicit name remains an override`; reason: `make the configured default effective for ordinary desktop and direct backend use`; invalidates: `AutoHotkey bindings and invocation commands, backend and source-check CLIs, credential wrapper, routing tests, and desktop documentation`; review: `NONE`.
- 2026-09-17 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`:
  `MVP settings include clipboard and UI policies and clipboard restoration may be disabled by configuration -> MVP settings do not require those policies and captured clipboard contents are restored unless the result action copies corrected text`; reason: `Project owner removed the unused settings requirements`; invalidates: `prior configuration and clipboard acceptance evidence; current settings, automation, and clipboard tests require revalidation`; review: `NONE`.
- 2026-10-10 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#constraints`, `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#credential-storage`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`, `spec://proofreader/DESKTOP-ASSISTANT#invariants`:
  `a PowerShell wrapper reads the fixed development file and injects its value through one backend process environment; Windows Credential Manager must later replace the file -> shipped settings schema version 2 selects a generic Windows Credential Manager credential read directly by Python, explicit and schema-version-1 legacy file modes remain available without automatic fallback, and credentials never pass through PowerShell, uv arguments, or process environments`; reason: `reduce runtime credential exposure while retaining a deliberate compatibility path`; invalidates: `credential and configuration specification evidence; settings, config loader, credential reader, launchers, live tests, failure logging, credential tests, development documentation, Windows acceptance documentation, and credential-related MVP checklist future-state statements`; review: `NONE`.
