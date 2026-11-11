# ADR 0003: Redis semantic cache

## Status
Accepted · 2026-11-08

## Decision

Use Redis for cache entries containing an embedding and a validated response. Keys are
namespaced by the content-derived index version, and only grounded validated answers are
stored. Cache failures fail open to retrieval.

## Consequences

Cache lookups are simple to invalidate by version and survive API pod replacement. A scan
over a small namespace is acceptable for this assignment; a larger system would use a
vector-capable cache index.

## Recovery supplement (2026-11-11)

The measured threshold is now 0.98, the lowest tested value with no false hits on eight
labeled pairs. A 2023/2026 policy pair scored 0.951054, ruling out 0.92 and 0.95. This
small benchmark does not guarantee correctness on unseen questions. Namespaces now also
fingerprint retrieval/citation policy and generation settings to avoid serving answers
from an older query policy on the same corpus. The indexer needs narrowly allowed Redis
access for actual expiry; a live sentinel experiment verified that it expires old cache
keys while preserving a designated current prefix and unrelated keys.
