"""Unit tests for the policy knowledge base and retrieval."""

from alibaba_mcp.application.policies import (
    POLICY_DOCUMENTS,
    get_policy,
    search_policies,
)


def test_corpus_has_expected_topics() -> None:
    topics = {e.topic for e in POLICY_DOCUMENTS}
    assert {"cancellation", "refund", "baggage"} <= topics


def test_get_policy_exact_slug() -> None:
    entry = get_policy("cancellation")
    assert entry is not None
    assert "cancellation" in entry.title.lower()


def test_get_policy_unknown_returns_none() -> None:
    assert get_policy("not-a-topic") is None


def test_search_ranks_cancellation_query() -> None:
    results = search_policies("cancellation rules refund penalty")
    assert results, "expected at least one hit"
    assert results[0].topic in {"cancellation", "refund"}


def test_search_baggage_query() -> None:
    results = search_policies("how much baggage can I check in?")
    assert results
    assert results[0].topic == "baggage"


def test_search_no_hits_returns_empty() -> None:
    assert search_policies("zzzqqqxyzzy") == []


def test_search_is_deterministic() -> None:
    q = "cancellation rules refund penalty"
    assert search_policies(q) == search_policies(q)
