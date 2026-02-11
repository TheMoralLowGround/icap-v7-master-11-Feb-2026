from pathlib import Path
import io
from typing import Dict, List, Any
from PIL import Image
import numpy as np
import math
from multiprocessing import current_process
from onnxtr.models import detection_predictor
from onnxtr.io import DocumentFile
from onnxtr.models.detection import db_mobilenet_v3_large

from ..preprocessing.image_preprocessing import TextBloatPreprocessor
from ..utils.logger import logger

class TableDetector:
    def __init__(self):
        self.preprocessor = TextBloatPreprocessor()
        self.FONT_THRESHOLD = [
            ("very_small", 8),
            ("small", 11),
            ("medium", 14),
            ("large", 20),
            ("very_large", math.inf),
        ]

    @staticmethod
    def _estimate_font_size(box_h: int, orig_h: int, resized_h: int, dpi: int = 400) -> float:
        scaled_h = box_h * (orig_h / resized_h)
        return round((scaled_h / dpi) * 72, 2)

    def get_word_classes(self, word_bboxes: List[List[int]], orig_h: int, resized_h: int) -> Dict[str, int]:
        word_classes = {k: 0 for k, _ in self.FONT_THRESHOLD}
        font_sizes = [self._estimate_font_size(b[3] - b[1], orig_h, resized_h) for b in word_bboxes]
        for size in font_sizes:
            for label, threshold in self.FONT_THRESHOLD:
                if size <= threshold:
                    word_classes[label] += 1
                    break
        return word_classes

    @staticmethod
    def morphological_closing(binary_img) -> np.ndarray:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        return cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)

    @staticmethod
    def merge_bboxes(bboxes, y_thresh=10, x_gap=15) -> List[List[int]]:
        """Merge word-level boxes into line-level boxes."""
        if not bboxes:
            return []

        bboxes = sorted(bboxes, key=lambda b: (b[1], b[0]))
        lines, current_line = [], [bboxes[0]]

        for box in bboxes[1:]:
            x1, y1, x2, y2 = box
            lx1, ly1, lx2, ly2 = current_line[-1]
            lcy = (ly1 + ly2) / 2
            cy = (y1 + y2) / 2

            if abs(cy - lcy) < y_thresh:  
                current_line.append(box)
            else:
                lines.append(current_line)
                current_line = [box]
        if current_line:
            lines.append(current_line)

        merged_bboxes = []
        for line in lines:
            line = sorted(line, key=lambda b: b[0])
            merged = [line[0]]
            for box in line[1:]:
                x1, y1, x2, y2 = box
                mx1, my1, mx2, my2 = merged[-1]
                if x1 - mx2 < x_gap:
                    merged[-1] = (mx1, min(my1, y1), max(mx2, x2), max(my2, y2))
                else:
                    merged.append(box)
            merged_bboxes.extend(merged)
        return merged_bboxes

    @staticmethod
    def get_connected_components(binary_img):
        """Extract connected components and their bounding boxes."""
        contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bboxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if w < 15 or h < 15 or area < 200:
                continue
            bboxes.append((x, y, x + w, y + h))

        return bboxes

    @staticmethod
    def extract_table_rois(binary_img, dilation_kernel=(50, 10), dilation_iter=2):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilation_kernel)
        dilated = cv2.dilate(binary_img, kernel, iterations=dilation_iter)
        return TableDetector.get_connected_components(dilated)

    @staticmethod
    def is_text_sparse(roi_box, word_bboxes, word_classes, coverage_thresh=0.45) -> bool:
        """Heuristic: is region table-like vs dense text?"""
        x1, y1, x2, y2 = roi_box
        roi_area = (x2 - x1) * (y2 - y1)
        if roi_area == 0:
            return True

        total_word_area = sum((x2 - x1) * (y2 - y1) for (x1, y1, x2, y2) in word_bboxes)
        total_word_count = len(word_bboxes)

        coverage = total_word_area / roi_area
        weighted_score = (
            (word_classes.get("very_small", 0) * 1.0 +
             word_classes.get("small", 0) * 0.8 +
             word_classes.get("medium", 0) * 0.5 +
             word_classes.get("large", 0) * 0.2 +
             word_classes.get("very_large", 0) * 0.1) / total_word_count
        ) if total_word_count else 0

        word_density = total_word_count / roi_area
        logger.debug(f"Coverage={coverage:.2f}, Density={word_density:.5f}, Score={weighted_score:.2f}")

        if (coverage > 0.5) or (coverage > 0.45 and word_density > 0.012) or (coverage > 0.40 and weighted_score > 0.70):
            return False
        return True

    @staticmethod
    def check_horizontal_vertical_alignment(text_blocks, vertical_thresh=0.5, horizontal_thresh=0.5) -> bool:
        """Check if blocks align into a table-like grid."""
        if len(text_blocks) < 2:
            return False
        x_centers = [(b[0] + b[2]) / 2 for b in text_blocks]
        y_centers = [(b[1] + b[3]) / 2 for b in text_blocks]
        avg_w = np.mean([b[2] - b[0] for b in text_blocks])
        avg_h = np.mean([b[3] - b[1] for b in text_blocks])

        # Horizontal lines
        horizontal_lines, prev_y, count = 0, sorted(y_centers)[0], 1
        for y in sorted(y_centers)[1:]:
            if abs(y - prev_y) < vertical_thresh * avg_h:
                count += 1
            else:
                if count >= 2:
                    horizontal_lines += 1
                count, prev_y = 1, y
        if count >= 2:
            horizontal_lines += 1

        # Vertical lines
        vertical_lines, prev_x, count = 0, sorted(x_centers)[0], 1
        for x in sorted(x_centers)[1:]:
            if abs(x - prev_x) < horizontal_thresh * avg_w:
                count += 1
            else:
                if count >= 2:
                    vertical_lines += 1
                count, prev_x = 1, x
        if count >= 2:
            vertical_lines += 1

        logger.debug(f"Horizontal lines={horizontal_lines}, Vertical lines={vertical_lines}")
        return horizontal_lines >= 2 and vertical_lines >= 2

    @staticmethod
    def is_table(roi_box, line_bboxes, word_bboxes, word_classes) -> bool:
        return TableDetector.check_horizontal_vertical_alignment(line_bboxes) and \
               TableDetector.is_text_sparse(roi_box, word_bboxes, word_classes)

    @staticmethod
    def is_two_column_page(line_bboxes, sep_multiplier=1.10, short_fraction_threshold=0.5) -> bool:
        """
        Detects if the page is two-column based on text line bounding line_bboxes.
        
        Args:
            line_bboxes: List of [xmin, ymin, xmax, ymax] for each text line.
            sep_multiplier: Multiplier for average line width to determine separation threshold (default: 1.49).
            short_fraction_threshold: Fraction of short lines above which it's considered a form/table, not columns (default: 0.4).
        
        Returns:
            bool: True if two-column, False otherwise.
        """
        if len(line_bboxes) < 4:
            return False
        
        # Check for too many short lines (indicative of forms/tables)
        page_width = max(b[2] for b in line_bboxes) - min(b[0] for b in line_bboxes)
        if page_width == 0:
            return False
        short_threshold = 0.2 * page_width
        widths = np.array([b[2] - b[0] for b in line_bboxes], dtype=float)
        num_short = np.sum(widths < short_threshold)
        logger.debug(f"Short lines: {num_short/len(line_bboxes)}, threshold: {short_fraction_threshold:.1f}")
        if num_short / len(line_bboxes) > short_fraction_threshold:
            return False
        
        centers = np.array([(b[0] + b[2]) / 2 for b in line_bboxes], dtype=float)
        centroids, _ = kmeans(centers, 2)
        if len(centroids) < 2:
            return False
        centroids = np.sort(centroids)
        sep = centroids[1] - centroids[0]
        
        # Require sufficient separation relative to page width
        logger.debug(f"Separation between columns: {sep:.1f}, Required: {0.25 * page_width:.1f}")
        if sep < 0.25 * page_width:
            return False
        
        code, _ = vq(centers, centroids)
        left_idx = np.where(code == 0)[0]
        right_idx = np.where(code == 1)[0]
        if len(left_idx) < 2 or len(right_idx) < 2:
            return False
        left_lines = [line_bboxes[i] for i in left_idx]
        right_lines = [line_bboxes[i] for i in right_idx]
        left_min_y = min(b[1] for b in left_lines)
        left_max_y = max(b[3] for b in left_lines)
        right_min_y = min(b[1] for b in right_lines)
        right_max_y = max(b[3] for b in right_lines)
    
        total_height = max(left_max_y, right_max_y) - min(left_min_y, right_min_y)
        if total_height == 0:
            return False
        
        avg_line_width = np.mean(widths)
        logger.debug(f"Sep: {sep:.1f}, Required: {sep_multiplier * max(250, avg_line_width):.1f}")
        if sep > max(250, sep_multiplier * avg_line_width):
            return True
        return False

    @staticmethod
    def _inside(inner_box, outer_box) -> bool:
        ix1, iy1, ix2, iy2 = inner_box
        ox1, oy1, ox2, oy2 = outer_box
        return ix1 >= ox1 and iy1 >= oy1 and ix2 <= ox2 and iy2 <= oy2

    def process(self, image_path: str, image_details: Dict[str, Any]) -> Dict[str, int]:
        logger.debug(f"Processing {image_path} for table detection.")
        image, image_binary = self.preprocessor.preprocess(image_path)
        image_morph = self.morphological_closing(image_binary)
        components = self.get_connected_components(image_morph)
        table_rois = self.extract_table_rois(image_morph)

        all_rois = list(components) + list(table_rois)

        word_bboxes = image_details.get("word_bboxes", [])
        logger.debug(f"{len(word_bboxes)} word boxes detected")

        line_bboxes = self.merge_bboxes(word_bboxes)
        logger.debug(f"{len(line_bboxes)} text boxes detected after merging")
        
        orig_h = image_details.get("orig_height", 1024)
        resized_h = image_details.get("resized_height", 1024)

        has_two_column = False
        has_table = False

        # First filter multi-column pages
        if self.is_two_column_page(line_bboxes):
            has_two_column = True
            logger.info(f"{image_path} is multi-column text page, skipping table detection.")
        else:
            for i, roi_box in enumerate(table_rois):
                filtered_lines = [b for b in line_bboxes if self._inside(b, roi_box) and (b[2]-b[0])>=25]
                filtered_words = [b for b in word_bboxes if self._inside(b, roi_box)]
                filtered_word_classes = self.get_word_classes(filtered_words, orig_h, resized_h)
                if self.is_table(roi_box, filtered_lines, filtered_words, filtered_word_classes):
                    logger.info(f"{image_path} contains table.")
                    has_table = True
                    break

        logger.debug(f"{image_path} - Two-column: {has_two_column}, Table: {has_table}")
        return {"has_two_column": int(has_two_column), "has_table": int(has_table)}

    def process_batch(self, dense_pages_details: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        results = {}
        for dense_page in dense_pages_details:
            for img_path, img_details in dense_page.items():
                try:
                    result = self.process(img_path, img_details)
                    results[img_path] = result
                except Exception as e:
                    logger.error(f"Failed processing {img_path}: {e}", exc_info=True)
        return results