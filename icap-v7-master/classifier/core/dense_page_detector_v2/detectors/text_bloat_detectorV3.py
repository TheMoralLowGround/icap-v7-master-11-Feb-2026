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

from core.dense_page_detector_v2.preprocessing.image_preprocessing import TextBloatPreprocessor
from core.dense_page_detector_v2.utils.logger import logger

class TextBloatDetector:
    def __init__(self, batch_size: int):
        self.model_name = "db_mobilenet_v3_large"
        self.model_path = "/app/core/model/onnxtr/db_mobilenet_v3_large_static_8_bit.onnx"
        self.FONT_THRESHOLD = [
            ("very_small", 8),
            ("small", 11),
            ("medium", 14),
            ("large", 20),
            ("very_large", math.inf),
        ]
        self.preprocessor = TextBloatPreprocessor()

        try:
            det_arch = db_mobilenet_v3_large(self.model_path)
            self.detect_model = detection_predictor(
                det_arch,
                assume_straight_pages=True,
                preserve_aspect_ratio=True,
                batch_size=batch_size
            )
        except Exception as e:
            logger.exception("Error loading pretrained model.")
            raise ValueError(f"Error loading pretrained model: {e}")

        self.model_type = "onnxtr"

    @staticmethod
    def _estimate_font_size(box_h: int, orig_h: int, resized_h: int, dpi: int = 400) -> float:
        scaled_h = box_h * (orig_h / resized_h)
        return round((scaled_h / dpi) * 72, 2)
    
    @staticmethod
    def count_text_blocks(word_bboxes, eps=50, min_samples=1):
        "Count number of text blocks (clusters) from word-level bounding boxes."
        if not word_bboxes:
            return 0, np.array([])

        word_bboxes = np.array(word_bboxes)
        
        # compute word centers (we cluster based on centers, could also use top-left)
        centers = np.column_stack([
            (word_bboxes[:, 0] + word_bboxes[:, 2]) / 2,  # cx
            (word_bboxes[:, 1] + word_bboxes[:, 3]) / 2   # cy
        ])
        
        # cluster using DBSCAN (density-based)
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
        
        labels = clustering.labels_
        num_blocks = len(set(labels)) - (1 if -1 in labels else 0)

        return num_blocks

    @staticmethod
    def _is_text_dense_binary(json_data: Dict, thresholds: Dict[str, float]) -> bool:

        text_blocks = json_data.get("text_blocks", 0)
        if text_blocks <= 10:
            return True
        
        coverage_percent = json_data["coverage_percent"]
        page_area = json_data["resized_width"] * json_data["resized_height"]
        word_density = json_data["total_word_count"] / page_area if page_area > 0 else 0

        word_classes = json_data["word_count"]
        total_word_count = json_data["total_word_count"]
        weighted_score = (
            (
                word_classes.get("very_small", 0) * 1.0
                + word_classes.get("small", 0) * 0.8
                + word_classes.get("medium", 0) * 0.5
                + word_classes.get("large", 0) * 0.2
                + word_classes.get("very_large", 0) * 0.1
            )
            / total_word_count
            if total_word_count > 0
            else 0
        )

        logger.debug(f"Total Word Count: {total_word_count} Coverage: {coverage_percent:.2f}, Word Density: {word_density:.5f}, Weighted Score: {weighted_score:.2f}")

        if (
            coverage_percent > thresholds.get("coverage_percent", 50)
            or (
                coverage_percent > thresholds.get("coverage_percent_low", 30)
                and word_density > thresholds.get("word_density", 0.01)
            )
            or (
                coverage_percent > thresholds.get("coverage_percent_medium", 20)
                and weighted_score > thresholds.get("weighted_score", 0.7)
            )
        ):
            return True
        return False

    def process_batch(self, image_paths: List[Path], thresholds: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """Process a batch of images and return their text density status safely."""
        results = {}
        buffers, sizes = [], {}

        for image_path in image_paths:
            try:
                with Image.open(str(image_path)) as orig_img:
                    orig_w, orig_h = orig_img.size

                img_final = self.preprocessor.preprocess(image_path)
                image_pil = Image.fromarray(img_final).convert("RGB")
                resized_h, resized_w = np.array(image_pil).shape[:2]

                buffer = io.BytesIO()
                image_pil.save(buffer, format="PNG")
                buffer.seek(0)

                buffers.append(buffer.read())
                sizes[image_path] = (orig_h, resized_h, resized_w)
                
                orig_img.close()
                image_pil.close()
                del img_final, image_pil
            except Exception as e:
                logger.warning(f"Skipping {image_path.name}: {e}", exc_info=True)

        if not buffers:
            return results  # no valid images

        try:
            doc = DocumentFile.from_images(buffers)
            predictions = self.detect_model(doc)
        except Exception as e:
            logger.error(f"Model inference failed in {current_process().name}: {e}", exc_info=True)
            return results

        for image_path, words_data in zip(image_paths, predictions):
            try:
                orig_h, resized_h, resized_w = sizes[image_path]
                page_area = resized_h * resized_w

                total_text_area, word_count = 0, 0
                word_classes = {k: 0 for k, _ in self.FONT_THRESHOLD}
                
                word_bboxes = []

                for word in words_data:
                    try:
                        x_min, y_min, x_max, y_max, _ = word
                        x1, y1 = int(x_min * resized_w), int(y_min * resized_h)
                        x2, y2 = int(x_max * resized_w), int(y_max * resized_h)
                        box_w, box_h = x2 - x1, y2 - y1
                        if box_w < 5 or box_h < 5:
                            continue
                        word_bboxes.append([x1, y1, x2, y2])
                        total_text_area += box_w * box_h
                        word_count += 1
                        font_size = self._estimate_font_size(box_h, orig_h, resized_h)
                        for class_name, threshold in self.FONT_THRESHOLD:
                            if font_size <= threshold:
                                word_classes[class_name] += 1
                                break
                    except Exception:
                        continue

                coverage_percent = (total_text_area / page_area) * 100
                text_blocks = self.count_text_blocks(word_bboxes)
                json_data = {
                    "file_name": str(image_path.resolve()),
                    "orig_height": orig_h,
                    "orig_width": orig_w,
                    "resized_width": resized_w,
                    "resized_height": resized_h,
                    "total_text_area": total_text_area,
                    "total_word_count": word_count,
                    "word_count": word_classes,
                    "word_bboxes": word_bboxes,
                    "text_blocks": text_blocks,
                    "coverage_percent": round(coverage_percent, 2),
                }

                json_data["is_text_dense"] = int(self._is_text_dense_binary(json_data, thresholds))
                
                results[str(image_path.resolve())] = json_data
                logger.debug(f"Processed {image_path.name}: {json_data['is_text_dense']}")

            except Exception as e:
                logger.warning(f"Failed on {image_path.name}: {e}", exc_info=True)

        return results