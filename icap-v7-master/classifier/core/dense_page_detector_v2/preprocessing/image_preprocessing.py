from pathlib import Path
import cv2
from PIL import Image
import numpy as np


class BasePreprocessor:
    def __init__(self):
        pass

    @staticmethod
    def load_image(img_path: Path, max_size: int = 1024) -> np.ndarray:
        img = Image.open(str(img_path)).convert("RGB")
        orig_w, orig_h = img.size
        scale = min(max_size / orig_w, max_size / orig_h)
        target_size = (int(orig_w * scale), int(orig_h * scale))
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return cv2.resize(img_bgr, target_size, interpolation=cv2.INTER_AREA)

    @staticmethod
    def normalize(img: np.ndarray) -> np.ndarray:
        return cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    @staticmethod
    def denoise(img: np.ndarray) -> np.ndarray:
        return cv2.bilateralFilter(img, 5, 55, 60)

    @staticmethod
    def to_grayscale(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def threshold(img_gray: np.ndarray) -> np.ndarray:
        return cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, 15, 10)

    @staticmethod
    def binarize_image(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 7, 2
        )
        return binary


class TextBloatPreprocessor(BasePreprocessor):
    @staticmethod
    def preprocess(img_path: Path, max_size: int = 1024) -> np.ndarray:
        img = BasePreprocessor.load_image(img_path, max_size)
        img = BasePreprocessor.normalize(img)
        img = BasePreprocessor.denoise(img)
        img = BasePreprocessor.to_grayscale(img)
        img = BasePreprocessor.threshold(img)
        return img


class TablePreprocessor(BasePreprocessor):
    @staticmethod
    def preprocess(img_path: Path, max_size: int = 1024) -> np.ndarray:
        r_img = BasePreprocessor.load_image(img_path, max_size)
        n_img = BasePreprocessor.normalize(r_img)
        b_img = BasePreprocessor.binarize_image(n_img)
        return r_img, b_img