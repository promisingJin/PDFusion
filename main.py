#!/usr/bin/env python3
"""
PDFusion - PDF 자동 병합 프로그램
메인 진입점
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from pdfusion import main

if __name__ == "__main__":
    main()