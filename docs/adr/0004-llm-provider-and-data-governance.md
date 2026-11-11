# ADR 0004: Pluggable provider and untrusted data

## Status
Accepted · 2026-11-08

## Decision

Ollama and OpenAI-compatible hosted providers implement one interface. Retrieved text and
user questions are delimited as data; the provider must return the Pydantic Answer schema,
which is validated again in the service. API keys are supplied only through environment or
Kubernetes Secret values.

## Consequences

The provider can be swapped without changing retrieval or response contracts. Schema
validation cannot prove factual truth, so the relevance floor and citation matching remain
mandatory.
