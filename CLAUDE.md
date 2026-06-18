# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 0. Project Context

**We are building `archiagent`: an agent that assists a software architect, on the Claude Agent SDK.**

- **Goal:** an agent-building competition. Two deliverables — (1) the competition submission/docs, (2) the agent itself.
- **Stack:** Claude Agent SDK (Python or TypeScript — fix the choice when implementation starts).
- **What this file is:** the working guide Claude Code follows when designing and iterating the agent's *harness* (system prompt, tools, context, loop, evaluation). Sections 1–4 are general coding discipline; sections 5–6 are harness-specific.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Harness Engineering

**The harness — not the model — is what we are building. Engineer it deliberately.** Rules below distill Anthropic's published guidance (see section 6 links).

### Tool design first

- **Minimize tool surface.** More tools ≠ better. Consolidate related functionality; cut tools the agent rarely needs.
- **No ambiguous tool sets.** If a human can't tell which tool to use from name + description, the agent can't either.
- **Name for navigation.** Use shared prefixes for related tools (e.g. `arch_review_*`, `arch_diagram_*`). Unambiguous parameter names (`user_id`, not `user`).
- **High-signal responses.** Return what the agent needs to act, resolve opaque IDs to meaning, and stay token-efficient (pagination/filtering, and a `concise|detailed` switch when output can be large).
- **Errors should teach.** A failing tool returns a message that tells the agent how to fix the call, not a stack trace.

### System prompt design

- Direct language at the right altitude. Give heuristics, not brittle hard-coded logic.
- State the agent's role, hard constraints, and *when* to use each tool explicitly.

### Agent loop & stopping

- Verify against environment ground truth every step (run it, read the result) — don't trust the model's claim.
- Set explicit stop conditions (max iterations) so the loop can't spin.
- Insert human checkpoints (`AskUserQuestion`) for high-stakes or irreversible decisions.

### Context engineering > prompt stuffing

- Aim for the **smallest set of high-signal tokens** that maximizes the chance of the right outcome.
- Use compaction (summarize history), external structured memory (a progress file), and subagents that return condensed results — instead of cramming everything into one context window.

### Long-running harness pattern

- **Initializer agent** (runs once): set up the environment, progress-tracking file, and an initial git commit.
- **Coding agent** (per session): start with an onboarding routine (read working dir, git log, progress file → pick next priority → run tests → implement), make incremental progress, commit with descriptive messages, leave clean state for the next session.

### Eval-driven iteration

- Build realistic, multi-step eval tasks grounded in real architect work. Measure tool/prompt effectiveness, then iterate.
- **Do not add harness complexity without a measurement showing it helps** (ties back to section 2, Simplicity First).

## 6. Claude Agent SDK Notes

**Core building blocks** (use these rather than re-inventing): `query()` + `options` for the run; custom system prompt; tool registration (built-in tools + MCP servers); subagents for focused delegation; hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Stop`); and sessions / memory tool / prompt caching for state across turns.

**Model selection** (default to Opus 4.8 for build/architecture reasoning):

| Model | API ID | Use for |
|-------|--------|---------|
| Opus 4.8 | `claude-opus-4-8` | Deep architecture reasoning, long-horizon agentic work — **default** |
| Sonnet 4.6 | `claude-sonnet-4-6` | Production agents balancing capability, cost, latency |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Simple, high-volume, cost-sensitive subtasks |
| Fable 5 | `claude-fable-5` | The most demanding reasoning (highest cost) |

**Reference links:**

- Agent SDK overview — https://code.claude.com/docs/en/agent-sdk/overview
- Quickstart — https://code.claude.com/docs/en/agent-sdk/quickstart
- Subagents / Hooks / MCP / Skills — `https://code.claude.com/docs/en/agent-sdk/{subagents,hooks,mcp,skills}`
- Building Effective AI Agents — https://www.anthropic.com/research/building-effective-agents
- Writing Effective Tools for AI Agents — https://www.anthropic.com/engineering/writing-tools-for-agents
- Effective Context Engineering — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Effective Harnesses for Long-Running Agents — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Models Overview — https://platform.claude.com/docs/en/about-claude/models/overview

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
