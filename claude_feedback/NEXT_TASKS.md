# Claude task queue compatibility pointer

The canonical live Claude work queue is now:

`claude_feedback/CURRENT_ASSIGNMENT.md`

Use that file for:
- the current unfinished task;
- ordered follow-up tasks;
- per-task PR/CI evidence;
- automatic continue-to-next-task instructions;
- stop conditions and coordination boundaries with ChatGPT.

This pointer remains so older prompts that mention `NEXT_TASKS.md` do not break.

Historical note:
- Task 1 (direct Settings/adapter regression coverage) was completed in PR #42 and merged as `3653e22f9618f0e00374ee3d008c5c435c94acdc`.

Do not maintain a second independent task queue here; that would create drift.
