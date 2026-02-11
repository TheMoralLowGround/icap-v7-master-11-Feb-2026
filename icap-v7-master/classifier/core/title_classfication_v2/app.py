import asyncio
from collections import Counter

from core.title_classfication_v2.processing.classifier import (
    classify_documents,
    classify_documents_async,
)
from core.title_classfication_v2.utils import (
    is_sync_mode,
    extract_classified_pages,
    merge_chunked_results,
    normalize_prediction,
)
from core.title_classfication_v2.utils.logger import get_logger

logger = get_logger("app")

# =============================================================================
# ASYNC PROCESSING FUNCTIONS
# =============================================================================

async def process_single_file_async(file_text, system_prompt, user_prompt, chunk_size, overlap):
    """Process a single file's chunks in parallel."""
    n = len(file_text)

    # -----------------------------
    # SMALL FILE → process directly
    # -----------------------------
    if n <= chunk_size:
        joined_text = "\n".join(file_text)
        resp = await classify_documents_async(
            pages=joined_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        return extract_classified_pages(resp)

    # -------------------------------------
    # LARGE FILE → chunk-wise processing IN PARALLEL
    # -------------------------------------
    tasks = []
    start = 0

    while start < n:
        end = start + chunk_size
        actual_start = start - overlap if start != 0 else start
        chunk = file_text[actual_start:end]
        chunk_text = "\n".join(chunk)

        task = classify_documents_async(
            pages=chunk_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        tasks.append(task)
        start = end

    logger.info(f"Processing {len(tasks)} chunks in parallel...")
    chunk_responses = await asyncio.gather(*tasks)
    chunk_outputs = [extract_classified_pages(resp) for resp in chunk_responses]

    return merge_chunked_results(chunk_outputs)


async def process_chunk_with_voting_async(chunk_text, system_prompt, user_prompt, total_runs,
                                          enable_early_stopping=True):
    """Process a single chunk with majority voting across multiple runs."""
    if not enable_early_stopping or total_runs <= 2:
        tasks = [
            classify_documents_async(
                pages=chunk_text,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            for _ in range(total_runs)
        ]
        responses = await asyncio.gather(*tasks)
        predictions = [extract_classified_pages(resp) for resp in responses]

        counts = Counter(normalize_prediction(p) for p in predictions)
        best_pred_tuple, _ = counts.most_common(1)[0]
        return {label: list(pages) for label, pages in best_pred_tuple}

    predictions = []
    votes_needed = (total_runs // 2) + 1

    tasks = [
        classify_documents_async(
            pages=chunk_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        for _ in range(total_runs)
    ]

    for coro in asyncio.as_completed(tasks):
        response = await coro
        prediction = extract_classified_pages(response)
        predictions.append(prediction)

        if len(predictions) >= votes_needed:
            counts = Counter(normalize_prediction(p) for p in predictions)
            most_common_pred, count = counts.most_common(1)[0]

            if count >= votes_needed:
                remaining = total_runs - len(predictions)
                if remaining > 0:
                    logger.info(f"  [OK] Early stop: Majority achieved after {len(predictions)}/{total_runs} runs (saved {remaining} calls)")
                return {label: list(pages) for label, pages in most_common_pred}

    counts = Counter(normalize_prediction(p) for p in predictions)
    best_pred_tuple, _ = counts.most_common(1)[0]
    return {label: list(pages) for label, pages in best_pred_tuple}


async def process_file_with_voting_async(file_text, system_prompt, user_prompt,
                                         chunk_size, overlap, total_runs, enable_early_stopping=True):
    """Process a single file with majority voting, parallelizing across chunks and runs."""
    n = len(file_text)

    if n <= chunk_size:
        chunk_text = "\n".join(file_text)
        return await process_chunk_with_voting_async(chunk_text, system_prompt, user_prompt,
                                                     total_runs, enable_early_stopping)

    chunk_tasks = []
    start = 0

    while start < n:
        end = start + chunk_size
        actual_start = start - overlap if start != 0 else start
        chunk = file_text[actual_start:end]
        chunk_text = "\n".join(chunk)

        task = process_chunk_with_voting_async(chunk_text, system_prompt, user_prompt,
                                              total_runs, enable_early_stopping)
        chunk_tasks.append(task)
        start = end

    chunk_results = await asyncio.gather(*chunk_tasks)
    return merge_chunked_results(chunk_results)


async def predictLabel_async(all_files, system_prompt, user_prompt, chunk_size=9, overlap=1):
    """Async version: processes files and chunks in parallel."""
    try:
        logger.info(f"Processing {len(all_files)} files in parallel...")
        file_tasks = [
            process_single_file_async(file_text, system_prompt, user_prompt, chunk_size, overlap)
            for file_text in all_files
        ]

        final_outputs = await asyncio.gather(*file_tasks)
        return merge_chunked_results(final_outputs)

    except Exception as e:
        logger.error(f"Error: {e}")
        return []


async def predictLabelWithMajorityVoting_async(
    all_files, system_prompt, user_prompt,
    chunk_size=9, overlap=1, total_runs=5, enable_early_stopping=True
):
    """Async version: processes files with majority voting in parallel."""
    try:
        early_stop_msg = "with early stopping" if enable_early_stopping else "without early stopping"
        logger.info(f"Processing {len(all_files)} files in parallel with majority voting ({early_stop_msg})...")

        file_tasks = [
            process_file_with_voting_async(file_text, system_prompt, user_prompt,
                                          chunk_size, overlap, total_runs, enable_early_stopping)
            for file_text in all_files
        ]

        file_results = await asyncio.gather(*file_tasks)
        return merge_chunked_results(file_results)

    except Exception as e:
        logger.error(f"Error: {e}")
        return {}


# =============================================================================
# SYNC PROCESSING FUNCTIONS
# =============================================================================

def process_single_file_sync(file_text, system_prompt, user_prompt, chunk_size, overlap):
    """Process a single file's chunks sequentially."""
    n = len(file_text)

    if n <= chunk_size:
        joined_text = "\n".join(file_text)
        resp = classify_documents(
            pages=joined_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        return extract_classified_pages(resp)

    chunk_outputs = []
    start = 0

    while start < n:
        end = start + chunk_size
        actual_start = start - overlap if start != 0 else start
        chunk = file_text[actual_start:end]
        chunk_text = "\n".join(chunk)

        logger.info(f"Processing chunk {len(chunk_outputs)+1} (sync)...")
        resp = classify_documents(
            pages=chunk_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        chunk_outputs.append(extract_classified_pages(resp))
        start = end

    return merge_chunked_results(chunk_outputs)


def process_chunk_with_voting_sync(chunk_text, system_prompt, user_prompt, total_runs,
                                   enable_early_stopping=True):
    """Process a single chunk with majority voting sequentially."""
    predictions = []
    votes_needed = (total_runs // 2) + 1

    for run in range(total_runs):
        logger.info(f"  Voting run {run+1}/{total_runs} (sync)...")
        resp = classify_documents(
            pages=chunk_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        predictions.append(extract_classified_pages(resp))

        if enable_early_stopping and len(predictions) >= votes_needed:
            counts = Counter(normalize_prediction(p) for p in predictions)
            most_common_pred, count = counts.most_common(1)[0]
            if count >= votes_needed:
                remaining = total_runs - len(predictions)
                if remaining > 0:
                    logger.info(f"  [OK] Early stop: Majority achieved after {len(predictions)}/{total_runs} runs (saved {remaining} calls)")
                return {label: list(pages) for label, pages in most_common_pred}

    counts = Counter(normalize_prediction(p) for p in predictions)
    best_pred_tuple, _ = counts.most_common(1)[0]
    return {label: list(pages) for label, pages in best_pred_tuple}


def process_file_with_voting_sync(file_text, system_prompt, user_prompt, chunk_size, overlap,
                                  total_runs, enable_early_stopping=True):
    """Process a single file with majority voting sequentially."""
    n = len(file_text)

    if n <= chunk_size:
        chunk_text = "\n".join(file_text)
        return process_chunk_with_voting_sync(chunk_text, system_prompt, user_prompt,
                                              total_runs, enable_early_stopping)

    chunk_results = []
    start = 0
    chunk_num = 0

    while start < n:
        end = start + chunk_size
        actual_start = start - overlap if start != 0 else start
        chunk = file_text[actual_start:end]
        chunk_text = "\n".join(chunk)

        chunk_num += 1
        logger.info(f"Processing chunk {chunk_num} (sync)...")
        result = process_chunk_with_voting_sync(chunk_text, system_prompt, user_prompt,
                                                total_runs, enable_early_stopping)
        chunk_results.append(result)
        start = end

    return merge_chunked_results(chunk_results)


def predictLabel_sync(all_files, system_prompt, user_prompt, chunk_size=9, overlap=1):
    """Sync version: processes files and chunks sequentially."""
    try:
        logger.info(f"Processing {len(all_files)} files sequentially (sync mode)...")
        final_outputs = []
        for i, file_text in enumerate(all_files):
            logger.info(f"Processing file {i+1}/{len(all_files)} (sync)...")
            result = process_single_file_sync(file_text, system_prompt, user_prompt, chunk_size, overlap)
            final_outputs.append(result)

        return merge_chunked_results(final_outputs)

    except Exception as e:
        logger.error(f"Error: {e}")
        return []


def predictLabelWithMajorityVoting_sync(
    all_files, system_prompt, user_prompt,
    chunk_size=9, overlap=1, total_runs=5, enable_early_stopping=True
):
    """Sync version: processes files with majority voting sequentially."""
    try:
        early_stop_msg = "with early stopping" if enable_early_stopping else "without early stopping"
        logger.info(f"Processing {len(all_files)} files sequentially with majority voting ({early_stop_msg}, sync mode)...")

        file_results = []
        for i, file_text in enumerate(all_files):
            logger.info(f"Processing file {i+1}/{len(all_files)} (sync)...")
            result = process_file_with_voting_sync(
                file_text, system_prompt, user_prompt, chunk_size, overlap,
                total_runs, enable_early_stopping
            )
            file_results.append(result)

        return merge_chunked_results(file_results)

    except Exception as e:
        logger.error(f"Error: {e}")
        return {}


# =============================================================================
# PUBLIC API
# =============================================================================

def predictLabel(all_files, system_prompt, user_prompt, chunk_size=9, overlap=1):
    """
    Main prediction function. Uses sync or async based on SYNC_MODE env variable.

    Args:
        all_files: List of files, where each file is a list of page texts
        system_prompt: System prompt for classification
        user_prompt: User prompt for classification
        chunk_size: Number of pages per chunk (default: 9)
        overlap: Number of pages to overlap between chunks (default: 1)

    Returns:
        Dict with classification results
    """
    if is_sync_mode():
        return predictLabel_sync(all_files, system_prompt, user_prompt, chunk_size, overlap)
    return asyncio.run(predictLabel_async(all_files, system_prompt, user_prompt, chunk_size, overlap))


def predictLabelWithMajorityVoting(
    all_files, system_prompt, user_prompt,
    chunk_size=9, overlap=1, total_runs=5, enable_early_stopping=True
):
    """
    Main prediction function with majority voting.

    Args:
        all_files: List of files, where each file is a list of page texts
        system_prompt: System prompt for classification
        user_prompt: User prompt for classification
        chunk_size: Number of pages per chunk (default: 9)
        overlap: Number of pages to overlap between chunks (default: 1)
        total_runs: Number of voting runs per chunk (default: 5)
        enable_early_stopping: Stop early when majority achieved (default: True)

    Returns:
        Dict with classification results
    """
    if is_sync_mode():
        return predictLabelWithMajorityVoting_sync(
            all_files, system_prompt, user_prompt, chunk_size, overlap,
            total_runs, enable_early_stopping
        )
    return asyncio.run(predictLabelWithMajorityVoting_async(
        all_files, system_prompt, user_prompt, chunk_size, overlap,
        total_runs, enable_early_stopping
    ))
