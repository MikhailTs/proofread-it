# Desktop Proofreading Assistant

- Status: `APPROVED`
- Owner: `Project owner`
- Approval authority: `Project owner`
- Supersedes: `NONE`
- Superseded by: `NONE`
- Updated: `2026-09-01`

## Contract Summary {#summary}

This specification governs the Windows MVP of a lightweight desktop tool that proofreads short English text selected in another application. A user invokes a global hotkey, the tool captures the selection and minimal allowed source context, sends one independent request to a public LLM API, validates a machine-readable response, and lets the user inspect the corrections or copy the corrected text without opening a ChatGPT web conversation.

The product is a desktop text-transformation tool, not a chat client. Every request is independent, and the MVP does not maintain conversation state.

## Critical Constraints {#constraints}

- The MVP operates on Windows and uses an AutoHotkey v2 automation layer with a Python backend -> `spec://proofreader/DESKTOP-ASSISTANT#architecture`.
- An invocation from an excluded application or window sends no data to the LLM API -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- API credentials are read from an environment variable and never written to configuration or logs -> `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
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
- [ ] Clipboard contents are restored after capture unless the selected action intentionally places corrected text on the clipboard or restoration is disabled.
- [ ] A second invocation while a request is active is rejected with a concise notification.
- [ ] Missing credentials, invalid configuration, authentication failures, timeouts, connection failures, rate limits, server failures, unsupported models, malformed responses, and empty model output fail visibly without exposing credentials.
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

**Rationale:** Thin platform adapters and isolated business logic make the core behavior testable and permit later reuse on another desktop platform.

**Verification:** Architecture review confirms separate modules or interfaces for the listed concerns; core request and response tests run without AutoHotkey, clipboard access, or network access.

**Alternatives:** A single AutoHotkey implementation and a monolithic Python application were rejected because they couple automation to model behavior and reduce testability.

**Reconsider when:** A measured implementation constraint shows that the two-process boundary materially harms reliability or distribution.

**Traceability:** Source proposal `SPEC-003`, `SPEC-004`, `SPEC-053`, `SPEC-055`, `SPEC-056`, `SPEC-060`, and `SPEC-065`; code and tests `UNKNOWN`.

## Configuration boundary {#configuration}

**Normative:** The MVP MUST load two distinct, human-editable JSON files:

- `settings.json` defines operational behavior: schema version, API model and credential source, timeouts and retries, default profile, hotkey routing, clipboard policy, UI policy, context allow/exclusion policy, concurrency behavior, logging behavior, and relevant paths.
- `profiles.json` defines model-processing behavior: schema version, task identifier, editable instructions, editing policy, output policy, tone/register guidance, and the subset of globally permitted context fields used by each profile.

Operational settings MUST NOT contain proofreading-specific language rules. Profiles MUST NOT contain capture, credential, concurrency, file-path, or logging mechanics. Each file MUST contain `schema_version`; the MVP version is integer `1`. Unsupported versions MUST fail clearly rather than be interpreted silently. Configuration fields MUST be added only for implemented behavior or a demonstrated extension point that would otherwise require a breaking format change.

**Rationale:** Separating operation from language policy keeps configuration understandable and prevents profile selection from changing technical permissions.

**Verification:** Configuration-schema tests accept supported minimal examples, reject unsupported versions and invalid cross-boundary fields, and identify the failing field in the user-facing configuration error.

**Alternatives:** A single combined configuration file and profile-specific code paths were rejected because they blur authority and increase duplication.

**Reconsider when:** Configuration growth makes two files less understandable than a versioned hierarchical format or when profiles require independently distributable packages.

**Traceability:** Source proposal `SPEC-005` through `SPEC-007`, `SPEC-009`, `SPEC-016` through `SPEC-018`, and `SPEC-061` through `SPEC-064`; code and tests `UNKNOWN`.

## API access and credentials {#api-access}

**Normative:** The backend MUST access the LLM through a small provider-facing API abstraction. `settings.json` MUST select the model, environment-variable name, request timeout, output-token limit when used, and retry count. For the MVP, the API key MUST be read from the named environment variable; `OPENAI_API_KEY` is the default example. The key and authorization material MUST NOT be stored in `settings.json`, included in the logical request, or written to logs.

The core workflow MUST use a public LLM API and MUST NOT drive the ChatGPT web UI or reproduce private browser requests.

**Rationale:** Isolating the provider SDK and keeping credentials out of files and logs reduces coupling and accidental secret disclosure.

**Verification:** API-client unit tests use a fake provider; configuration and log tests scan outputs for a sentinel API key and authorization header and find neither.

**Alternatives:** Direct SDK calls throughout the application, plaintext keys in configuration, ChatGPT DOM automation, and Windows Credential Manager are rejected for the MVP; an OS-native secret store remains a future option.

**Reconsider when:** The application requires multiple providers, organization-managed credentials, or an approved OS-native secret store.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#configuration`; source proposal `SPEC-007`, `SPEC-008`, `SPEC-050`, and `SPEC-055`; code and tests `UNKNOWN`.

