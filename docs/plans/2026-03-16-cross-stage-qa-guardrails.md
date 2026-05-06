# Cross-Stage QA Guardrails Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strengthen prompt-driven process guardrails so each stage applies a QA-minded review lens that can catch broken UI labels and suspicious semantic inconsistencies before approval.

**Architecture:** The implementation stays inside the current prompt-construction model. Add a shared cross-stage QA guardrail contract in `src/asd_shop/prompts.py`, extend role-specific guidance for business analyst, architect, developer, and QA, and pin the new behavior with prompt tests that fail if these critical instructions disappear.

**Tech Stack:** Python 3.10, pytest, prompt-generation code in `src/asd_shop/prompts.py`

---

### Task 1: Add failing tests for cross-stage QA guardrail language

**Files:**
- Modify: `C:\Users\james\source\repos\agent-software-development-shop\tests\test_backend_prompts.py`
- Test: `C:\Users\james\source\repos\agent-software-development-shop\tests\test_backend_prompts.py`

**Step 1: Write the failing test**

Add tests that assert:

- business analyst prompts require explicit user-visible labels and semantic consistency criteria
- architect prompts require invariants or validation strategy for user-visible semantics
- QA prompts explicitly challenge suspicious logic and earlier assumptions
- developer prompts require tests or validation hooks for semantic consistency when relevant

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_prompts.py -q`
Expected: FAIL because the new guardrail language is not yet present in generated prompts.

**Step 3: Write minimal implementation**

Do not implement code yet. This task ends after the red test is confirmed.

**Step 4: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_prompts.py -q`
Expected: FAIL with assertions showing the missing guidance text.

**Step 5: Commit**

Do not commit in this worktree unless the user explicitly asks for it.

### Task 2: Implement shared and role-specific prompt guardrails

**Files:**
- Modify: `C:\Users\james\source\repos\agent-software-development-shop\src\asd_shop\prompts.py`
- Test: `C:\Users\james\source\repos\agent-software-development-shop\tests\test_backend_prompts.py`

**Step 1: Write the failing test**

Use the tests from Task 1 as the red state.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_prompts.py -q`
Expected: FAIL due to missing prompt language.

**Step 3: Write minimal implementation**

Update prompt construction so:

- there is a shared cross-stage QA-minded guidance block applied to all roles
- `business_analyst` guidance includes defining exact labels or terminology where user-visible wording matters and adding semantic consistency criteria
- `architect` guidance includes defining invariants or validation strategy for suspicious semantic mismatches
- `developer` guidance includes implementing tests or validation hooks for label integrity and ranking/semantic consistency when relevant
- `qa` guidance includes challenging prior artifacts when they appear incomplete, contradictory, or suspicious from a user-experience standpoint

Keep the wording short, imperative, and specific.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backend_prompts.py -q`
Expected: PASS

**Step 5: Commit**

Do not commit in this worktree unless the user explicitly asks for it.

### Task 3: Verify broader prompt behavior still passes

**Files:**
- Modify: none unless failures require minimal adjustment
- Test: `C:\Users\james\source\repos\agent-software-development-shop\tests\test_backend_prompts.py`
- Test: `C:\Users\james\source\repos\agent-software-development-shop\tests\test_prompts.py`

**Step 1: Write the failing test**

No new tests in this task. Use existing suite as regression coverage.

**Step 2: Run test to verify it fails**

Only if Task 2 unexpectedly regresses existing behavior.

**Step 3: Write minimal implementation**

If needed, make the smallest prompt wording adjustment that restores existing expectations without weakening the new guardrails.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backend_prompts.py tests/test_prompts.py -q`
Expected: PASS

**Step 5: Commit**

Do not commit in this worktree unless the user explicitly asks for it.

### Task 4: Run full verification

**Files:**
- Modify: none
- Test: `C:\Users\james\source\repos\agent-software-development-shop\tests`

**Step 1: Write the failing test**

No new test file. This task is verification only.

**Step 2: Run test to verify it fails**

Skip unless a regression appears.

**Step 3: Write minimal implementation**

Only if full-suite verification reveals a prompt regression elsewhere.

**Step 4: Run test to verify it passes**

Run: `python -m pytest -q`
Expected: PASS with all tests green.

**Step 5: Commit**

Do not commit in this worktree unless the user explicitly asks for it.
