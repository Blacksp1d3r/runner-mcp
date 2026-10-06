# Bounded work-item standard

Every substantial roadmap item is an umbrella. Implementation happens in bounded child issues.

Each child records parent/dependencies, owner/lane, exact scope, started/completed timestamps, initial/final revision or state, acceptance criteria, required credential/key/token metadata by symbolic name and purpose only, trust/location class, known-valid/issued date, expiry and rotation/renewal date, CI/tests/qualification evidence, blockers, errors/root cause/remediation/prevention, rollback/recovery notes and final outcome/follow-up children.

Never record secret values. Reusable, surprising, security-relevant, expensive-to-diagnose or recurring errors become linked dedicated failure records containing symptom, conditions, evidence, root-cause confidence, fix, prevention/detection and affected versions. Keep failure records small and indexable.

A parent is complete only from child evidence, never from prose alone.
