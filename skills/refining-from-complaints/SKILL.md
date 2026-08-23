---
name: refining-from-complaints
description: Use when the user complains about working code or design that feels wrong.
---

# Refining From Complaints

Turn dissatisfaction with working code into a confirmed refinement target. This
skill owns diagnosis, not implementation.

## 1. Qualify

Capture the complaint from the user's perspective.

- A crash or reproducible failure belongs to `leveraging-tasks` debugging.
- A request for new behavior belongs to `leveraging-tasks` implementation.
- A complaint with no identifiable target may be venting; ask whether the user
  wants it investigated.

**Complete when:** there is a working code or design target the user wants
improved.

## 2. Diagnose

Inspect the implicated code and identify separately:

- the design decision that creates the complaint
- the documented standard, best practice, or project precedent it violates

Use `investigating` for substantial cross-source research. If neither item is
supported by evidence, classify the complaint as a preference rather than invent
a defect.

**Complete when:** the chain `complaint → root cause → violated standard` is
evidence-backed.

## 3. Confirm

Propose the smallest correction. Use `grilling` when viable alternatives carry a
real user-owned trade-off. Wait until the user confirms the root cause and
direction; treat disagreement as new diagnostic input.

## 4. Hand off

Return the confirmed chain to `leveraging-tasks` as requirements input for every
source-changing fix, regardless of size. This skill does not bypass specification,
design, implementation, or verification.

**Complete when:** no change was requested, or `leveraging-tasks` has received a
confirmed refinement target.
