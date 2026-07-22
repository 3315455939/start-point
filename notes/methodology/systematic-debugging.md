# Systematic Debugging

来源：Superpowers 6.1.1 `systematic-debugging` skill（MIT License）
提取理由：根因追踪、防御性深度、条件等待——Claude Code 无内置等效。

---

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## When to Use

Any technical issue: test failures, bugs, unexpected behavior, performance problems, build failures.

**ESPECIALLY when:** under time pressure, "just one quick fix" seems obvious, you've already tried multiple fixes, you don't fully understand the issue.

## The Four Phases

### Phase 1: Root Cause Investigation (BEFORE any fix)

1. **Read Error Messages Carefully** — stack traces completely, line numbers, error codes
2. **Reproduce Consistently** — exact steps, every time? If not → gather more data
3. **Check Recent Changes** — git diff, recent commits, new dependencies, config changes
4. **Gather Evidence in Multi-Component Systems** — add diagnostic instrumentation at each component boundary before proposing fixes
5. **Trace Data Flow** — where does bad value originate? What called this with bad value? Keep tracing up until source

### Phase 2: Pattern Analysis

1. Find working examples in same codebase
2. Compare against references (read completely, don't skim)
3. Identify every difference between working and broken
4. Understand dependencies

### Phase 3: Hypothesis and Testing

1. Form single hypothesis: "I think X is root cause because Y"
2. Test minimally — smallest possible change, one variable at a time
3. Verify before continuing — worked? → Phase 4. Didn't? → new hypothesis

### Phase 4: Implementation

1. Create failing test case first
2. Implement single fix — ONE change, no "while I'm here"
3. Verify — test passes? no other tests broken?
4. **If 3+ fixes failed:** STOP — question the architecture. Is this pattern fundamentally sound? Discuss with your human partner.

## Red Flags — STOP and Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "It's probably X, let me fix that"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)

## Root Cause Tracing

Bugs often manifest deep in the call stack. Your instinct is to fix where the error appears — that's treating a symptom.

**Core principle:** Trace backward through the call chain until you find the original trigger, then fix at the source.

Process:
1. Observe the symptom
2. Find immediate cause (what code directly causes this?)
3. Ask: What called this?
4. Keep tracing up — what value was passed?
5. Find original trigger — where did that value come from?
6. Fix at source, then add validation at each layer

## Defense-in-Depth

When you fix a bug caused by invalid data, don't stop at one validation point. Validate at EVERY layer:

- **Layer 1:** Entry point validation (reject obviously invalid input)
- **Layer 2:** Business logic validation (data makes sense for this operation)
- **Layer 3:** Environment guards (prevent dangerous operations in specific contexts)
- **Layer 4:** Debug instrumentation (capture context for forensics)

All four layers are necessary — different code paths bypass different checks.

## Condition-Based Waiting

Flaky tests often guess at timing with arbitrary delays.

**Core principle:** Wait for the actual condition you care about, not a guess about timing.

| Scenario | Pattern |
|----------|---------|
| Wait for event | `waitFor(() => events.find(e => e.type === 'DONE'))` |
| Wait for state | `waitFor(() => machine.state === 'ready')` |
| Wait for count | `waitFor(() => items.length >= 5)` |
| Wait for file | `waitFor(() => fs.existsSync(path))` |

Always include timeout with clear error message. Poll every 10ms, not 1ms.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too |
| "Emergency, no time" | Systematic is faster than guess-and-check thrashing |
| "I'll write test after confirming fix works" | Untested fixes don't stick |
| "Multiple fixes at once saves time" | Can't isolate what worked |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause |
