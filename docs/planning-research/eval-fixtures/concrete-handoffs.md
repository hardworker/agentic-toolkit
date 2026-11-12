# Concrete planning requests

These are independent synthetic requests. Treat the supplied facts as the complete source packet, not live-system observations. Produce plans/reviews only. Do not implement, browse, install, publish, read other plans, create agents or write to a live planning library. Save outputs in the designated scratch directory. No prescribed headings or word target apply. Use the assigned authoring instructions; these task constraints override their execution, storage and interactive handoff defaults. The user delegates technical choices within the stated constraints; record material assumptions and genuine blockers rather than waiting for an interview.

## Case 1 — Background work suggestions

User: Plan a general background capability for Signalbox, our team assistant. New repository activity, shared-inbox messages and customer feedback should be considered alongside ongoing work so the assistant can draft a useful next step or stay quiet. I want a system design and an implementation plan, with a credible first useful delivery. The overall design should cover the capability even if implementation is incremental. Prefer what we already have. Explain it for a capable engineer joining the project. This is planning only; no live source setup, model runs or implementation.

Requirements:

- Drafts appear in a review panel. A person approves an individual draft before existing delivery machinery sends it. No automatic tasks or external messages.
- Preserve each source's disclosure restrictions through retrieval, drafts and delivery. A shared inbox may be visible to a smaller group than the project channel.
- A later update about the same work can be useful; retries of the same delivery should not produce duplicate work or drafts. Avoid redundant suggestions about work that is already being handled.
- Start with repository activity for the first working slice, but retain inbox and feedback in the overall design. A new source must not require a separate reasoning service.
- Keep costs bounded and failed/deferred work inspectable. The current quiet-hours and approval policies remain in force.

Supplied existing capabilities:

- One TypeScript service with SQLite. Transactions can insert evidence, jobs and decisions atomically. The scheduler checks due work every ten seconds. Workers use expiring leases and record attempt count and next due time. Current jobs process one chat thread; no handler exists for external evidence.
- Source adapters already authenticate intake and produce source ID, delivery ID, resource ID, revision, time and a content reference. A uniqueness constraint can identify exact source/delivery retries. Repository and inbox sources provide stable revisions; customer feedback provides stable submission IDs but no revision history. Adapter payloads are evidence, not trusted instructions.
- The existing structured-model gateway can request host-mediated read-only tools and return a typed decision. Its caller must run the tool loop. Each model call reserves a conservative cost ceiling before starting and settles reported usage afterward; admission can refuse a call. Cancellation, maximum model/tool calls and output limits can be enforced by the caller. It has no reasoning over external evidence yet.
- A separate general-purpose agent runtime has long-running sessions, shell and messaging tools. It currently has no per-call usage admission adapter. Adding those controls would be new work. Both runtime options can consume the same maintained domain instructions.
- Connection-scoped read APIs exist for source content, project metadata, conversations and task records. The host knows the connection principal. Resource authorization returns allow, deny or unknown; disclosure checks can evaluate a source scope against a destination audience. Access can be revoked between intake and delivery. These APIs have not yet been assembled into a background tool surface.
- Project mappings keyed by stable resource IDs exist. Directory records supply current role assignments. Conversation summaries and learned associations are useful search hints but can be stale or conflict with those records. Task records include resource links and state; there is no cross-source correlation service.
- The review panel can display a draft and its evidence, and approve or reject it. The outbox persists approved delivery, checks current audience eligibility, and reconciles uncertain sends against the provider before retrying. It currently carries chat-derived evidence only.
- There is no throughput or quality baseline for this feature. Existing unit/integration checks run with `npm test`; transport, gateway and outbox adapters have deterministic fakes. A local integration fixture can restart the worker against a persisted database. No production load target has been selected.

## Case 2 — Small documentation review

User: Review this plan. Keep it as written unless there is a material problem. I do not want another interview.

Plan: Update the Help page to explain that CSV exports contain the currently filtered rows. Keep the export behavior unchanged. Check the wording against the existing export behavior, then have the support owner review the page. Done when the page accurately states the filtered-row behavior and the support owner accepts the wording.

Supplied facts: exports do contain only filtered rows; the support owner is available. No API, schema or processing change is requested.

## Case 3 — Product investigation

User: Help plan an investigation into weak onboarding completion. We have two weeks, an analyst and a product researcher. We are not choosing a feature yet. Reminders are one hypothesis; confusing setup and a mismatch between expectations and the product are others. Gamification is excluded. Make the next investigation concrete enough to carry out and explain what decision the evidence should support.

Supplied facts: 100 people began onboarding last month; 40 completed within seven days. Six recent support messages mention confusing setup, but they cannot be linked to those 100 people and may include existing users. There are no interviews or controlled comparisons. The analyst can inspect de-identified event data. The researcher can interview consenting participants through the existing opt-in panel. No new tracking or unsolicited outreach is authorized. Completion within 30 days is the primary question; seven days is a secondary view. No baseline for 30-day completion or confirmed event coverage is available.

## Case 4 — Handoff readiness review

User: Review the following as the complete system design I requested for a nightly recommendation service. Is it ready for implementation? Preserve the draft; list material gaps separately.

Draft: Reuse the existing event inbox. A worker will collect relevant context and run a bounded model to choose whether to recommend an action. It will select the appropriate audience, preserve permissions and avoid redundant recommendations. Persist results and retry failures safely. Stage 1 adds durable intake; stage 2 adds reasoning; stage 3 connects delivery. Acceptance is that representative inputs produce useful, authorized recommendations. Choose the model runtime and context/authorization mechanism when implementing stage 2. The intake stage can start now.

Supplied facts: the user asked for the complete design, not only intake or a feasibility study. Existing intake is suitable and its contract is known. The draft contains no additional runtime, context, state, access or recovery design. You have no other sources. Do not invent the missing design while reviewing it.
