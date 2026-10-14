# Retrieval-first implementation (full instruction block)

Origin of the quote: "Good programmers write good code; great programmers
steal great code" — popularized by Jeff Atwood (Coding Horror, "Never Design
What You Can Steal"), itself a programmer's rewording of the apocryphal
Picasso line "Good artists copy; great artists steal." Exact attribution is
murky; treat it as folklore, not a citable source.

---

## The block

Before writing non-trivial code from scratch, look for a working reference
first. **Everyone** are far more reliable at adapting a correct example than
deriving logic from scratch in one pass.

### When this applies

Trigger for: new algorithms, parsers, protocol/format implementations, API
integrations, CLI argument handling, regex-heavy logic — essentially anything
with a well-known standard-library idiom or a common upstream package that has
already solved it.

Skip for: one-line changes, project-specific business logic, and edits to code
that already exists in this repo (read-before-edit still governs those).

### Workflow

1. **Search before drafting.** Use `websearch` to find how this is typically
   implemented: official docs, the relevant stdlib/package source, or a
   well-starred repo solving the same problem. If `dispatch` is available,
   prefer spawning a sub-coder for the research leg so the main session's
   context stays clean.
2. **Fetch, don't guess.** Use `webfetch` to pull the actual source or doc
   page rather than relying on a search-result snippet alone.
3. **Adapt, don't transcribe.** Rewrite the found example to fit this
   project's conventions, types, and error handling. Recode, don't retype:
   reworking the pattern line by line is how it gets understood well enough to
   debug later. Prefer the standard library over copying a third-party
   dependency, and note the source in a brief comment.
4. **Verify against the task, not the source.** The reference is a starting
   point, not ground truth for this repo's requirements. Run the existing
   tests/build after adapting, same as any other change.

### If retrieval fails

After 2-3 search refinements with no usable reference, say so explicitly, then
write from scratch and flag the assumption in a comment. Never present
unverified code as if it were adapted from a working source.

---

## Maintainability: write for the next reader

Adapted from the Changeability Specialist review lens: the bar for new code
is that an unfamiliar teammate can safely understand, change, validate,
debug, and recover it without the author present. Write-time rules:

1. **Make contracts explicit.** State assumptions, invariants, and error
   behavior at the interface (signature, types, or a short comment). If a
   caller must know something invisible at the call site, that is hidden
   coupling — a defect, not a style choice.
2. **One responsibility per unit, safe seams.** Keep coupling low and
   ownership clear so a change does not ripple sideways. Avoid action at a
   distance: shared mutable state, globals, side effects the signature does
   not admit to.
3. **No giant one-liners or overly dense blocks.** If you cannot set a
   breakpoint on it, you cannot debug it. Prefer boring, stepped code over
   clever compression — "Debugging is twice as hard as writing the code in
   the first place" (Kernighan).
4. **Comment the why, not the what.** Capture intent, invariants, and
   recovery knowledge (retry-safety, ordering constraints, rollback notes)
   that the code cannot say. Do not narrate the code. Missing documentation
   matters exactly when the missing contract would prevent safe change — no
   earlier.
5. **Leave validation behind.** The test or command that proves the change
   works is part of the deliverable; name it near the code or in the commit.

References: Ousterhout, *A Philosophy of Software Design* (complexity is
whatever makes code hard to understand or modify; deep modules behind simple
interfaces); Kernighan & Pike, *The Practice of Programming*; Winters et
al., *Software Engineering at Google* (code is read far more than written —
optimize for the reader); tef, "Write code that is easy to delete, not easy
to extend" (2016).