## Proofreading profile contract {#proofreading-profile}

**Normative:** The MVP MUST ship with a generic profile named `proofread` and use it when no profile is explicitly selected. Its editable instructions MUST require the model to:

- correct spelling and grammar;
- preserve meaning and factual claims;
- preserve the original tone, register, slang, and community or technical terminology unless they are incorrect or confusing;
- avoid unnecessary rewriting and keep length approximately unchanged;
- preserve the source English variant instead of silently converting between British and American conventions;
- return the correction list and final corrected text required by `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.

The profile MUST express editing policy declaratively rather than require a separate implementation code path. Additional profiles are not required by the MVP.

**Rationale:** Explicit editing constraints produce more predictable proofreading than a broad tone label and keep policy editable without source changes.

**Verification:** Profile-schema tests load `proofread`; request-builder snapshots contain each required policy; semantic acceptance examples cover casual, professional, slang-heavy, British, and American inputs.

**Alternatives:** Free-form prompts embedded in source code and automatic application-selected profiles were rejected for the MVP.

**Reconsider when:** Real usage demonstrates a need for separate Discord, work, translation, rewriting, or grammar-only profiles.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#configuration`; source proposal `SPEC-009`, `SPEC-016` through `SPEC-023`, `SPEC-037`, and `SPEC-038`; code and tests `UNKNOWN`.

## Context collection, minimization, and exclusions {#context-policy}

**Normative:** At hotkey time, the automation layer MUST obtain the active process identity and active-window title locally, normalize them into an optional structured source object, and evaluate configured application and title-pattern exclusions before copying selected text. If an exclusion matches, the application MUST NOT capture or transmit the selected text, MUST NOT call the LLM API, and MUST notify the user that processing is blocked for the active source.

For an allowed source, `settings.json` defines the maximum context fields the application may collect, and the selected profile defines the subset that may be transmitted. The intersection of those policies is the only source context included in the logical request. The MVP context fields are friendly application name, process name, and active-window title. Missing or unusable values MUST be represented as `null` or omitted and MUST NOT fail the request.

The application MUST NOT automatically collect or send whole webpages, URLs, chat histories, HTML, unrelated UI text, clipboard history, arbitrary surrounding screen content, or deeper application metadata. A data-driven mapping SHOULD convert known executable names such as `firefox.exe`, `Discord.exe`, and `Telegram.exe` to friendly names, with deterministic fallback for unknown applications.

**Rationale:** Small explicit metadata can improve register selection while reducing unnecessary disclosure; fail-closed exclusions prevent requests from sensitive applications.

**Verification:** Unit tests cover known and unknown process mapping, empty titles, global/profile policy intersection, application exclusions, title-pattern exclusions, and proof that blocked invocations never invoke clipboard capture or the API fake.

