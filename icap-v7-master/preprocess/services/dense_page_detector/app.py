from pathlib import Path
from typing import Dict, List

from .detectors.text_bloat_detector import TextBloatDetector
from .detectors.table_detector import TableDetector
from .utils.logger import logger

text_bloat_detector = None
table_detector = None


def init_models(batch_size: int = 4):
    """Initialize TextBloatDetector and TableDetector once."""
    global text_bloat_detector, table_detector
    try:
        text_bloat_detector = TextBloatDetector(batch_size=batch_size)
        table_detector = TableDetector()
        logger.info("Initialized TextBloatDetector and TableDetector.")
    except Exception as e:
        logger.exception(f"Failed to initialize models: {e}")
        raise


def process_batch(batch_paths: List[Path], thresholds: Dict[str, float]) -> Dict[str, dict]:
    """Safe wrapper around text_bloat_detector.process_batch."""
    global text_bloat_detector, table_detector
    try:
        text_bloat_result = text_bloat_detector.process_batch(batch_paths, thresholds)
        dense_page_images = [{k: v} for k, v in text_bloat_result.items() if v.get("is_text_dense")]
        table_results = table_detector.process_batch(dense_page_images)
        merged_results = {}
        for path, tb_result in text_bloat_result.items():
            merged_results[str(path)] = {**tb_result, **table_results.get(str(path), {})}

        return merged_results

    except Exception as e:
        logger.error(f"Batch failed: {e}", exc_info=True)
        return {}


def detect_dense_pages(
    img_folders: List[Path],
    thresholds: Dict[str, float] = None,
    supported_formats=(".tiff", ".tif", ".png"),
) -> Dict[str, int]:
    """Detect dense pages in a set of images serially."""
    if thresholds is None:
        thresholds = {
            "coverage_percent": 50,
            "coverage_percent_low": 30,
            "coverage_percent_medium": 20,
            "word_density": 0.01,
            "weighted_score": 0.7,
        }

    image_files = [
        p
        for img_folder in img_folders
        for p in img_folder.rglob("*")
        if p.is_file() and p.suffix.lower() in supported_formats
    ]
    logger.info(f"Found {len(image_files)} images to process.")

    if not image_files:
        return {}

    batch_size = 1
    logger.info(f"Using batch size {batch_size} for serial processing.")

    # Initialize models once
    init_models(batch_size=batch_size)

    img_details = {}
    batches = [image_files[i : i + batch_size] for i in range(0, len(image_files), batch_size)]

    # Process batches serially
    results = []
    for batch in batches:
        batch_result = process_batch(batch, thresholds)
        results.append(batch_result)

    for batch_result in results:
        for img_path_str, output in batch_result.items():
            if output.get("is_text_dense"):
                if output.get("has_table"):
                    img_details[img_path_str] = 0
                else:
                    img_details[img_path_str] = 1
            else:
                img_details[img_path_str] = 0

    logger.info(f"Processed {len(img_details)} images successfully.")
    return img_details