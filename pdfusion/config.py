"""
설정 파일 관리 및 사용자 입력 처리 모듈
"""

import os
import json
import logging
from typing import Dict
from pathlib import Path
import re
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class ConfigManager:
    """설정 관리 클래스"""

    @staticmethod
    def get_user_input() -> Dict:
        """사용자로부터 병합 설정 입력 받기"""
        logger.info("사용자 입력 모드 시작")
        print("\n=== PDF 병합 설정 ===")

        # 0. 최상위 폴더 입력
        while True:
            root_dir = input("최상위 폴더 경로를 입력하세요: ").strip()
            if os.path.isdir(root_dir):
                break
            print("폴더 경로가 올바르지 않습니다.")

        # 1. 책 제목별 하위 폴더 자동 탐색
        book_folders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
        print(f"\n[책 제목 폴더 자동 탐색 결과]")
        for idx, f in enumerate(book_folders, 1):
            print(f"{idx}. {f}")
        # 책 선택 단계 추가
        selected = input("이번에 병합할 책의 번호(또는 이름)를 입력하세요 (여러 개 선택 시 쉼표로 구분, Enter 시 전체 선택): ").strip()
        if selected:
            selected_indices_or_names = [s.strip() for s in selected.split(',') if s.strip()]
            selected_folders = []
            for s in selected_indices_or_names:
                if s.isdigit():
                    idx = int(s) - 1
                    if 0 <= idx < len(book_folders):
                        selected_folders.append(book_folders[idx])
                elif s in book_folders:
                    selected_folders.append(s)
                else:
                    print(f"[경고] '{s}'는 목록에 없는 책입니다. 무시됩니다.")
            if selected_folders:
                book_folders = selected_folders
            else:
                print("[경고] 선택된 책이 없습니다. 전체 책을 대상으로 진행합니다.")
        # 2. 각 책 폴더별로 병합 진행
        configs = {}
        for book_title in book_folders:
            print(f"\n[책: {book_title}] 처리 시작")
            book_path = os.path.join(root_dir, book_title)
            # prac book/Prac book 폴더 탐색
            prac_candidates = [d for d in os.listdir(book_path) if os.path.isdir(os.path.join(book_path, d)) and d.lower().replace(' ', '') == 'pracbook']
            if not prac_candidates:
                print(f"[경고] {book_title} 폴더 내 prac book 폴더를 찾을 수 없습니다. 건너뜁니다.")
                continue
            prac_dir_path = Path(book_path) / prac_candidates[0]
            # Actual Test 폴더 유무 확인
            actual_test_exists = any('actual test' in d.lower() for d in os.listdir(book_path) if os.path.isdir(os.path.join(book_path, d)))
            # prac book 내 PDF 파일 목록 (재귀 탐색)
            pdf_paths = list(prac_dir_path.rglob("*.pdf"))
            # answer 포함 파일 제외
            pdf_paths = [p for p in pdf_paths if 'answer' not in p.name.lower()]
            # review test 포함/제외
            review_test_paths = [p for p in pdf_paths if 'review test' in p.name.lower()]
            if actual_test_exists:
                print("[안내] Actual Test 폴더가 있으므로 Review Test PDF도 병합에 포함합니다.")
                filtered_paths = pdf_paths
            else:
                print("[안내] Actual Test 폴더가 없으므로 Review Test PDF는 병합에서 제외합니다.")
                filtered_paths = [p for p in pdf_paths if p not in review_test_paths]
            print(f"[디버그] 병합 후보 파일 목록:")
            numbered_paths = list(filtered_paths)
            for idx, p in enumerate(numbered_paths, 1):
                print(f"{idx}. {p.relative_to(prac_dir_path)}")
            # 사용자에게 최종 확인
            yn = input("이대로 병합할까요? (y/n): ").strip().lower()
            if yn != 'y':
                print("제외할 파일 번호 또는 파일명을 입력하세요 (예: -3, -5, -파일명, Enter=종료)")
                print("- 파일명 앞에 -를 붙이면 해당 파일은 제외됩니다. 번호/파일명 혼용 가능. 여러 번 나누어 입력할 수 있습니다.")
                exclude_set = set()
                include_set = set()
                while True:
                    sel = input(", ").strip()
                    if not sel:
                        break
                    selected = [s.strip() for s in sel.split(',') if s.strip()]
                    invalid_files = []
                    for s in selected:
                        is_exclude = s.startswith('-')
                        target = s[1:].strip() if is_exclude else s.strip()
                        # 번호 입력 지원
                        if target.isdigit():
                            idx = int(target) - 1
                            if 0 <= idx < len(numbered_paths):
                                file_path = numbered_paths[idx]
                            else:
                                invalid_files.append(target)
                                continue
                        else:
                            # 파일명 입력
                            match = None
                            for p in numbered_paths:
                                if str(p.relative_to(prac_dir_path)) == target:
                                    match = p
                                    break
                            if match:
                                file_path = match
                            else:
                                invalid_files.append(target)
                                continue
                        if is_exclude:
                            exclude_set.add(file_path.resolve())
                        else:
                            include_set.add(file_path.resolve())
                    if invalid_files:
                        print(f"일치하지 않는 파일/번호가 있습니다: {invalid_files}")
                        print("다시 입력해 주세요.")
                        continue
                    more = input("더 입력할 것이 있나요? (y/n): ").strip().lower()
                    if more != 'y':
                        break
                if include_set:
                    filtered_paths = [p for p in filtered_paths if p.resolve() in include_set]
                elif exclude_set:
                    filtered_paths = [p for p in filtered_paths if p.resolve() not in exclude_set]
                # 아무것도 입력하지 않으면 전체 포함
            print(f"[최종 병합 파일 목록]")
            for p in filtered_paths:
                print("-", p.relative_to(prac_dir_path))
            # categories 자동 생성 (유닛별 파일/통합 파일 구분 및 unit_page_lengths 리스트)
            categories = {}
            unit_counts_set = set()
            unit_page_lengths_dict = {}
            # 1. 유닛별 파일(예: Unit Test) 자동 인식
            unit_file_pattern = re.compile(r"unit[ _-]?(\d{1,2})", re.IGNORECASE)
            unit_files = {}
            other_files = []
            for p in filtered_paths:
                m = unit_file_pattern.search(p.name)
                if m:
                    unit_num = int(m.group(1))
                    unit_files[unit_num] = p
                else:
                    other_files.append(p)
            # 2. 유닛별 파일 처리
            if unit_files:
                sorted_units = sorted(unit_files.keys())
                unit_page_lengths = []
                pdf_paths = []
                for u in sorted_units:
                    path = unit_files[u]
                    try:
                        reader = PdfReader(str(path))
                        page_count = len(reader.pages)
                    except Exception:
                        page_count = 0
                    unit_page_lengths.append(page_count)
                    pdf_paths.append(str(path))
                cat_name = 'Unit Test'  # 또는 폴더명/패턴에서 추출
                categories[cat_name] = {
                    "pdf_paths": pdf_paths,
                    "unit_page_lengths": unit_page_lengths
                }
                unit_counts_set.add(len(unit_page_lengths))
                unit_page_lengths_dict[cat_name] = unit_page_lengths
            # 3. 통합 파일(한 파일에 여러 유닛) 처리
            def is_toc_page(text):
                """목차 페이지인지 더 엄격하게 확인"""
                toc_keywords = [
                    '목차', 'contents', 'table of contents', 'index'
                ]
                text_lower = text.lower()
                # 키워드 기반
                if any(keyword in text_lower for keyword in toc_keywords):
                    return True
                # 구조 기반: 한 페이지에 Unit 1, Unit 2 등 여러 유닛이 나열되어 있으면 목차로 간주
                unit_matches = re.findall(r'unit\s*\d{1,2}', text_lower)
                if len(set(unit_matches)) >= 3:  # 3개 이상 유닛이 한 페이지에 있으면 목차로 추정
                    return True
                return False
            
            def extract_unit_page_lengths(pdf_path):
                # 더 유연한 유닛 패턴: Unit 1, Unit 1-, Unit 1 - 등 다양한 형태 지원
                # U nit, Un it 등 분리된 형태도 지원
                unit_pattern = re.compile(r'u\s*n\s*i\s*t\s*[\.:∙-]?\s*(\d{1,2})', re.IGNORECASE)
                
                def normalize_text(text):
                    """PDF 텍스트 정규화: 불필요한 줄바꿈과 공백 제거"""
                    # 줄바꿈을 공백으로 변환
                    text = text.replace('\n', ' ')
                    # 연속된 공백을 하나로
                    text = re.sub(r'\s+', ' ', text)
                    # 앞뒤 공백 제거
                    text = text.strip()
                    
                    # "U nit" -> "Unit" 같은 패턴 수정
                    # 단어 사이의 불필요한 공백 제거 (특히 Unit 패턴)
                    text = re.sub(r'U\s+n\s*i\s+t', 'Unit', text, flags=re.IGNORECASE)
                    text = re.sub(r'U\s+nit', 'Unit', text, flags=re.IGNORECASE)
                    text = re.sub(r'Un\s+it', 'Unit', text, flags=re.IGNORECASE)
                    text = re.sub(r'Uni\s+t', 'Unit', text, flags=re.IGNORECASE)
                    
                    return text
                try:
                    reader = PdfReader(str(pdf_path))
                    
                    # 목차 페이지 감지
                    first_page_text = reader.pages[0].extract_text() or ""
                    is_toc = is_toc_page(first_page_text)
                    
                    if is_toc:
                        print(f"[안내] 카테고리: {os.path.basename(str(pdf_path))}")
                        print(f"[안내] 첫 번째 페이지가 목차로 감지되었습니다.")
                        print(f"미리보기: {first_page_text[:200]}...")
                        confirm = input("목차 페이지를 제외하시겠습니까? (y/n): ").strip().lower()
                        start_page = 1 if confirm == 'y' else 0
                    else:
                        start_page = 0
                    
                    unit_indices = []
                    unit_numbers = []
                    last_unit_num = None
                    print(f"[디버그] {os.path.basename(str(pdf_path))} 각 페이지별 유닛 인식 결과:")
                    
                    # 첫 페이지에서 unit 감지 안되고, 두 번째 페이지에서 unit 감지되면 첫 두 페이지를 합쳐 하나의 유닛으로 처리
                    first_unit_found = False
                    for i, page in enumerate(reader.pages[start_page:], start_page):
                        raw_text = page.extract_text() or ""
                        
                        # 텍스트 추출이 실패한 경우 대안 방법 시도
                        if not raw_text.strip():
                            print(f"- {i+1}페이지: 텍스트 추출 실패, 대안 방법 시도...")
                            # 페이지의 첫 번째 부분을 다시 시도
                            try:
                                # 페이지의 상단 부분만 추출 시도
                                raw_text = page.extract_text() or ""
                                if not raw_text.strip():
                                    print(f"  텍스트 추출 완전 실패")
                                    continue
                            except Exception as e:
                                print(f"  텍스트 추출 오류: {e}")
                                continue
                        
                        # 텍스트 정규화
                        text = normalize_text(raw_text)
                        found = unit_pattern.search(text)
                        preview = text[:80]
                        
                        # 더 상세한 디버깅 정보 추가
                        print(f"- {i+1}페이지: 원본 텍스트 길이={len(raw_text)}")
                        print(f"  원본 텍스트 (처음 200자): {raw_text[:200]}")
                        print(f"  정규화된 텍스트 (처음 200자): {text[:200]}")
                        print(f"  패턴 매칭 결과: {found}")
                        if found:
                            print(f"  매칭된 텍스트: '{found.group(0)}'")
                            print(f"  추출된 유닛 번호: {found.group(1)}")
                        
                        if found:
                            unit_num = int(found.group(1))
                            if not first_unit_found and i == start_page + 1 and len(unit_indices) == 0:
                                # 첫 페이지에서 unit 감지 안되고, 두 번째에서 감지 → 첫 두 페이지를 하나의 유닛으로
                                unit_indices.append(start_page)
                                unit_numbers.append(unit_num)
                                last_unit_num = unit_num
                                first_unit_found = True
                                print(f"- {i}페이지: (첫 페이지+두 번째 페이지 합침) 유닛 시작 감지! → '{found.group(0)}' (Unit {unit_num}) / 미리보기: {preview}")
                            elif unit_num != last_unit_num:
                                unit_indices.append(i)
                                unit_numbers.append(unit_num)
                                last_unit_num = unit_num
                                print(f"- {i+1}페이지: 유닛 시작 감지! → '{found.group(0)}' (Unit {unit_num}) / 미리보기: {preview}")
                            else:
                                print(f"- {i+1}페이지: (동일 유닛 {unit_num}) / 미리보기: {preview}")
                        else:
                            print(f"- {i+1}페이지: (유닛 없음) / 미리보기: {preview}")
                    
                    # 유닛 순서 검증
                    if unit_numbers:
                        print(f"[디버그] 감지된 유닛 순서: {unit_numbers}")
                        for i, unit_num in enumerate(unit_numbers):
                            expected_unit = i + 1
                            if unit_num != expected_unit:
                                print(f"[경고] Unit {unit_num}이 {expected_unit}번째 위치에 있습니다.")
                                print("유닛 순서가 올바르지 않을 수 있습니다.")
                    
                    if not unit_indices:
                        print(f"[디버그] {os.path.basename(str(pdf_path))}에서 유닛이 감지되지 않았습니다.")
                        print("이 파일은 유닛별로 분리되어 있지 않을 수 있습니다.")
                        manual_input = input("유닛 수를 직접 입력하시겠습니까? (y/n): ").strip().lower()
                        if manual_input == 'y':
                            try:
                                unit_count = int(input("유닛 수를 입력하세요: "))
                                total_pages = len(reader.pages) - start_page
                                pages_per_unit = total_pages // unit_count
                                unit_page_lengths = [pages_per_unit] * unit_count
                                # 나머지 페이지는 마지막 유닛에 추가
                                remainder = total_pages % unit_count
                                if remainder > 0:
                                    unit_page_lengths[-1] += remainder
                                print(f"[디버그] 수동 입력 결과: {unit_page_lengths}")
                                return unit_page_lengths
                            except ValueError:
                                print("올바른 숫자를 입력해주세요.")
                        print("[디버그] 유닛 시작이 감지되지 않아 전체를 한 유닛으로 간주합니다.")
                        return [len(reader.pages) - start_page]
                    
                    unit_indices.append(len(reader.pages))
                    unit_page_lengths = [unit_indices[i+1] - unit_indices[i] for i in range(len(unit_indices)-1)]
                    print(f"[디버그] 최종 unit_page_lengths: {unit_page_lengths}")
                    return unit_page_lengths
                except Exception as e:
                    print(f"[디버그] PDF 텍스트 추출 오류: {e}")
                    return []
            review_tests = [] # 별도로 저장할 Review Test 리스트
            for p in other_files:
                # Review Test 파일은 categories에서 제외하고 별도로 review_tests 리스트에 추가
                if 'review test' in p.name.lower():
                    print(f"[디버그] Review Test 파일 처리: {p.name}")
                    # 파일명에서 구간 추출 (예: Units 01-04)
                    m = re.search(r'Units?[\s_]*(\d{1,2})[\s\-~]+(\d{1,2})', p.name)
                    if m:
                        start_unit = int(m.group(1))
                        end_unit = int(m.group(2))
                        print(f"[디버그] Review Test 구간: {start_unit}-{end_unit}")
                    else:
                        start_unit = end_unit = 1
                    try:
                        reader = PdfReader(str(p))
                        total_pages = len(reader.pages)
                        # Review Test는 categories에 추가하지 않고 별도 리스트에만 추가
                        review_tests.append({
                            "cat_name": p.stem,
                            "pdf_path": str(p),
                            "unit_page_lengths": [total_pages],
                            "start_unit": start_unit,
                            "end_unit": end_unit
                        })
                    except Exception as e:
                        print(f"[경고] Review Test 파일 읽기 오류: {e}")
                    continue
                unit_page_lengths = extract_unit_page_lengths(p)
                cat_name = p.stem
                categories[cat_name] = {
                    "pdf_path": str(p),
                    "unit_page_lengths": unit_page_lengths
                }
                unit_counts_set.add(len(unit_page_lengths))
                unit_page_lengths_dict[cat_name] = unit_page_lengths
            # 4. 유닛 수 일치 검증 전, 각 카테고리별 유닛 수/리스트 로그 출력 및 사용자 확인
            print("[디버그] 카테고리별 유닛 수 및 unit_page_lengths:")
            for cat, upl in unit_page_lengths_dict.items():
                print(f"- {cat}: 유닛 수={len(upl)}, unit_page_lengths={upl}")
            while True:
                yn = input("위 유닛 수/구성이 맞습니까? (y/n): ").strip().lower()
                if yn == 'y' or yn == '':
                    break
                # 사용자 입력으로 unit_page_lengths 보정
                for cat in categories.keys():
                    upl_str = input(f"[{cat}] 유닛별 페이지 수를 쉼표로 입력하세요 (예: 1,1,1,1,1,1,1,1): ").strip()
                    try:
                        upl = [int(x) for x in upl_str.split(',') if x.strip()]
                        categories[cat]["unit_page_lengths"] = upl
                        unit_page_lengths_dict[cat] = upl
                        unit_counts_set.add(len(upl))
                    except Exception:
                        print(f"[경고] 입력값이 올바르지 않습니다. 다시 시도하세요.")
                print("[수정 후 카테고리별 유닛 수 및 unit_page_lengths]:")
                for cat, upl in unit_page_lengths_dict.items():
                    print(f"- {cat}: 유닛 수={len(upl)}, unit_page_lengths={upl}")
            # Review Test 카테고리 자동 분리
            main_categories = {cat: upl for cat, upl in unit_page_lengths_dict.items() if 'review test' not in cat.lower()}
            review_categories = {cat: upl for cat, upl in unit_page_lengths_dict.items() if 'review test' in cat.lower()}
            # 메인 카테고리만 유닛 수 일치 검증
            if len(set(len(upl) for upl in main_categories.values())) != 1:
                print(f"[오류] (Review Test 제외) 모든 메인 카테고리의 유닛 수가 일치하지 않습니다: {[len(upl) for upl in main_categories.values()]}")
                raise ValueError("모든 메인 카테고리의 유닛 수가 일치해야 합니다.")
            total_units = list(main_categories.values())[0].__len__() if main_categories else 0
            # Review Test 카테고리는 별도 리스트로 저장
            # review_tests는 이미 자동 추출된 값이 있으면 사용, 없으면 빈 리스트
            
            # 병합 순서 입력 받기
            print(f"\n[병합 순서 설정]")
            print("다음 카테고리들이 감지되었습니다:")
            main_categories_list = list(main_categories.keys())
            for idx, cat in enumerate(main_categories_list, 1):
                print(f"{idx}. {cat}")
            
            while True:
                order_input = input("병합 순서를 번호로 입력하세요 (예: 1,2,3 또는 Enter=자동순서): ").strip()
                if not order_input:
                    # 자동 순서 사용
                    merge_order = main_categories_list
                    print(f"자동 순서 사용: {merge_order}")
                    break
                else:
                    try:
                        order_numbers = [int(x.strip()) for x in order_input.split(',') if x.strip()]
                        merge_order = []
                        for num in order_numbers:
                            if 1 <= num <= len(main_categories_list):
                                merge_order.append(main_categories_list[num-1])
                            else:
                                print(f"[경고] 번호 {num}는 유효하지 않습니다. 무시됩니다.")
                        
                        if merge_order:
                            print(f"설정된 병합 순서: {merge_order}")
                            break
                        else:
                            print("유효한 카테고리가 선택되지 않았습니다. 다시 입력해주세요.")
                    except ValueError:
                        print("올바른 숫자를 입력해주세요.")
            
            configs[book_title] = {
                "book_title": book_title,
                "total_units": total_units,
                "categories": categories,
                "merge_order": merge_order,
                "review_tests": review_tests
            }
        return configs