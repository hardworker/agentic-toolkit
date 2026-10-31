# Planning requests

These are four independent, synthetic requests. Source facts are supplied below; no external retrieval is needed. No implementation, external actions, new agents or live-library writes are permitted. Return each requested plan/review in a separate Markdown file in the designated output directory; use the supplied skill and relevant references. Do not impose an output word target. Treat supplied conversation updates as later user messages.

## 1. Repeat support issues

User: We need a continuously running multi-agent improvement service: a vector database, an observer, a critic, a proposal queue and a dashboard. Please plan the architecture and first useful delivery. The actual goal is to identify recurring support issues and produce proposed fixes with enough evidence for a maintainer to assess them. Keep raw support text local. CSV export is required for the weekly review. Humans must approve any proposed change; no automatic code edits or external posting. A report could look like `R-001 | Login errors | investigate token expiry`—that is just an example.

Existing capability: a local SQLite archive of completed support cases with timestamps and stable case IDs; a working keyword search; a daily scheduler; a Markdown report generator. There is no reliable count yet of how often apparently similar cases share a root cause. One maintainer can inspect proposals weekly. No accuracy benchmark has run.

Later user update: Start with a weekly report, not continuous observation. Keep CSV export. We rejected a dashboard for now. Revisit automation only if the weekly reports prove useful. We still need the architecture and a credible first proof.

## 2. Broad documentation comparison

User: Compare all four approaches below for keeping team documentation current. Cover ownership, discoverability, update cost, uncertainty and suitability for a small pilot. I want both the comparison and a recommended pilot; selecting a pilot must not replace the broad comparison. Use these internal descriptions as the evidence available today, not as performance measurements.

A. Manual review: document owners get a weekly list of recent repository changes. Existing owners and Git history are available; nobody has measured how much is missed.
B. In-repository checks: validate local links and flag changed public interfaces. Existing CI can run the checks; semantic correctness still requires review.
C. Retrieval assistant: search docs and suggest outdated passages for a human reviewer. Local search exists; retrieved text may describe an old decision that is still valid.
D. Agent-maintained drafts: an agent proposes doc diffs after changes. A development branch and reviewer workflow exist; no evaluation of factual accuracy or reviewer burden has run.

Constraints: no automatic publication and no new hosted service for the pilot. Keep rejected alternatives available with the reason. Don't turn this into an implementation specification.

## 3. Already-clear small plan

User: Review this plan. Keep it as written unless there is a material problem; I do not want another interview.

Plan: Update the Help page to explain that CSV exports contain the currently filtered rows. Keep the export behavior unchanged. Check the wording against the existing export behavior, then have the support owner review the page. Done when the page accurately states the filtered-row behavior and the support owner accepts the wording.

Verified context: the export currently includes only filtered rows. The support owner is available. No API, schema or data-processing change is requested.

## 4. Early onboarding research

User: Help plan an investigation into weak onboarding completion. We are not choosing a feature yet. I initially thought reminders might fix it, but that is only a hypothesis. We have ruled out gamification for this investigation. Outline what to learn next, competing explanations and the decision the research should support.

Available evidence: of 100 people who began onboarding last month, 40 completed it within 7 days. Six recent support messages mention confusing setup; they are not linked to those 100 people and may include existing users. There are no interviews or controlled comparisons yet. The analyst can inspect de-identified event data; the product researcher can interview consenting participants. No new tracking or unsolicited outreach is authorized by this request.

Later user update: Use completion within 30 days as the main question; 7 days can remain a secondary view. Consider both confusing setup and a mismatch between expectations and the product. I want a research direction and next evidence, not a delivery roadmap.
