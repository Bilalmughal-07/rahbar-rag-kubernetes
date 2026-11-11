from __future__ import annotations

from run_eval import citation_validity, gate, recall_at_k, summarise


def test_recall_and_citation_matching() -> None:
    relevant = [{"source": "a.pdf", "section": "1"}, {"source": "b.pdf", "section": "2"}]
    retrieved = [{"source": "a.pdf", "section": "1"}, {"source": "x.pdf", "section": "9"}]
    assert recall_at_k(relevant, retrieved, 2) == 0.5
    response = {"citations": [{"source": "a.pdf", "section": "1", "page": 1}],
                "retrieved": [{"source": "a.pdf", "section": "1", "page": 1}]}
    assert citation_validity(response) == 1.0


def test_summary_and_gate() -> None:
    relevant = [{"source": "a.pdf", "section": "1"}, {"source": "b.pdf", "section": "2"}]
    retrieved = [{"source": "a.pdf", "section": "1"}, {"source": "x.pdf", "section": "9"}]
    rows = [{"id": "a", "type": "ordinary", "relevant": relevant, "must_abstain": False,
             "response": {"retrieved": retrieved,
                          "citations": [{"source": "missing", "section": "x", "page": 1}],
                          "answered_from_context": True}}]
    summary = summarise(rows)
    assert summary["recall_at_5"] == 0.5
    assert gate(summary, {"recall_at_5": 0.5}) == [
        "citation validity 0.000 is below 0.95"
    ]
