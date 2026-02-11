"""
Services package for preprocess operations.

This package contains all service modules for PDF processing:
- detect_pdf: PDF detection and categorization
- electronic_pdf: PDF to RAJson conversion
- dense_page_detector: ML-based dense page detection
"""

from .detect_pdf import is_electronic_pdf
from .electronic_pdf import process_files

__all__ = [
    'is_electronic_pdf',
    'process_files',
]
