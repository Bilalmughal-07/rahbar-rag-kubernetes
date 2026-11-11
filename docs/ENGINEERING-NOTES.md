# Engineering notes

These notes tie the design to the implementation. Kubernetes command evidence is recorded
in `docs/evidence/`. Relevant implementation locations are `indexer/pipeline/run.py`
for the one-shot entrypoint, `api/app/routes/health.py` for probes,
`api/app/retrieval/chroma.py` for metadata filtering, `api/app/services/answer.py` for
validation/fallback, and `api/app/services/cache.py` for versioned cache keys.

## 1. Indexing in API startup: what breaks with 3 replicas and one Chroma volume?

Three replicas would race to write one Chroma volume, repeat extraction on restart, and
expose readiness before a complete index exists. The separate indexer entrypoint and Job
prevent API startup from becoming a multi-writer.

The API process only constructs readers in its lifespan; `run_pipeline()` is reachable from
the indexer command-line entrypoint. Re-indexing is therefore a Job/CronJob operation rather
than a deployment restart.

## 2. Readiness and liveness swapped, Chroma slow for 90 seconds: what happens?

If liveness depended on slow Chroma, all pods could be killed during the delay and create a
restart storm. `/healthz` is process-only; `/readyz` checks Chroma, collection, Redis, and
the embedding pin.

Readiness is allowed to be false while a dependency recovers. Liveness continues to return
200 because the process itself is healthy, so Kubernetes does not amplify a dependency outage
into a restart storm.

## 3. What does a CPU-based HPA measure on a generation service, and what should scale it?

Remote generation is I/O wait, so CPU measures request overhead rather than model pressure.
Scale on in-flight requests, queue depth, or generation latency using a custom metric.

The Prometheus layer exposes request, retrieval, generation, cache, abstention, fallback,
and token metrics. A future HPA can consume an in-flight request gauge or queue-depth metric
through the Kubernetes custom-metrics API.

## 4. The indexer's peak memory, its limit, the margin, and the exit code when it is wrong

Select the limit from `kubectl top pod` during indexing plus headroom. Too low yields
`OOMKilled` and exit code 137. The recovery run recorded samples in
`docs/evidence/current/resource-samples.txt`: API pods were generally around 65–71 MiB,
and the original indexer's sampled working set reached 859 MiB. Its 2 GiB memory limit
therefore leaves about 1,189 MiB above that observed sample, not a proven peak margin.
The original run also had an observed cgroup memory reading of 1,308,037,120 bytes;
cgroup usage includes more than the working-set figure reported by Metrics Server.

The exact memory high-water mark was not captured before the completed container exited.
The failed probe record remains local-only; no retained evidence establishes a true peak.
Do not label a sampled value as the true peak. CPU evidence showed 9,037 throttled periods out of 9,631 under the
one-core limit. The Job/CronJob CPU limit is now four cores; a later sample used 3,477m.
The final complete run took 382.3 seconds. These are measured workload observations,
not a guarantee for a larger corpus or a different host.

## 5. recall@5 by question type: where is it worst, and why?

The final run's weakest groups were exact-term and HTML-table questions, both at 0.5
recall@5. Annual reports improved from 0.25 to 1.0 after explicit period filtering;
version-sensitive questions improved to 1.0. Dense embeddings blur codes, clause numbers,
and thresholds. Hybrid lexical plus vector retrieval or reranking addresses the remaining
gap; better HTML extraction also deserves inspection before blaming generation.

The evaluator reports the breakdown instead of hiding this weakness inside an overall average.

## 6. EMBED_MODEL changed on the API only: what does your system do?

Startup records the collection/configured model conflict and `/readyz` returns 503. Without
the guardrail, incomparable vectors would silently produce nonsense retrieval.

The collection stores both `embed_model` and `dimension`; the readiness response names the
configured and indexed model. Re-indexing with the new model is the remediation.

## 7. The failure that cost us more than an hour

Numbered prose was initially misclassified as headings. Fixture chunks lost section labels;
printing `_units()` revealed the cause, and narrowing heading detection fixed it.

The regression test now checks that fixture sections survive extraction, cleaning, and
chunking, making this metadata-loss class visible before integration testing.

That paragraph is a transferred historical account; its elapsed time was not independently
verified. Current recovery directly observed a different failure: a year-specific question
could retrieve another report year because the old code only removed the superseded filter.
Per-request response inspection, followed by Chroma metadata checks, exposed it. Exact
version selection raised measured recall@5 from 0.684211 to 0.894737. Partners should confirm
their own personal retrospective and actual time spent for the assignment's question 7;
this report does not invent a greater-than-one-hour duration for an individual bug.
