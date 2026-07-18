# Chronos — Project Brief

## 1. One-Line Pitch
Chronos is a Bob-orchestrated, multi-agent pipeline that maps, modernizes, and compliance-audits legacy codebases — turning a manual, weeks-long migration process into a fast, visible, auditable workflow.

## 2. Challenge Context
- **Hackathon:** AI Builders Challenge with IBM Bob (BeMyApp / IBM SkillsBuild)
- **Track:** Wildcard — "Build Intelligent Systems for the Future of Work"
- **Deadline:** July 31, 2026, 11:59 PM ET
- **Primary tool requirement:** IBM Bob must be the primary development tool used to build the prototype.

## 3. Problem Statement
Legacy systems (Java 8/11, COBOL, old Python) run critical infrastructure in government, banking, and transit. Modernizing them is risky and expensive because:
- Developers manually trace dependencies before touching anything, which is slow and error-prone.
- Refactors silently break existing behavior.
- Security vulnerabilities and compliance gaps (GDPR, HIPAA, FedRAMP) are usually caught late, manually, or not at all.
- There is no single, visible source of truth for "what changed and why it's safe."

## 4. Solution Overview
Chronos runs three specialized Bob agent modes against a target legacy repository, coordinated in sequence, each producing a structured artifact the next agent (and the dashboard) can consume:

| Agent | Bob Mode | Job | Output |
|---|---|---|---|
| **Cartographer** | Read-only custom mode | Scans the repo, builds a dependency/structure map | `dependency-map.json` + architecture diagram |
| **Modernizer** | Write-enabled custom mode | Refactors deprecated code to a modern standard while preserving logic | Modified source files + `changelog.md` |
| **Compliance Officer** | Read + limited-write custom mode | Scans refactored code against GDPR/HIPAA/FedRAMP-style rules; flags issues | `compliance-report.json` |

A lightweight dashboard (built after the pipeline works) reads these three output files and renders:
- The dependency map (before)
- The code diff (before/after)
- The compliance findings (pass/fail flags with severity)

## 5. Why This Fits the Wildcard Track
Legacy modernization is a direct, high-stakes "future of work" bottleneck — it consumes enormous engineering hours across regulated industries. Chronos reframes it as an orchestrated, auditable AI workflow rather than a manual, tribal-knowledge-dependent process.

## 6. Scope for MVP (What We Are Actually Building)
**In scope:**
- One small sample legacy repo (Java 11, a handful of files, seeded with real code smells)
- Three working custom Bob modes, run in sequence, producing real output files
- One end-to-end pass: raw repo in → mapped, modernized, audited repo + reports out
- A simple dashboard page displaying the three outputs
- Documentation of exactly how Bob was used at each stage

**Out of scope (for MVP):**
- True parallel multi-agent execution (sequential is fine for MVP; mention parallelization as a roadmap item)
- Support for multiple languages (Java only for MVP)
- Auto-merging a pull request (can be simulated/described, not required to be live)
- A production-grade compliance rules engine (a focused, well-chosen rule set is enough — depth over breadth)
- User auth, multi-tenant, persistence layer for the dashboard

## 7. Success Criteria
1. Bob's Cartographer mode produces a real, correct dependency map from the sample repo.
2. Bob's Modernizer mode successfully refactors at least 2–3 concrete deprecated patterns without breaking logic (demonstrated via before/after + passing tests if present).
3. Bob's Compliance Officer mode correctly flags at least 2–3 seeded compliance/security issues.
4. All three outputs are visualized in a working dashboard.
5. The full pipeline runs in a single recorded pass for the demo video, in well under the 3-minute video limit.

## 8. Deliverables Checklist
- [ ] Sample legacy repo (seeded with issues)
- [ ] `AGENTS.md` (generated via Bob `/init`)
- [ ] Three custom Bob modes configured and tested
- [ ] Pipeline run producing `dependency-map.json`, modernized code + `changelog.md`, `compliance-report.json`
- [ ] Dashboard rendering all three artifacts
- [ ] Public GitHub repo + README (problem, solution, architecture, theme, how Bob was used)
- [ ] IBM SkillsBuild learning activity completed
- [ ] Project page submitted on challenge platform
- [ ] 3-minute public demo video

## 9. Team & Roles
*(fill in once team is finalized)*
- Builder(s):
- Video/pitch:
- README/docs:

## 10. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Modernizer breaks logic during refactor | Keep sample repo small; verify with tests or manual check before/after each change |
| Compliance rules feel arbitrary/fake | Base rule set on real, named clauses (e.g., "GDPR Art. 32 — encryption of personal data at rest") rather than generic "security best practices" |
| Running out of time before video | Get pipeline working on tiny repo first; polish dashboard only after core pipeline is proven |
| Judges can't tell what Bob actually did vs. what we scripted | Document every Bob mode, prompt, and `/init` output explicitly in README |
