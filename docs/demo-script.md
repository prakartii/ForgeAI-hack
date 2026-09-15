# FailureFoundry — 4-minute submission script

Target: 3:50 of spoken content inside a 4:00 video, leaving ~10s buffer.
Pace: ~150 words/minute. Read each line once out loud before recording —
if a beat runs long, cut adjectives, not nouns (keep claim IDs, numbers,
field names; those are what make it look real).

**Before you hit record:**
1. Restart both servers fresh so PRISM's settings cache and the DB are current.
2. Do one full silent dry run of every click below — PRISM calls and
   `computeMetrics` can take a few seconds; know where the pauses are so
   you can talk over them instead of standing in dead air.
3. Have a claim with a real uploaded photo ready in `/users` history
   (or be ready to upload one on camera — either works, camera is more
   convincing).
4. Open two tabs: `/users` (portal) and `/` (console), console on Judge
   View. Keep both loaded before recording starts.

---

### 0:00–0:20 — Cold open, no dashboard yet (20s)

**Screen:** blank browser, then type the portal URL.
**VO:**
> "Every AI-reliability tool at a hackathon shows you a dashboard that
> says a model was unfair. We're going to show you a model that's
> *structurally unable* to see the thing that made it unfair — and prove
> it, live, on a claim I file right now."

### 0:20–1:00 — File a real claim (40s)

**Screen:** `/users` → "File a new claim" → upload a real photo, pick
peril/damage part/severity, submit.
**VO:**
> "This is FairClaim — a synthetic insurance claims system, and the
> demonstration environment for the real product, FailureFoundry. I'm
> uploading an actual photo and filing a real claim — nothing here is a
> canned sample."
(as it processes)
> "Four agents run: Intake structures this into damage type, severity,
> repair cost. Adjudication applies a deterministic payout rule. Explainability
> writes the plain-English reason. Nothing here is invented — the payout
> is math: repair estimate minus deductible, capped at the coverage limit."

### 1:00–1:50 — The fairness certificate: the wow moment (50s)

**Screen:** Result page → tap the fairness trust badge → show "no
disparity found" → then narrate the toggle concept using the console
(or, if wired, the protection-off view).
**VO:**
> "Here's the part that matters. This claim just got re-run four times —
> same policy, same damage, same evidence — with only the claimant's
> name, city, and writing style changed. Decision and payout: identical
> across every variant.
>
> Now watch what happens with the fairness protection turned off."
**Screen:** switch to console → Agent Runs, or a pre-staged unprotected
run showing payout divergence for the same counterfactual group.
**VO:**
> "Same facts. Different payout. That's not a dashboard warning — that's
> a real, reproducible fairness failure, and it's exactly the failure
> FailureFoundry was built to catch and structurally remove."

### 1:50–2:30 — Console: failure → ABI → enforcement (40s)

**Screen:** click the receipt's "verify in the engineering console" link
→ Failures page (the matching failure) → Behavior ABI page.
**VO:**
> "PRISM diagnosed this. FailureFoundry compiled that diagnosis into a
> versioned Behavior ABI — `fair_adjudication_v1` — a contract that
> names exactly what's prohibited: ZIP, name, narrative style. This
> isn't a YAML file that just sits there — enforcing it means those
> fields are removed from Adjudication's context before it ever
> reasons. Structurally unavailable, not filtered after the fact."

### 2:30–3:00 — Regression + Judge View (30s)

**Screen:** Regression page (the permanent test) → Judge View page,
scroll through v1 vs v2 metrics.
**VO:**
> "That failure is now a permanent regression test — it can never
> silently disappear from the suite. And here's the whole story on one
> screen: v1's pairwise consistency, and v2 with the ABI enforced,
> computed live, right now, not asserted."

### 3:00–3:35 — Release gate: PASS or BLOCKED, live (35s)

**Screen:** Judge View's release gate section (or full Release Gate
page) → click "Re-run live" → show the real clause-by-clause result.
**VO:**
> "The release gate checks every one of these conditions against real
> executions — critical violations, fairness threshold, regression pass
> rate, and real PRISM evidence, actually fetched, not assumed. Right
> now it says [read the live status]. If any clause fails, this blocks —
> and tells you exactly which clause and why."

### 3:35–3:50 — Close (15s)

**Screen:** back to the thesis line (Overview or Judge View header).
**VO:**
> "PRISM found the failure. FailureFoundry turned it into a contract,
> enforced it, and now guards it forever. That's FailureFoundry."

---

## If you're short on time, cut in this order

1. Cut the Regression-page detour (2:30 beat) — mention it in one line
   instead of clicking to it.
2. Cut the Behavior ABI page visit — say the ABI's field list out loud
   over the Failures page instead of navigating there.
3. Never cut: the fairness certificate toggle (1:00–1:50) and the live
   release-gate result (3:00–3:35) — those are the two beats that prove
   this isn't hardcoded.

## Live-demo risk and the fallback line

PRISM API calls have occasionally timed out under load in testing. If a
PRISM-dependent screen hangs on camera, don't panic-cut — say the line
below and keep moving, it's true and it's on-brand for the project's own
rule (never fabricate PRISM evidence):

> "PRISM's evaluating this live over the network, so it may take a
> second — while it does, [continue narrating]."
