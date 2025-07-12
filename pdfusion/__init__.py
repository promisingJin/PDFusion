"""
PDFusion - Unit별 PDF 자동 병합 도구
"""

__version__ = "2.0.0"
__author__ = "Uijin"
__email__ = "uijincrtw@gmail.com"

from .merger import PDFMerger
from .config import ConfigManager

__all__ = ["PDFMerger", "ConfigManager"]

def main():
    """PDFusion CLI 진입점"""
    import logging
    logging.basicConfig(level=logging.INFO)
    print("\nPDFusion - 유닛별 PDF 자동 병합 도구\n")

    config_manager = ConfigManager()
    merger = PDFMerger()

    # 사용자 입력을 받아 설정 생성
    config = config_manager.get_user_input()

    # 병합용 config 구조 변환
    # Review Test 관련 입력 처리
    review_test = {
        "enabled": False,
        "units": [],
        "pdf_path": None,
        "pages_per_unit": 2
    }
    if config.get("has_review"):
        review_test["enabled"] = True
        review_test["pdf_path"] = input("Review Test PDF 파일 경로: ").strip()
        review_test["pages_per_unit"] = int(input("Review Test 유닛당 페이지 수(기본 2): ") or 2)
        review_units_str = input("Review Test를 추가할 유닛 번호(쉼표로 구분): ").strip()
        if review_units_str:
            review_test["units"] = [int(u.strip()) for u in review_units_str.split(",") if u.strip().isdigit()]

    # 병합용 config dict 생성
    merge_config = {
        "total_units": config["total_units"],
        "categories": config["categories"],
        "merge_order": config["merge_order"],
        "review_test": review_test
    }

    # PDF 파일 검증
    if not merger.validate_pdf_files(merge_config):
        print("\n[실패] PDF 파일 검증에 실패했습니다. 오류를 수정 후 다시 시도하세요.")
        return

    # 병합 실행
    if merger.merge_all_units(merge_config):
        print("\n[완료] 모든 유닛 PDF 병합이 성공적으로 완료되었습니다.")
    else:
        print("\n[실패] 병합 과정에서 오류가 발생했습니다. 로그를 확인하세요.")