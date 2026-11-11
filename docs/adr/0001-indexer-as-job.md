# ADR 0001: Keep indexing in a one-shot Job

## Status
Accepted · 2026-11-08

## Context

The API has three replicas and Chroma owns the persistent index. Indexing during API
startup would create concurrent writers, repeat work on restarts, and make readiness lie.

## Decision

The indexer runs only from `python -m pipeline.run` as a Job/CronJob. The API is read-only.
The collection is rebuilt with a content-derived index version and the API refuses empty or
incompatible indexes.

## Options considered

Startup indexing and an init container were rejected because they couple availability to a
long-running write operation.

## Consequences

Re-indexing is explicit and can happen without rebuilding the API image. During replacement
the API may become temporarily unready, which is safer than serving a partial index.
