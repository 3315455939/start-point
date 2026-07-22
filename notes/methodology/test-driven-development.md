# Test-Driven Development (TDD)

来源：Superpowers 6.1.1 `test-driven-development` skill（MIT License）
提取理由：RED-GREEN-REFACTOR 方法论——Claude Code 无内置等效。

---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. Delete means delete — don't keep as "reference", don't adapt it while writing tests.

## Red-Green-Refactor Cycle

### RED — Write Failing Test

Write one minimal test showing what should happen.
- One behavior per test
- Clear name describing behavior
- Real code (no mocks unless unavoidable)

### Verify RED — Watch It Fail (MANDATORY)

```
Run test → confirm it FAILS (not errors) → confirm fails because feature missing (not typos)
```

Test passes? You're testing existing behavior. Fix test.
Test errors? Fix error, re-run until it fails correctly.

### GREEN — Minimal Code

Write simplest code to pass the test. Don't add features, refactor other code, or "improve" beyond the test.

### Verify GREEN — Watch It Pass (MANDATORY)

```
Run test → confirm passes → confirm other tests still pass → output pristine
```

### REFACTOR — Clean Up

After green only: remove duplication, improve names, extract helpers. Keep tests green. Don't add behavior.

### Repeat

Next failing test for next feature.

## Why Order Matters

**"I'll write tests after to verify it works"** — Tests written after code pass immediately. Passing immediately proves nothing. You never saw it catch the bug.

**"I already manually tested all the edge cases"** — Manual testing is ad-hoc. No record, can't re-run, easy to forget cases under pressure.

**"Deleting hours of work is wasteful"** — Sunk cost fallacy. Keeping code you can't trust is technical debt.

**"TDD is dogmatic"** — TDD IS pragmatic: finds bugs before commit, prevents regressions, documents behavior, enables refactoring.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| Minimal | One thing. "and" in name? Split it. | `test('validates email and domain')` |
| Clear | Name describes behavior | `test('test1')` |
| Shows intent | Demonstrates desired API | Obscures what code should do |

## Example: Bug Fix

**Bug:** Empty email accepted.

**RED:** `test('rejects empty email', async () => { ... expect(result.error).toBe('Email required'); })`

**Verify RED:** `FAIL: expected 'Email required', got undefined`

**GREEN:** Add `if (!data.email?.trim()) return { error: 'Email required' };`

**Verify GREEN:** `PASS`

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "TDD will slow me down" | TDD faster than debugging. |
| "Test hard = design unclear" | Hard to test = hard to use. Simplify interface. |
| "Must mock everything" | Code too coupled. Use dependency injection. |

## Red Flags — STOP and Start Over

- Code before test
- Test passes immediately
- Can't explain why test failed
- Rationalizing "just this once"
- "Keep as reference" or "adapt existing code"
- "Already spent hours, deleting is wasteful"

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API first. Ask your human partner. |
| Test too complicated | Design too complicated. Simplify interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify design. |

## Verification Checklist

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass, output pristine
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered
