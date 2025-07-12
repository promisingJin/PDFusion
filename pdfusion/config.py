"""
설정 파일 관리 및 사용자 입력 처리 모듈
"""

import os
import json
import logging
from typing import Dict
from pathlib import Path
import re
from glob import glob

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

        # 0-1. PDF가 들어있는 폴더 경로 입력
        while True:
            pdf_dir = input("PDF가 들어있는 폴더 경로를 입력하세요: ").strip()
            if os.path.isdir(pdf_dir):
                break
            print("폴더 경로가 올바르지 않습니다.")

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

        # 2. 카테고리 PDF 자동 탐색 및 카테고리명 추출
        book_prefix = book_title + "_"
        pdf_files = sorted(glob(os.path.join(pdf_dir, f"{book_prefix}*.pdf")))
        print(f"\n[디버그] 자동 탐색된 PDF 파일 목록:")
        for f in pdf_files:
            print(" -", os.path.basename(f))
        categories = {}
        for f in pdf_files:
            fname = os.path.basename(f)
            # 책이름_카테고리명.pdf 에서 카테고리명 추출
            cat = fname[len(book_prefix):-4] if fname.lower().endswith('.pdf') else fname[len(book_prefix):]
            categories[cat] = {"pdf_path": f}
        print(f"\n[디버그] 추출된 카테고리명:")
        for cat in categories:
            print(" -", cat)

        # 3. 병합 순서 입력
        print(f"\n[안내] Review Test 카테고리는 병합 순서에 넣지 않아도 자동으로 마지막 유닛에 붙습니다.")
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

        # 4. 각 카테고리 PDF에서 유닛별 페이지 인덱스 자동 분석
        def auto_detect_unit_pages(pdf_path, total_units):
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            unit_pages = {}
            unit1_indices = []
            current_unit = 1
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                m = re.search(r"[Uu]nit[\s]*([0-9]{1,2})", text)
                if m:
                    detected_unit = int(m.group(1))
                    if detected_unit == 1:
                        unit1_indices.append(i)
                    current_unit = detected_unit
                if current_unit not in unit_pages:
                    unit_pages[current_unit] = []
                unit_pages[current_unit].append(i)
            # Unit 1이 여러 번 감지된 경우, 실제 시작 인덱스 선택
            if len(unit1_indices) > 1:
                print(f"[디버그] {os.path.basename(pdf_path)}에서 Unit 1이 여러 번 감지되었습니다: {unit1_indices}")
                idx = input(f"실제 Unit 1의 시작 페이지 인덱스를 선택하세요 (기본: {unit1_indices[0]}): ").strip()
                try:
                    start_idx = int(idx) if idx else unit1_indices[0]
                except Exception:
                    start_idx = unit1_indices[0]
                # start_idx 이전 페이지는 모두 무시
                filtered_unit_pages = {}
                for u, pages in unit_pages.items():
                    filtered = [p for p in pages if p >= start_idx]
                    if filtered:
                        filtered_unit_pages[u] = filtered
                unit_pages = filtered_unit_pages
            print(f"[디버그] {os.path.basename(pdf_path)} 유닛별 페이지 인덱스:", unit_pages)
            if len(unit_pages) < total_units:
                print(f"[경고] {os.path.basename(pdf_path)}에서 감지된 유닛 수가 전체 유닛 수보다 적습니다.")
            return unit_pages
        # 각 카테고리별로 자동 분석
        for cat, info in categories.items():
            info["unit_pages_auto"] = auto_detect_unit_pages(info["pdf_path"], total_units)

        # 5. Review Test 자동 탐색 및 분석
        review_tests = []
        review_test_files = [f for f in pdf_files if 'review test' in os.path.basename(f).lower()]
        if not review_test_files:
            print("[안내] Review Test PDF가 탐지되지 않았습니다. Review Test 없이 병합을 진행합니다.")
        else:
            print(f"\n[디버그] 자동 탐색된 Review Test PDF:")
            for f in review_test_files:
                print(" -", os.path.basename(f))
            for f in review_test_files:
                fname = os.path.basename(f)
                # 예: Units 01-04 또는 Units 05-08 등에서 범위 추출
                m = re.search(r"Units?\s*(\d{1,2})\s*[-~]\s*(\d{1,2})", fname)
                if m:
                    start, end = int(m.group(1)), int(m.group(2))
                    review_tests.append({
                        "units": list(range(start, end+1)),
                        "pdf_path": f
                    })
            print(f"\n[디버그] Review Test 자동 분석 결과:")
            for r in review_tests:
                print(f" - 파일: {os.path.basename(r['pdf_path'])} → 마지막 유닛: {max(r['units'])}")
            # 사용자에게 자동 분석 결과 확인
            yn = input("이대로 Review Test를 적용할까요? (y/n): ").strip().lower()
            if yn != 'y':
                review_tests = []
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
                    review_tests.append({
                        "units": list(range(start, end+1)),
                        "pdf_path": pdf_path
                    })

        # 최종 config 반환
        return {
            "book_title": book_title,
            "pdf_dir": pdf_dir,
            "total_units": total_units,
            "categories": categories,
            "merge_order": merge_order,
            "has_review": True, # Review Test가 있으므로 True로 설정
            "review_tests": review_tests
        }