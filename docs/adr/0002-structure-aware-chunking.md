# ADR 0002: Structure-aware word chunks

## Status
Accepted · 2026-11-08

## Decision

Split headings first, then paragraphs and sentences, with a configurable word target and
same-section overlap. Each chunk records source, section, page, version, and superseded.

## Consequences

Clause boundaries remain visible to retrieval and citations. Chunk size still requires
recall@5 measurement on the approved golden set before final submission.
