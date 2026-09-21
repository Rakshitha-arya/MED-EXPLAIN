"""Evaluation metrics module for OCR, extraction, retrieval, and generation performance."""
from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Sequence, Set, Union


def _levenshtein_distance(seq1: Sequence[Any], seq2: Sequence[Any]) -> int:
    """Calculate Levenshtein edit distance between two sequences."""
    m, n = len(seq1), len(seq2)
    if m == 0:
        return n
    if n == 0:
        return m

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost # substitution
            )
    return dp[m][n]


def compute_cer(reference_text: str, hypothesis_text: str) -> float:
    """Compute Character Error Rate (CER).

    CER = Levenshtein Distance (characters) / len(reference_text)
    """
    ref = str(reference_text or "").strip()
    hyp = str(hypothesis_text or "").strip()
    if not ref:
        return 0.0 if not hyp else 1.0

    distance = _levenshtein_distance(list(ref), list(hyp))
    return round(distance / len(ref), 4)


def compute_wer(reference_text: str, hypothesis_text: str) -> float:
    """Compute Word Error Rate (WER).

    WER = Levenshtein Distance (words) / len(reference_words)
    """
    ref_words = str(reference_text or "").strip().split()
    hyp_words = str(hypothesis_text or "").strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = _levenshtein_distance(ref_words, hyp_words)
    return round(distance / len(ref_words), 4)


def compute_precision(tp: int, fp: int) -> float:
    """Compute Precision: TP / (TP + FP)."""
    if (tp + fp) <= 0:
        return 0.0
    return round(tp / (tp + fp), 4)


def compute_recall(tp: int, fn: int) -> float:
    """Compute Recall: TP / (TP + FN)."""
    if (tp + fn) <= 0:
        return 0.0
    return round(tp / (tp + fn), 4)


def compute_f1(precision: float, recall: float) -> float:
    """Compute F1 Score: 2 * Precision * Recall / (Precision + Recall)."""
    if (precision + recall) <= 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def compute_recall_at_k(
    retrieved_ids: List[Any], ground_truth_ids: Union[Set[Any], List[Any]], k: int = 3
) -> float:
    """Compute Recall@K for a single query (1.0 if any ground-truth item in top-K else 0.0)."""
    if not retrieved_ids or not ground_truth_ids or k < 1:
        return 0.0
    gt_set = set(ground_truth_ids)
    top_k = retrieved_ids[:k]
    return 1.0 if any(item in gt_set for item in top_k) else 0.0


def compute_precision_at_k(
    retrieved_ids: List[Any], ground_truth_ids: Union[Set[Any], List[Any]], k: int = 3
) -> float:
    """Compute Precision@K for a single query."""
    if not retrieved_ids or not ground_truth_ids or k < 1:
        return 0.0
    gt_set = set(ground_truth_ids)
    top_k = retrieved_ids[:k]
    hits = sum(1 for item in top_k if item in gt_set)
    return round(hits / min(k, len(top_k)), 4)


def compute_mrr(
    retrieved_lists: List[List[Any]], ground_truth_sets: List[Union[Set[Any], List[Any]]]
) -> float:
    """Compute Mean Reciprocal Rank (MRR) across multiple query evaluations."""
    if not retrieved_lists or not ground_truth_sets or len(retrieved_lists) != len(ground_truth_sets):
        return 0.0

    reciprocal_ranks = []
    for retrieved, gt in zip(retrieved_lists, ground_truth_sets):
        gt_set = set(gt)
        rr = 0.0
        for rank, item in enumerate(retrieved, start=1):
            if item in gt_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4)


def mean(values: Iterable[float]) -> float:
    """Return a rounded arithmetic mean, or zero for an empty iterable."""
    numbers = list(values)
    return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


def evaluate_ranked_retrieval(
    evaluations: Iterable[Mapping[str, Any]], keys: Sequence[int] = (1, 3, 5)
) -> dict[str, float]:
    """Evaluate independently labelled ranked retrieval results.

    Each evaluation must provide ``retrieved_ids`` and ``relevant_ids``.  This
    deliberately does not infer relevance from the returned records: doing so
    would make a retrieval benchmark self-fulfilling rather than measured.
    """
    rows = list(evaluations)
    results: dict[str, float] = {}
    for key in keys:
        results[f"recall_at_{key}"] = mean(
            compute_recall_at_k(list(row["retrieved_ids"]), set(row["relevant_ids"]), key)
            for row in rows
        )
        results[f"precision_at_{key}"] = mean(
            compute_precision_at_k(list(row["retrieved_ids"]), set(row["relevant_ids"]), key)
            for row in rows
        )
    results["mrr"] = compute_mrr(
        [list(row["retrieved_ids"]) for row in rows],
        [set(row["relevant_ids"]) for row in rows],
    )
    return results
