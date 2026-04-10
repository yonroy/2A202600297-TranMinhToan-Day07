from __future__ import annotations
from pathlib import Path
import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
            if sentence.strip()
        ]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_text = " ".join(sentences[i : i + self.max_sentences_per_chunk]).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks
        # raise NotImplementedError("Implement SentenceChunker.chunk")


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        separators = self.separators if self.separators else [""]
        return [chunk for chunk in self._split(text.strip(), separators) if chunk.strip()]
        # raise NotImplementedError("Implement RecursiveChunker.chunk")

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        parts = [part for part in current_text.split(separator) if part]
        if len(parts) <= 1:
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        buffer = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue
            candidate = part if not buffer else buffer + separator + part

            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.extend(self._split(buffer, next_separators))

                if len(part) <= self.chunk_size:
                    buffer = part
                else:
                    chunks.extend(self._split(part, next_separators))
                    buffer = ""

        if buffer:
            if len(buffer) <= self.chunk_size:
                chunks.append(buffer)
            else:
                chunks.extend(self._split(buffer, next_separators))

        return [chunk.strip() for chunk in chunks if chunk.strip()]
        # raise NotImplementedError("Implement RecursiveChunker._split")


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    if not vec_a or not vec_b:
        return 0.0

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)
    # raise NotImplementedError("Implement compute_similarity")


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # TODO: call each chunker, compute stats, return comparison dict
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, max(0, chunk_size // 5))),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100)),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            avg_length = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0
            result[name] = {
                "count": len(chunks),
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return result
        # raise NotImplementedError("Implement ChunkingStrategyComparator.compare")

if __name__ == "__main__":
    # Example usage
    text = Path("data/ai_engineer.md").read_text(encoding="utf-8")
    
    comparator = ChunkingStrategyComparator()
    comparison = comparator.compare(text[:50000], chunk_size=500)
    print(comparison.keys())
    for strategy, stats in comparison.items():
        print(f"Strategy: {strategy}")
        print(f"  Count: {stats['count']}")
        print(f"  Average Length: {stats['avg_length']:.2f}")
        print(f"  Chunks: {stats['chunks']}\n")