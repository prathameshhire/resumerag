# CLAUDE.md

## 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State assumptions explicitly. If uncertain, ask before writing code.
- If multiple interpretations exist, name them. Don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- Don't invent APIs, methods, flags, or config keys. If you're not sure something exists, check the source or docs. A guessed signature is worse than a question.

## 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No configurability or "flexibility" that wasn't requested.
- No defensive error handling for scenarios that can't occur.
- If it's 200 lines and could be 50, rewrite it.

Test: would a senior engineer call this overcomplicated? If yes, cut.

## 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor what isn't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions your changes orphaned. Leave pre-existing dead code alone — mention it, don't delete it.

Test: every changed line traces directly to the request.

## 4. Goal-driven execution

Define success criteria, then loop until they're met.

Turn vague tasks into verifiable ones:

- "Add validation" → write tests for invalid inputs, make them pass.
- "Fix the bug" → write a test that reproduces it, make it pass.
- "Refactor X" → confirm tests pass before and after.

For multi-step work, state a short plan with a check per step:

```
1. [step] → verify: [check]
2. [step] → verify: [check]
```

Verify the goal, not the keystrokes. Run the test that proves it works. Don't re-run commands whose output you already know.

## Code style

- Comments explain _why_, not _what_. Don't narrate the code.
- Follow the conventions already in the file over your own preferences.

## Git

- Run `git pull origin main` before branching or starting work, even if local looks current. Avoids conflicts from PRs merged between sessions.
- Don't commit, push, or open PRs unless asked.

## Token efficiency

- Don't re-read files you just wrote. You know the contents.
- Don't re-run commands to "verify" unless the outcome is genuinely uncertain.
- Don't echo back large code blocks or file contents unless asked.
- Batch related edits into one operation, not five.
- Skip "I'll continue..." filler. Just do the next thing.

---

**Working if:** diffs contain only necessary changes, fewer rewrites from overcomplication, and questions come before implementation rather than after mistakes.