**Alternatives:** Sending selected text without metadata from excluded applications was explicitly rejected; broad screen scraping and implicit context collection were rejected as disproportionate and fragile.

**Reconsider when:** Measured quality improvements justify an explicit, reviewed collector for browser, accessibility, or application-specific metadata.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#request-construction`; source proposal `SPEC-010` through `SPEC-015`, `SPEC-025`, `SPEC-045` through `SPEC-048`, `SPEC-066`, and `SPEC-067`; authorized human decision on 2026-09-01; code and tests `UNKNOWN`.

## Request construction and trust boundary {#request-construction}

**Normative:** Request construction MUST be a pure or near-pure operation with the conceptual interface:

```python
build_request(text, profile, source_context, settings) -> request
```

The logical request MUST place stable profile instructions and the structured-output contract before dynamic per-request input. Dynamic input MAY contain only the selected text, permitted normalized source context, and an optional user-supplied note when that post-MVP feature exists. Selected text, source metadata, and manual notes MUST be treated as untrusted data to transform or interpret, not as authoritative instructions that override the profile contract. Source metadata MAY influence tone, register, and degree of rewriting but MUST NOT be treated as factual content of the selected message.

Given identical selected text, profile, normalized context, and settings, the builder MUST produce the same logical request structure. Model output need not be byte-for-byte deterministic. Stable instruction prefixes SHOULD remain consistent to improve reproducibility and permit provider-side caching, but correctness MUST NOT depend on caching.

**Rationale:** A deterministic, explicit request boundary is independently testable, auditable, and resistant to accidental mixing of instructions with application metadata.

**Verification:** Snapshot or structural unit tests compare repeated builds, reject undeclared context fields, preserve stable/dynamic ordering, and verify that no local data is read implicitly by the builder.

**Alternatives:** Request construction inside the API client, implicit local-data reads, and correctness dependent on provider prompt caching were rejected.

**Reconsider when:** A provider API requires a different representation while preserving the same logical contract, or approved conversational behavior introduces explicit state.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`; source proposal `SPEC-026` through `SPEC-028`, `SPEC-051` through `SPEC-053`, and `SPEC-066`; code and tests `UNKNOWN`.

## Structured model result {#structured-result}

**Normative:** The MVP MUST request and accept a simple machine-readable object with exactly these required semantic fields:

```json
{
  "corrections": ["Concise description of a proposed correction"],
  "final_text": "The complete corrected text"
}
```

`corrections` MUST be an array of strings and MAY be empty when no correction is needed. `final_text` MUST be a string and MUST contain the complete usable result, including unchanged input when no correction is needed. The API/response boundary MUST validate the response before exposing a normalized internal result to UI or clipboard operations. Missing fields, wrong types, invalid structured data, or an empty `final_text` MUST be handled as malformed API responses and MUST NOT overwrite the clipboard with a partial result. The raw response MAY be retained only for logging and diagnostics.

**Rationale:** A small enforced structure reliably separates explanatory corrections from the text that may be copied automatically.

**Verification:** Parser tests accept valid objects with populated and empty correction lists; reject missing, mistyped, malformed, and empty-final-text cases; and verify UI and clipboard consumers receive only normalized results.

**Alternatives:** Parsing free-form prose and deferring structured output until after the MVP were explicitly rejected.

**Reconsider when:** The UI requires source spans, typed edits, confidence, localization, or a provider-neutral schema version.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#request-construction`; source proposal `SPEC-023`, `SPEC-024`, `SPEC-033`, and `SPEC-056`; authorized human decision on 2026-09-01; code and tests `UNKNOWN`.

## Selected-text and clipboard behavior {#clipboard}

**Normative:** For an allowed invocation, the automation layer MUST preserve the existing clipboard, issue the active application's standard copy command, wait for a clipboard update with a bounded timeout, and pass a non-empty textual selection to the backend. It MUST NOT assume an instantaneous update or reuse stale clipboard text as a selection fallback.

If no usable selection is obtained, the application MUST make no API request and MUST show a concise error such as `No selected text was detected.` After successful capture, the previous clipboard MUST be restored by default, including non-text formats where feasible. Restoration MUST NOT occur when the invoked result action intentionally copies corrected text, and MAY be disabled by configuration.

**Rationale:** Clipboard-based capture works across target applications but requires explicit stale-data and restoration safeguards.

**Verification:** Automation tests or Windows manual tests cover delayed copy, no selection, stale clipboard, text and representative non-text clipboard restoration, disabled restoration, and intentional final-text copy.

**Alternatives:** Processing existing clipboard text when no selection is detected and direct replacement of the original selection are outside the MVP.

**Reconsider when:** Accessibility APIs provide a more reliable cross-application selection interface or users explicitly request clipboard fallback/direct replacement.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`; source proposal `SPEC-030` through `SPEC-032`; code and tests `UNKNOWN`.

## Hotkeys, actions, and result presentation {#interaction}

**Normative:** Hotkeys MUST be configurable in `settings.json` and MUST route an explicit profile name and result action to the backend. The MVP MUST expose:

- `show_full`: display the corrections and final corrected text; and
- `copy_final`: place only normalized `final_text` on the clipboard.

The initial defaults SHOULD be `Ctrl+Alt+E` for `show_full` and `Ctrl+Alt+Shift+E` for `copy_final`. The presentation MAY be a minimal Python window, a Tkinter dialog, or a development console plus clipboard behavior, but it MUST expose both result fields for `show_full` and MUST NOT bind the long-term architecture to that presentation technology.

**Rationale:** Two explicit actions cover inspection and fast replacement workflows without requiring a sophisticated GUI.

**Verification:** Windows acceptance tests invoke each configured hotkey, verify explicit profile/action routing, inspect both fields for `show_full`, and compare clipboard contents for `copy_final`.

**Alternatives:** Direct selection replacement, automatic profile selection, tray UI, and a full chat UI are deferred beyond the MVP.

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

Timeout and retry count MUST be configurable. Automatic retries MUST be bounded and limited to transient connection failures, rate limits, and temporary server failures. Invalid credentials, invalid configuration, malformed requests, unsupported models, and invalid model responses MUST NOT be retried automatically.

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

**Normative:** Context normalization, request construction, API access, and response normalization MUST each be independently testable. Unit tests MUST NOT require AutoHotkey, the Windows clipboard, or live network access to cover those components. The API abstraction MUST support a fake implementation, and UI/clipboard consumers MUST receive normalized results rather than parse raw provider responses.

Windows integration coverage MUST separately exercise active-window observation, clipboard capture/restoration, hotkey routing, and single-request concurrency.

**Rationale:** Pure core components provide fast deterministic evidence while narrow Windows integration tests cover the platform boundary.

**Verification:** The project test runner can execute core unit tests offline; component tests demonstrate fake API injection and normalized result consumption; Windows acceptance commands are documented and reproducible.

**Alternatives:** End-to-end-only verification was rejected because it makes provider and clipboard failures hard to isolate.

**Reconsider when:** The implementation language or packaging model changes while preserving equivalent isolation and evidence.

**Traceability:** `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`; source proposal `SPEC-052` through `SPEC-056`; code and tests `UNKNOWN`.

## Explicit MVP scope {#mvp-scope}

**Normative:** The MVP includes Windows desktop support; AutoHotkey v2 global hotkeys; selected-text capture; clipboard preservation; a Python backend; versioned `settings.json` and `profiles.json`; the `proofread` profile; application/process detection; active-window-title capture; configured exclusions; stateless public-API access; structured corrections plus final text; full-result display; final-text copy; one in-flight request; full single-file logging; and basic errors and bounded retries.

The MVP explicitly excludes persistent conversations, chat UI, browser extensions, Discord and Telegram APIs, OCR, surrounding-message capture, sophisticated application-specific UI scraping, tray application, installer, cloud synchronization, direct replacement of selected text, Windows Credential Manager, automatic profile selection, manual context notes, local history, request queues, and multiple simultaneous requests.

Items excluded from the MVP are candidates only; this document does not authorize or require their implementation.

**Rationale:** The boundary contains the smallest end-to-end workflow that replaces manual web-chat proofreading while retaining inspectable results, privacy controls, and diagnostic evidence.

**Verification:** Release checklist maps every included item to a passing test or recorded Windows manual acceptance and confirms excluded features are not required for operation.

**Alternatives:** A richer initial GUI and application-specific integrations were rejected to keep the first implementation focused.

**Reconsider when:** MVP acceptance is complete and observed use identifies the next smallest valuable increment.

**Traceability:** All decisions in this specification; source proposal `SPEC-057` through `SPEC-059`; code and tests `UNKNOWN`.

## Cross-Cutting Invariants {#invariants}

- One invocation maps to at most one independent LLM request -> `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle` and `spec://proofreader/DESKTOP-ASSISTANT#concurrency`.
- Technical collection permission and profile usage permission are separate; transmitted context is their intersection -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- Exclusion decisions occur before selection capture and cause zero API transmission -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- Dynamic text and source metadata cannot override stable proofreading and output instructions -> `spec://proofreader/DESKTOP-ASSISTANT#request-construction`.
- Only a validated normalized result may reach result presentation or clipboard output -> `spec://proofreader/DESKTOP-ASSISTANT#structured-result`.
- Credentials never enter configuration, logical requests, model-visible input, or logs -> `spec://proofreader/DESKTOP-ASSISTANT#api-access` and `spec://proofreader/DESKTOP-ASSISTANT#logging`.
- Platform automation remains outside profile and model-processing policy -> `spec://proofreader/DESKTOP-ASSISTANT#architecture` and `spec://proofreader/DESKTOP-ASSISTANT#configuration`.

## Semantic changelog {#changelog}

- 2026-09-01 — authorized human request — `spec://proofreader/DESKTOP-ASSISTANT#summary`, `spec://proofreader/DESKTOP-ASSISTANT#constraints`, `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`, `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle`, `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, `spec://proofreader/DESKTOP-ASSISTANT#errors`, `spec://proofreader/DESKTOP-ASSISTANT#logging`, `spec://proofreader/DESKTOP-ASSISTANT#integration-boundary`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`, `spec://proofreader/DESKTOP-ASSISTANT#invariants`:
  `NONE -> initial DRAFT proposal consolidated from specs/spec-draft.md and the user's clarifications`; reason: `establish one reviewable protocol-compliant product contract`; invalidates: `NONE (initial specification; implementation and tests are UNKNOWN)`; review: `NONE`.
- 2026-09-01 — Project owner — `spec://proofreader/DESKTOP-ASSISTANT#summary`, `spec://proofreader/DESKTOP-ASSISTANT#constraints`, `spec://proofreader/DESKTOP-ASSISTANT#acceptance`, `spec://proofreader/DESKTOP-ASSISTANT#product-workflow`, `spec://proofreader/DESKTOP-ASSISTANT#stateless-lifecycle`, `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#request-construction`, `spec://proofreader/DESKTOP-ASSISTANT#structured-result`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, `spec://proofreader/DESKTOP-ASSISTANT#errors`, `spec://proofreader/DESKTOP-ASSISTANT#logging`, `spec://proofreader/DESKTOP-ASSISTANT#integration-boundary`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`, `spec://proofreader/DESKTOP-ASSISTANT#invariants`:
  `DRAFT proposal -> APPROVED normative specification`; reason: `explicit approval by the declared Project owner in the current conversation`; invalidates: `pre-approval specification verification evidence; implementation and test conformance remain UNKNOWN`; review: `NONE`.
