#!/usr/bin/env python3
"""
PDFusion - PDF 자동 병합 프로그램 (ver_5)
메인 진입점
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from pdfusion.config_v5 import ConfigManagerV5
from pdfusion.merger import PDFMerger

if __name__ == "__main__":
    import logging
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    print("\n" + "="*60)
    print("PDFusion - 유닛별 PDF 자동 병합 도구 (ver_5)")
    print("="*60)
    print("[확인] config_v5.py 사용 중\n")

    config_manager = ConfigManagerV5()
    configs = config_manager.get_user_input()

    # 여러 책을 처리하는 경우
    for book_title, book_config in configs.items():
        print(f"\n{'='*60}")
        print(f"[책: {book_title}] 병합 시작")
        if book_config.get('book_type'):
            print(f"책 타입: {book_config['book_type']}")
        if book_config.get('level'):
            print(f"레벨: {book_config['level']}")
        print(f"{'='*60}")
        
        output_dir = str(Path("output") / book_title)
        merger = PDFMerger(output_dir=output_dir)

        # 병합용 config dict 생성
        merge_config = {
            "total_units": book_config["total_units"],
            "categories": book_config["categories"],
            "merge_order": book_config["merge_order"],
            "review_tests": book_config.get("review_tests", [])
        }

        # PDF 파일 검증
        if not merger.validate_pdf_files(merge_config):
            print(f"\n[실패] {book_title} PDF 파일 검증에 실패했습니다. 오류를 수정 후 다시 시도하세요.")
            continue

        # 병합 실행
        if merger.merge_all_units(merge_config):
            print(f"\n[완료] {book_title} 모든 유닛 PDF 병합이 성공적으로 완료되었습니다.")
            # 전체 합본 PDF 자동 생성
            merger.merge_all_units_to_one(merge_config["total_units"])
        else:
            print(f"\n[실패] {book_title} 병합 과정에서 오류가 발생했습니다. 로그를 확인하세요.")
