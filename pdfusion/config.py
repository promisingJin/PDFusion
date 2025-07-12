"""
설정 파일 관리 및 사용자 입력 처리 모듈
"""

import os
import json
import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """설정 관리 클래스"""

    @staticmethod
    def get_user_input() -> Dict:
        """사용자로부터 병합 설정 입력 받기"""
        logger.info("사용자 입력 모드 시작")
        print("\n=== PDF 병합 설정 ===")

        # try 블록 제거, 내부 로직은 그대로 유지

        # 0. 책 제목(폴더명) 입력
        while True:
            book_title = input("책 제목(폴더명)을 입력하세요: ").strip()
            if book_title:
                break
            print("책 제목을 입력해주세요.")

        # 1. 전체 유닛 수
        while True:
            try:
                total_units = int(input("전체 유닛 수를 입력하세요 (예: 16): "))
                if total_units <= 0:
                    print("유닛 수는 1 이상이어야 합니다.")
                    continue
                break
            except ValueError:
                print("올바른 숫자를 입력해주세요.")

        logger.debug(f"전체 유닛 수: {total_units}")

        # 2. 카테고리 개수
        while True:
            try:
                num_categories = int(input("카테고리 개수를 입력하세요: "))
                if num_categories <= 0:
                    print("카테고리 개수는 1 이상이어야 합니다.")
                    continue
                break
            except ValueError:
                print("올바른 숫자를 입력해주세요.")

        logger.debug(f"카테고리 개수: {num_categories}")

        categories = {}

        # 3. 각 카테고리 정보 입력
        for i in range(num_categories):
            print(f"\n--- 카테고리 {i + 1} ---")

            # 카테고리 이름 입력
            while True:
                category_name = input("카테고리 이름: ").strip()
                if category_name:
                    break
                print("카테고리 이름을 입력해주세요.")

            # PDF 파일 경로 입력 및 검증
            while True:
                pdf_path = input("PDF 파일 경로: ").strip()
                if os.path.exists(pdf_path):
                    break
                print(f"파일을 찾을 수 없습니다: {pdf_path}")
                retry = input("다시 입력하시겠습니까? (y/n): ").lower()
                if retry != 'y':
                    logger.warning(f"존재하지 않는 파일 경로 사용: {pdf_path}")
                    break

            # 유닛당 페이지 수 입력
            while True:
                try:
                    pages_per_unit = int(input("유닛당 페이지 수: "))
                    if pages_per_unit <= 0:
                        print("페이지 수는 1 이상이어야 합니다.")
                        continue
                    break
                except ValueError:
                    print("올바른 숫자를 입력해주세요.")

            logger.debug(f"카테고리 {i + 1}: {category_name}, 경로: {pdf_path}, 페이지/유닛: {pages_per_unit}")

            categories[category_name] = {
                "pages_per_unit": pages_per_unit,
                "pdf_path": pdf_path
            }

        # 4. 병합 순서
        print(f"\n사용 가능한 카테고리: {list(categories.keys())}")
        while True:
            merge_order_str = input("병합 순서를 입력하세요 (쉼표로 구분): ").strip()
            if merge_order_str:
                merge_order = [cat.strip() for cat in merge_order_str.split(',')]
                # 입력된 카테고리 검증
                invalid_cats = [cat for cat in merge_order if cat not in categories]
                if invalid_cats:
                    print(f"다음 카테고리를 찾을 수 없습니다: {invalid_cats}")
                    continue
                break
            print("병합 순서를 입력해주세요.")

        logger.debug(f"병합 순서: {merge_order}")

        # 5. Review Test 설정
        has_review = input("\nReview Test가 있나요? (y/n): ").lower() == 'y'
        review_tests = []
        if has_review:
            num_review = int(input("Review Test 구간 개수: "))
            for i in range(num_review):
                print(f"--- Review Test 구간 {i+1} ---")
                while True:
                    unit_range = input("적용할 유닛 범위 (예: 1-4): ")
                    try:
                        start, end = map(int, unit_range.split('-'))
                        break
                    except Exception:
                        print("유닛 범위 입력이 올바르지 않습니다. 예: 1-4")
                pdf_path = input("PDF 파일 경로: ").strip()
                pages_per_unit = int(input("유닛당 페이지 수(기본 2): ") or 2)
                review_tests.append({
                    "units": list(range(start, end+1)),
                    "pdf_path": pdf_path,
                    "pages_per_unit": pages_per_unit
                })

        # 최종 config 반환
        return {
            "book_title": book_title,
            "total_units": total_units,
            "categories": categories,
            "merge_order": merge_order,
            "has_review": has_review,
            "review_tests": review_tests
        }