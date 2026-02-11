"""
Utilities for merging classification results and handling page ranges.
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from core.title_classfication_v2.schemas.models import ClassificationResponse


def extract_classified_pages(response: ClassificationResponse) -> Dict[str, List[Tuple[int, int]]]:
    """Extract classified pages from a ClassificationResponse into a dict of label -> page ranges."""
    result = defaultdict(list)
    for item in response.classes:
        for start, end in item.pages:
            result[item.label].append((start, end))
    return dict(result)


def find_label(chunk: Dict[str, List[Tuple[int, int]]], page: int) -> Optional[str]:
    """Find the label for a given page in a chunk's classification results."""
    for label, ranges in chunk.items():
        for s, e in ranges:
            if s <= page <= e:
                return label
    return None


def clean_conflicting_overlap(prev_chunk: Dict, label: str, start: int, end: int) -> List[Tuple[int, int]]:
    """Clean overlapping pages that have conflicting labels between chunks."""
    cleaned = []
    current_start = None

    for pg in range(start, end + 1):
        prev_label = find_label(prev_chunk, pg)

        # keep page if: no prev label OR same label
        if prev_label is None or prev_label == label:
            if current_start is None:
                current_start = pg
        else:
            if current_start is not None:
                cleaned.append((current_start, pg - 1))
                current_start = None

    if current_start is not None:
        cleaned.append((current_start, end))

    return cleaned


def merge_overlapping_only(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge only truly overlapping ranges (not adjacent ones)."""
    if not ranges:
        return []

    ranges = sorted(ranges, key=lambda x: x[0])
    merged = [ranges[0]]

    for s, e in ranges[1:]:
        last_s, last_e = merged[-1]

        # Merge only when ranges truly overlap
        if s <= last_e:  # NOT last_e + 1
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))

    return merged


def merge_chunked_results(chunked_results: List[Dict]) -> Dict[str, List[Tuple[int, int]]]:
    """Merge classification results from multiple chunks, resolving conflicts."""
    final = {}
    prev_chunk = None

    for chunk in chunked_results:
        if prev_chunk is None:
            for label, ranges in chunk.items():
                final[label] = ranges[:]
            prev_chunk = chunk
            continue

        for label, ranges in chunk.items():
            for start, end in ranges:
                cleaned = clean_conflicting_overlap(prev_chunk, label, start, end)
                for cs, ce in cleaned:
                    final.setdefault(label, []).append((cs, ce))

        prev_chunk = chunk

    # merge only overlapping ranges
    for label in final:
        final[label] = merge_overlapping_only(final[label])

    return final


def normalize_prediction(pred: dict) -> tuple:
    """Normalize a prediction dict for comparison/counting."""
    return tuple(
        (label, tuple(sorted(pages)))
        for label, pages in sorted(pred.items())
    )
