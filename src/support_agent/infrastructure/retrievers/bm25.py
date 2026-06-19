import math
import re
from collections import Counter
from collections.abc import Iterable

from support_agent.domain.documents import RetrievedChunk, SupportDocumentChunk


class BM25Retriever:
    """In-memory BM25 retriever for lexical matching over indexed chunks."""

    def __init__(self, chunks: Iterable[SupportDocumentChunk], k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = list(chunks)
        self._k1 = k1
        self._b = b
        self._tokenized = [self._tokenize(chunk.text) for chunk in self._chunks]
        self._term_frequencies = [Counter(tokens) for tokens in self._tokenized]
        self._doc_lengths = [len(tokens) for tokens in self._tokenized]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        )
        self._idf = self._build_idf()

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query.strip() or not self._chunks:
            return []

        query_terms = self._tokenize(query)
        scored = [
            RetrievedChunk(
                chunk=chunk,
                score=self._score(query_terms, index),
                retrieval_method="bm25",
            )
            for index, chunk in enumerate(self._chunks)
        ]
        return [result for result in sorted(scored, key=lambda item: item.score, reverse=True)[:top_k] if result.score > 0]

    def _build_idf(self) -> dict[str, float]:
        document_count = len(self._tokenized)
        document_frequencies: Counter[str] = Counter()
        for tokens in self._tokenized:
            document_frequencies.update(set(tokens))

        return {
            term: math.log(1 + (document_count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequencies.items()
        }

    def _score(self, query_terms: list[str], index: int) -> float:
        if self._avg_doc_length == 0:
            return 0.0

        score = 0.0
        term_frequency = self._term_frequencies[index]
        doc_length = self._doc_lengths[index]

        for term in query_terms:
            if term not in term_frequency:
                continue
            frequency = term_frequency[term]
            numerator = frequency * (self._k1 + 1)
            denominator = frequency + self._k1 * (
                1 - self._b + self._b * doc_length / self._avg_doc_length
            )
            score += self._idf.get(term, 0.0) * numerator / denominator
        return score

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())
