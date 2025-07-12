"""
PDFusion - Unit별 PDF 자동 병합 도구
"""

__version__ = "2.0.0"
__author__ = "Uijin"
__email__ = ".com"

from .merger import PDFMerger
from .config import ConfigManager

__all__ = ["PDFMerger", "ConfigManager"]

def main():
    import logging
    from pathlib import Path
    logging.basicConfig(level=logging.INFO)
    print("\nPDFusion - 유닛별 PDF 자동 병합 도구\n")

    config_manager = ConfigManager()
    config = config_manager.get_user_input()

    # 책 제목(폴더명)으로 output 하위 폴더 지정
    output_dir = str(Path("output") / config["book_title"])
    merger = PDFMerger(output_dir=output_dir)

    # 병합용 config dict 생성 (review_tests 리스트 포함)
    merge_config = {
        "total_units": config["total_units"],
        "categories": config["categories"],
        "merge_order": config["merge_order"],
        "review_tests": config.get("review_tests", [])
    }

    # PDF 파일 검증
    if not merger.validate_pdf_files(merge_config):
        print("\n[실패] PDF 파일 검증에 실패했습니다. 오류를 수정 후 다시 시도하세요.")
        return

    # 병합 실행
    if merger.merge_all_units(merge_config):
        print("\n[완료] 모든 유닛 PDF 병합이 성공적으로 완료되었습니다.")
        # 전체 합본 PDF 자동 생성
        merger.merge_all_units_to_one(merge_config["total_units"])
    else:
        print("\n[실패] 병합 과정에서 오류가 발생했습니다. 로그를 확인하세요.")