"""
PDFusion - Unit별 PDF 자동 병합 도구
"""

__version__ = "2.0.0"
__author__ = "Uijin"
__email__ = ".com"

from .merger import PDFMerger
from .config import ConfigManager

__all__ = ["PDFMerger", "ConfigManager"]