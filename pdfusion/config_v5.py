"""
설정 파일 관리 및 사용자 입력 처리 모듈 (ver_5)
압축 해제, LC/RC 감지, 레벨별 처리 통합
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
import re
from pypdf import PdfReader

from .extractor import ZipExtractor
from .book_type_detector import BookTypeDetector
from .level_config import LevelConfig
from .file_discovery import FileDiscovery

logger = logging.getLogger(__name__)


class ConfigManagerV5:
    """설정 관리 클래스 (ver_5)"""
    
    def __init__(self):
        self.extractor = ZipExtractor()
        self.book_type_detector = BookTypeDetector()
        self.level_config = LevelConfig()
        self.file_discovery = FileDiscovery()
    
    def get_user_input(self) -> Dict:
        """사용자로부터 병합 설정 입력 받기 (ver_5)"""
        logger.info("="*60)
        logger.info("사용자 입력 모드 시작 (ver_5)")
        logger.info("="*60)
        print("\n" + "="*60)
        print("=== PDF 병합 설정 (ver_5) ===")
        print("="*60)
        
        # 0. 최상위 폴더 입력
        while True:
            root_dir = input("최상위 폴더 경로를 입력하세요: ").strip()
            if os.path.isdir(root_dir):
                break
            print("폴더 경로가 올바르지 않습니다.")
        
        root_path = Path(root_dir)
        
        # 1. 압축 파일 처리 (필수)
        print("\n[1단계] 압축 파일 처리")
        zip_files = self.extractor.find_zip_files(str(root_path))
        extracted_folder_names = set()  # 압축 해제된 폴더 이름 추적
        
        # 압축 파일이 없으면 경고하고 종료
        if not zip_files:
            print("⚠️  압축 파일(.zip)을 찾을 수 없습니다.")
            print("최상위 폴더에 압축 파일이 있어야 합니다.")
            return {}
        
        # 압축 파일이 있으면 처리
        if zip_files:
            print(f"압축 파일 {len(zip_files)}개 발견:")
            for idx, zip_file in enumerate(zip_files, 1):
                print(f"  {idx}. {zip_file.name}")
            
            print("\n압축 해제 옵션:")
            print("  - 전체 해제: 'all' 또는 Enter")
            print("  - 선택 해제: 번호 입력 (예: 1,3,5 또는 1-5)")
            print("  - 건너뛰기: 'n' 또는 'skip' (압축 해제를 건너뛰면 프로그램이 종료됩니다)")
            
            extract_choice = input("압축 해제 옵션을 선택하세요: ").strip()
            
            selected_zips = []
            
            if extract_choice.lower() in ['n', 'skip']:
                print("⚠️  압축 해제를 건너뛰었습니다.")
                print("압축 파일을 먼저 해제해야 병합 작업을 진행할 수 있습니다.")
                return {}
            elif extract_choice.lower() in ['', 'all']:
                # Enter 또는 'all' 입력 시 전체 해제
                selected_zips = zip_files
                print("전체 압축 파일 해제를 진행합니다.")
            else:
                # 번호 선택 처리
                selected_indices = []
                parts = extract_choice.split(',')
                
                for part in parts:
                    part = part.strip()
                    # 범위 처리 (예: 1-5)
                    if '-' in part:
                        try:
                            start, end = part.split('-')
                            start_idx = int(start.strip()) - 1
                            end_idx = int(end.strip())
                            selected_indices.extend(range(start_idx, end_idx))
                        except ValueError:
                            print(f"⚠️  잘못된 범위 형식: {part}")
                    else:
                        try:
                            idx = int(part) - 1
                            if 0 <= idx < len(zip_files):
                                selected_indices.append(idx)
                            else:
                                print(f"⚠️  범위를 벗어난 번호: {part}")
                        except ValueError:
                            # 파일명으로 검색
                            matching_files = [f for f in zip_files if part.lower() in f.name.lower()]
                            if matching_files:
                                for f in matching_files:
                                    if f not in selected_zips:
                                        selected_zips.append(f)
                            else:
                                print(f"⚠️  일치하는 파일 없음: {part}")
                
                # 중복 제거 및 정렬
                selected_indices = sorted(set(selected_indices))
                for idx in selected_indices:
                    selected_zips.append(zip_files[idx])
            
            if not selected_zips:
                print("⚠️  선택된 압축 파일이 없습니다.")
                return {}
            
            print(f"\n선택된 압축 파일 {len(selected_zips)}개:")
            for idx, zip_file in enumerate(selected_zips, 1):
                print(f"  {idx}. {zip_file.name}")
            
            remove_after = input("\n압축 해제 후 원본 zip 파일을 삭제하시겠습니까? (y/n, 기본값: n): ").strip().lower() == 'y'
            
            extracted_dirs = []
            for zip_file in selected_zips:
                extracted_dir = self.extractor.extract_zip(zip_file, remove_after_extract=remove_after)
                if extracted_dir:
                    extracted_dirs.append(extracted_dir)
                    # 압축 해제된 폴더 이름 저장 (zip 파일명에서 .zip 제거)
                    extracted_folder_names.add(extracted_dir.name)
                    logger.debug(f"[DEBUG] 압축 해제된 폴더 추가: {extracted_dir.name}")
            
            print(f"✅ {len(extracted_dirs)}개 압축 파일 해제 완료")
            
            if not extracted_folder_names:
                print("⚠️  압축 해제된 폴더가 없습니다.")
                return {}
        
        # 2. 책 폴더 탐색 (압축 해제된 폴더만 표시)
        print("\n[2단계] 책 폴더 탐색")
        
        # 압축 해제된 폴더만 표시 (반드시 있어야 함)
        if not extracted_folder_names:
            print("⚠️  압축 해제된 폴더가 없습니다.")
            print("압축 파일을 먼저 해제해주세요.")
            return {}
        
        # 압축 해제된 폴더만 필터링 (실제로 존재하는 폴더만)
        book_folders = []
        for folder_name in extracted_folder_names:
            folder_path = root_path / folder_name
            if folder_path.exists() and folder_path.is_dir():
                book_folders.append(folder_name)
        
        logger.info(f"[DEBUG] 압축 해제된 폴더만 표시: {len(book_folders)}개")
        print(f"압축 해제된 폴더 {len(book_folders)}개 발견:")
        
        if not book_folders:
            print("❌ 책 폴더를 찾을 수 없습니다.")
            return {}
        
        print(f"책 폴더 {len(book_folders)}개 발견:")
        for idx, folder in enumerate(book_folders, 1):
            print(f"  {idx}. {folder}")
        
        selected = input("병합할 책의 번호(또는 이름)를 입력하세요 (여러 개 선택 시 쉼표로 구분, Enter 시 전체 선택): ").strip()
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
        
        # 3. 각 책별 처리
        configs = {}
        for book_title in book_folders:
            print(f"\n{'='*60}")
            print(f"[책: {book_title}] 처리 시작")
            print(f"{'='*60}")
            
            book_path = root_path / book_title
            
            # 3-1. LC/RC 감지
            print(f"\n[3-1단계] LC/RC 감지")
            logger.info(f"[DEBUG] ===== [{book_title}] LC/RC 감지 시작 =====")
            logger.info(f"[DEBUG] 책 경로: {book_path}")
            detection_result = self.book_type_detector.detect(book_path)
            book_type = detection_result['type']
            
            logger.info(f"[DEBUG] 감지 결과: {detection_result}")
            if book_type:
                print(f"✅ 책 타입 감지: {book_type} (방법: {detection_result['method']})")
                logger.info(f"[DEBUG] ✅ 책 타입 감지 성공: {book_type} (방법: {detection_result['method']})")
            else:
                print("⚠️  책 타입을 자동으로 감지할 수 없습니다.")
                logger.warning(f"[DEBUG] ⚠️  책 타입 자동 감지 실패")
                try:
                    manual_type = input("수동으로 입력하세요 (LC/RC, Enter=건너뛰기): ").strip().upper()
                    if manual_type in ['LC', 'RC']:
                        book_type = manual_type
                        print(f"✅ 책 타입 설정: {book_type}")
                        logger.info(f"[DEBUG] ✅ 수동 입력으로 책 타입 설정: {book_type}")
                    else:
                        print("⚠️  책 타입을 건너뜁니다.")
                        logger.warning(f"[DEBUG] ⚠️  책 타입 없이 진행")
                except (KeyboardInterrupt, EOFError) as e:
                    print("\n⚠️  입력이 중단되었습니다. 책 타입을 건너뜁니다.")
                    logger.warning(f"[DEBUG] 입력 중단: {e}")
                    book_type = None
                except Exception as e:
                    print(f"\n⚠️  입력 오류 발생: {e}. 책 타입을 건너뜁니다.")
                    logger.error(f"[DEBUG] 입력 오류: {e}")
                    book_type = None
            
            # 3-2. 레벨 감지
            print(f"\n[3-2단계] 레벨 감지")
            logger.info(f"[DEBUG] ===== [{book_title}] 레벨 감지 시작 =====")
            detected_level = self.level_config.detect_level(book_path)
            
            logger.info(f"[DEBUG] 레벨 감지 결과: {detected_level}")
            if detected_level:
                print(f"✅ 레벨 감지: {detected_level}")
                level = detected_level
                logger.info(f"[DEBUG] ✅ 레벨 감지 성공: {level}")
            else:
                print("⚠️  레벨을 자동으로 감지할 수 없습니다.")
                logger.warning(f"[DEBUG] ⚠️  레벨 자동 감지 실패")
                print(f"사용 가능한 레벨: {', '.join(self.level_config.get_all_levels())}")
                try:
                    manual_level = input("레벨을 입력하세요 (예: Level 1, Enter=기본 규칙 사용): ").strip()
                    if manual_level and self.level_config.has_level(manual_level):
                        level = manual_level
                        logger.info(f"[DEBUG] ✅ 수동 입력으로 레벨 설정: {level}")
                    else:
                        level = None
                        print("⚠️  기본 규칙을 사용합니다.")
                        logger.warning(f"[DEBUG] ⚠️  레벨 없이 진행 (기본 규칙 사용)")
                except (KeyboardInterrupt, EOFError) as e:
                    print("\n⚠️  입력이 중단되었습니다. 기본 규칙을 사용합니다.")
                    logger.warning(f"[DEBUG] 입력 중단: {e}")
                    level = None
                except Exception as e:
                    print(f"\n⚠️  입력 오류 발생: {e}. 기본 규칙을 사용합니다.")
                    logger.error(f"[DEBUG] 입력 오류: {e}")
                    level = None
            
            # 3-2.5. 내부 압축 파일 처리 (LC/RC 감지 후)
            if book_type:
                print(f"\n[3-2.5단계] 내부 압축 파일 처리")
                logger.info(f"[DEBUG] ===== [{book_title}] 내부 압축 파일 처리 시작 =====")
                logger.info(f"[DEBUG] 책 타입: {book_type}, 탐색 경로: {book_path}")
                
                # 폴더 내부의 zip 파일 찾기
                internal_zips = self.extractor.find_zip_files(str(book_path))
                logger.info(f"[DEBUG] 내부 zip 파일 {len(internal_zips)}개 발견")
                
                if internal_zips:
                    # LC/RC에 따라 필요한 zip 파일만 필터링
                    # LevelConfig의 중앙화된 메서드 사용 (DRY 원칙)
                    target_patterns = self.level_config.get_zip_patterns(book_type, book_path)
                    logger.info(f"[DEBUG] 내부 zip 필터링용 패턴: {len(target_patterns)}개 (책 타입: {book_type})")
                    
                    if target_patterns:
                        filtered_zips = []
                        for zip_file in internal_zips:
                            zip_name_lower = zip_file.name.lower()
                            # _Eng가 포함된 zip 파일 제외
                            if '_eng' in zip_name_lower:
                                logger.debug(f"[DEBUG]   _Eng zip 파일 제외: {zip_file.name}")
                                continue
                            if any(pattern in zip_name_lower for pattern in target_patterns):
                                filtered_zips.append(zip_file)
                                logger.debug(f"[DEBUG]   대상 zip 파일: {zip_file.name}")
                        
                        if filtered_zips:
                            print(f"내부 압축 파일 {len(filtered_zips)}개 발견 (자동 압축 해제):")
                            for idx, zip_file in enumerate(filtered_zips, 1):
                                print(f"  {idx}. {zip_file.name}")
                            
                            # 자동으로 압축 해제
                            for zip_file in filtered_zips:
                                extracted_dir = self.extractor.extract_zip(zip_file, remove_after_extract=False)
                                if extracted_dir:
                                    logger.info(f"[DEBUG]   ✅ 내부 zip 압축 해제 완료: {zip_file.name} -> {extracted_dir}")
                                    print(f"  ✅ {zip_file.name} 압축 해제 완료")
                        else:
                            logger.warning(f"[DEBUG]   ⚠️  대상 zip 파일 없음")
                            logger.info(f"[DEBUG]   모든 zip 파일 목록: {[z.name for z in internal_zips]}")
                            logger.info(f"[DEBUG]   찾는 패턴: {target_patterns}")
                            print(f"⚠️  대상 압축 파일을 찾을 수 없습니다.")
                            print(f"   발견된 zip 파일: {len(internal_zips)}개")
                            for z in internal_zips:
                                print(f"     - {z.name}")
                    else:
                        logger.info(f"[DEBUG]   책 타입이 없어 내부 zip 파일 처리 건너뜀")
            
            # 3-3. 파일 탐색 및 분류
            print(f"\n[3-3단계] 파일 탐색 및 분류")
            logger.info(f"[DEBUG] ===== [{book_title}] 파일 탐색 및 분류 시작 =====")
            logger.info(f"[DEBUG] 탐색 경로: {book_path}")
            discovery_result = self.file_discovery.discover(book_path)
            
            all_pdfs = discovery_result['all']
            main_pdfs = discovery_result['main']
            review_tests = discovery_result['review_tests']
            categories = discovery_result['categories']
            
            logger.info(f"[DEBUG] 탐색 결과:")
            logger.info(f"[DEBUG]   총 PDF 파일: {len(all_pdfs)}개")
            logger.info(f"[DEBUG]   메인 파일: {len(main_pdfs)}개")
            logger.info(f"[DEBUG]   Review Test: {len(review_tests)}개")
            logger.info(f"[DEBUG]   카테고리: {len(categories)}개")
            
            print(f"📄 총 PDF 파일: {len(all_pdfs)}개")
            print(f"📄 메인 파일: {len(main_pdfs)}개")
            print(f"📄 Review Test: {len(review_tests)}개")
            print(f"📁 카테고리: {len(categories)}개")
            
            # 카테고리별 상세 정보 출력
            for cat_name, files in categories.items():
                logger.info(f"[DEBUG]   카테고리 '{cat_name}': {len(files)}개 파일")
            
            # 레벨별 필터링 적용 (LC/RC가 감지된 경우에만)
            logger.info(f"[DEBUG] ===== 레벨별 필터링 적용 여부 확인 =====")
            logger.info(f"[DEBUG] 레벨: {level}, 책 타입: {book_type}")
            
            if level and book_type:
                print(f"\n[레벨별 필터링 적용: {level}, 타입: {book_type}]")
                logger.info(f"[DEBUG] ✅ 필터링 조건 충족 - 필터링 실행")
                logger.info(f"[DEBUG] 필터링 전 파일 수: {len(main_pdfs)}개")
                filtered_pdfs = self.level_config.get_files_for_level(level, main_pdfs, book_type, book_path)
                
                # 필수 파일 누락으로 None이 반환된 경우 - 사용자에게 선택권 제공
                if filtered_pdfs is None:
                    print(f"\n⚠️  [경고] 필수 파일이 누락되었습니다!")
                    logger.warning(f"[DEBUG] 필수 파일 누락 - 사용자 선택 필요")
                    
                    # 필수 검증 없이 필터링만 수행
                    filtered_pdfs = self.level_config.get_files_for_level(level, main_pdfs, book_type, book_path, skip_required_check=True)
                    
                    if filtered_pdfs:
                        # 누락된 필수 파일 패턴 확인
                        book_number = self.level_config.extract_book_number(book_path) if book_path else None
                        required_patterns = []
                        if book_type.upper() == 'RC' and book_number is not None:
                            if book_number <= 60:
                                required_patterns = [r'word\s*list', r'word\s*writing', r'translation\s*sheet', 
                                                   r'unscramble\s*sheet', r'unit\s*test']
                            elif book_number >= 100:
                                required_patterns = [r'word\s*list', r'word\s*test', r'translation\s*sheet', 
                                                   r'unscramble\s*sheet', r'grammar\s*sheet', r'unit\s*test']
                            elif book_number >= 80:
                                required_patterns = [r'word\s*list', r'word\s*test', r'translation\s*sheet', 
                                                   r'unscramble\s*sheet', r'unit\s*test']
                            else:
                                required_patterns = [r'word\s*list', r'word\s*test', r'translation\s*sheet', 
                                                   r'unscramble\s*sheet']
                        
                        found_required = set()
                        for required_pattern in required_patterns:
                            for file_path in filtered_pdfs:
                                if re.search(required_pattern, str(file_path).lower(), re.IGNORECASE):
                                    found_required.add(required_pattern)
                                    break
                        
                        missing_required = set(required_patterns) - found_required
                        
                        if missing_required:
                            print(f"   누락된 파일 패턴: {', '.join(missing_required)}")
                            print(f"   현재 필터링된 파일 목록:")
                            for f in filtered_pdfs:
                                print(f"     - {f.name}")
                            print(f"\n  선택하세요:")
                            print(f"    1. 누락된 파일 없이 계속 진행 (기본값)")
                            print(f"    2. 병합 중단")
                            
                            try:
                                choice = input("  선택 (1/2, 기본값: 1): ").strip()
                            except (KeyboardInterrupt, EOFError) as e:
                                print("\n⚠️  입력이 중단되었습니다. 계속 진행합니다.")
                                logger.warning(f"[DEBUG] 입력 중단: {e}. 계속 진행.")
                                choice = '1'
                            except Exception as e:
                                print(f"\n⚠️  입력 오류 발생: {e}. 계속 진행합니다.")
                                logger.error(f"[DEBUG] 입력 오류: {e}. 계속 진행.")
                                choice = '1'
                            
                            if choice == '2':
                                print(f"\n❌ [중단] 사용자 요청으로 병합을 중단합니다.")
                                logger.info(f"[DEBUG] 사용자 요청으로 병합 중단")
                                configs[book_title] = {
                                    "book_title": book_title,
                                    "total_units": 0,
                                    "categories": {},
                                    "merge_order": [],
                                    "review_tests": [],
                                    "book_type": book_type,
                                    "level": level
                                }
                                continue  # 다음 책으로 넘어감
                            else:
                                print(f"    ✅ 누락된 파일 없이 계속 진행합니다.")
                                logger.info(f"[DEBUG] 사용자 선택: 누락된 파일 없이 계속 진행")
                
                if filtered_pdfs is None or not filtered_pdfs:
                    print(f"\n❌ [오류] 필터링된 파일이 없어 병합을 진행할 수 없습니다.")
                    logger.error(f"[DEBUG] ❌ 필터링된 파일 없음으로 병합 중단")
                    configs[book_title] = {
                        "book_title": book_title,
                        "total_units": 0,
                        "categories": {},
                        "merge_order": [],
                        "review_tests": [],
                        "book_type": book_type,
                        "level": level
                    }
                    continue  # 다음 책으로 넘어감
                
                print(f"필터링 결과: {len(filtered_pdfs)}/{len(main_pdfs)}개 파일")
                logger.info(f"[DEBUG] 필터링 후 파일 수: {len(filtered_pdfs)}개")
                
                # 필터링된 파일로 카테고리 재구성
                logger.info(f"[DEBUG] 필터링된 파일로 카테고리 재구성 중...")
                categories = self.file_discovery.categorize_files(filtered_pdfs)
                logger.info(f"[DEBUG] 재구성 완료: {len(categories)}개 카테고리")
            elif level:
                print(f"\n⚠️  레벨은 감지되었지만 책 타입(LC/RC)이 없어 필터링을 건너뜁니다.")
                logger.warning(f"[DEBUG] ⚠️  레벨만 있고 책 타입 없음 - 필터링 건너뜀")
            elif book_type:
                print(f"\n⚠️  책 타입은 감지되었지만 레벨이 없어 필터링을 건너뜁니다.")
                logger.warning(f"[DEBUG] ⚠️  책 타입만 있고 레벨 없음 - 필터링 건너뜀")
            else:
                logger.warning(f"[DEBUG] ⚠️  레벨과 책 타입 모두 없음 - 필터링 건너뜀")
            
            # 3-3.5. Unit Test 특별 처리 (파일 목록 확인 전에)
            if 'Unit Test' in categories:
                print(f"\n[3-3.5단계] Unit Test 파일 처리")
                logger.info(f"[DEBUG] ===== Unit Test 특별 처리 시작 =====")
                files = categories['Unit Test']
                
                # _Eng 폴더의 파일 제외 (원본 폴더만 사용)
                files = [f for f in files if '_Eng' not in str(f) and '\\Unit Test_Eng\\' not in str(f)]
                logger.info(f"[DEBUG]   _Eng 폴더 제외 후 파일 수: {len(files)}개")
                
                all_files = [f for f in files if 'all' in f.name.lower() and 'answer' not in f.name.lower()]
                unit_files = [f for f in files if 'all' not in f.name.lower() and 'answer' not in f.name.lower()]
                
                logger.info(f"[DEBUG]   Unit Test 파일 분석:")
                logger.info(f"[DEBUG]     전체 파일: {len(files)}개")
                logger.info(f"[DEBUG]     ALL 파일: {len(all_files)}개")
                logger.info(f"[DEBUG]     개별 Unit 파일: {len(unit_files)}개")
                
                if all_files and unit_files:
                    # ALL 파일과 개별 파일이 모두 있는 경우 - 사용자 선택
                    print(f"\n  [Unit Test] ALL 파일과 개별 Unit 파일이 모두 발견되었습니다:")
                    print(f"    - ALL 파일: {len(all_files)}개")
                    for f in all_files:
                        print(f"      • {f.name}")
                    print(f"    - 개별 Unit 파일: {len(unit_files)}개")
                    
                    # 중복 제거 (같은 유닛의 파일들)
                    unique_unit_files = {}
                    for f in unit_files:
                        unit_num = self._extract_unit_number(f)
                        if unit_num > 0:
                            if unit_num not in unique_unit_files:
                                unique_unit_files[unit_num] = []
                            unique_unit_files[unit_num].append(f)
                    
                    print(f"      (Unit 1~{max(unique_unit_files.keys()) if unique_unit_files else 0})")
                    
                    print(f"\n  사용할 파일을 선택하세요:")
                    print(f"    1. ALL 파일 사용 (통합 파일로 처리)")
                    print(f"    2. 개별 Unit 파일 사용 (유닛별 파일로 처리)")
                    
                    try:
                        choice = input("  선택 (1/2, 기본값: 2): ").strip()
                    except (KeyboardInterrupt, EOFError) as e:
                        print("\n⚠️  입력이 중단되었습니다. 개별 Unit 파일을 사용합니다.")
                        logger.warning(f"[DEBUG] 입력 중단: {e}. 개별 Unit 파일 사용.")
                        choice = '2'
                    except Exception as e:
                        print(f"\n⚠️  입력 오류 발생: {e}. 개별 Unit 파일을 사용합니다.")
                        logger.error(f"[DEBUG] 입력 오류: {e}. 개별 Unit 파일 사용.")
                        choice = '2'
                    
                    if choice == '1':
                        # ALL 파일 사용 (통합 파일로 처리)
                        # 중복 제거: 같은 이름의 파일은 하나만 선택
                        unique_all_files = {}
                        for f in all_files:
                            base_name = f.name
                            if base_name not in unique_all_files:
                                unique_all_files[base_name] = f
                        categories['Unit Test'] = list(unique_all_files.values())
                        logger.info(f"[DEBUG]   사용자 선택: ALL 파일 사용 ({len(categories['Unit Test'])}개)")
                        print(f"    ✅ ALL 파일 {len(categories['Unit Test'])}개 선택됨")
                    else:
                        # 개별 Unit 파일 사용 (유닛별 파일로 처리)
                        # 각 유닛별로 첫 번째 파일만 선택 (중복 제거)
                        selected_unit_files = []
                        for unit_num in sorted(unique_unit_files.keys()):
                            selected_unit_files.append(unique_unit_files[unit_num][0])
                        categories['Unit Test'] = selected_unit_files
                        logger.info(f"[DEBUG]   사용자 선택: 개별 Unit 파일 사용 ({len(categories['Unit Test'])}개)")
                        print(f"    ✅ 개별 Unit 파일 {len(categories['Unit Test'])}개 선택됨")
                elif all_files:
                    # ALL 파일만 있는 경우 - 중복 제거
                    unique_all_files = {}
                    for f in all_files:
                        base_name = f.name
                        if base_name not in unique_all_files:
                            unique_all_files[base_name] = f
                    categories['Unit Test'] = list(unique_all_files.values())
                    logger.info(f"[DEBUG]   ALL 파일만 있음: {len(categories['Unit Test'])}개 (중복 제거 후)")
                elif unit_files:
                    # 개별 Unit 파일만 있는 경우 - 중복 제거
                    unique_unit_files = {}
                    for f in unit_files:
                        unit_num = self._extract_unit_number(f)
                        if unit_num > 0:
                            if unit_num not in unique_unit_files:
                                unique_unit_files[unit_num] = f
                    categories['Unit Test'] = [unique_unit_files[k] for k in sorted(unique_unit_files.keys())]
                    logger.info(f"[DEBUG]   개별 Unit 파일만 있음: {len(categories['Unit Test'])}개 (중복 제거 후)")
                else:
                    logger.warning(f"[DEBUG]   ⚠️  Unit Test 파일이 없어 카테고리 제거")
                    del categories['Unit Test']
            
            # 3-3.6. Word Test 파일 처리 (A/B 타입 선택)
            if 'Word Test' in categories:
                print(f"\n[3-3.6단계] Word Test 파일 처리")
                logger.info(f"[DEBUG] ===== Word Test 파일 처리 시작 =====")
                files = categories['Word Test']
                
                # A 타입과 B 타입 파일 분리
                # 패턴: "Test A", "Test_A", "Test A.pdf", "Word Test A" 등
                def is_test_a(file_path: Path) -> bool:
                    name = file_path.stem.lower()  # 확장자 제외, 소문자 변환
                    # "test a" 또는 "test_a" 패턴 확인
                    return bool(re.search(r'test\s*[_\s]a\b', name, re.IGNORECASE)) or \
                           bool(re.search(r'[_\s]a\.pdf$', file_path.name, re.IGNORECASE))
                
                def is_test_b(file_path: Path) -> bool:
                    name = file_path.stem.lower()  # 확장자 제외, 소문자 변환
                    # "test b" 또는 "test_b" 패턴 확인
                    return bool(re.search(r'test\s*[_\s]b\b', name, re.IGNORECASE)) or \
                           bool(re.search(r'[_\s]b\.pdf$', file_path.name, re.IGNORECASE))
                
                files_a = [f for f in files if is_test_a(f)]
                files_b = [f for f in files if is_test_b(f)]
                
                logger.info(f"[DEBUG]   Word Test 파일 분석:")
                logger.info(f"[DEBUG]     전체 파일: {len(files)}개")
                logger.info(f"[DEBUG]     A 타입: {len(files_a)}개")
                logger.info(f"[DEBUG]     B 타입: {len(files_b)}개")
                
                if files_a and files_b:
                    # A와 B가 둘 다 존재하는 경우 - 사용자 선택
                    print(f"\n  [Word Test] A 타입과 B 타입이 모두 발견되었습니다:")
                    print(f"    - A 타입: {len(files_a)}개")
                    for f in files_a:
                        print(f"      • {f.name}")
                    print(f"    - B 타입: {len(files_b)}개")
                    for f in files_b:
                        print(f"      • {f.name}")
                    
                    print(f"\n  사용할 Word Test 타입을 선택하세요:")
                    print(f"    1. Test A만 사용")
                    print(f"    2. Test B만 사용")
                    print(f"    3. 둘 다 사용 (기본값)")
                    
                    try:
                        choice = input("  선택 (1/2/3, 기본값: 3): ").strip()
                    except (KeyboardInterrupt, EOFError) as e:
                        print("\n⚠️  입력이 중단되었습니다. 둘 다 사용합니다.")
                        logger.warning(f"[DEBUG] 입력 중단: {e}. 둘 다 사용.")
                        choice = '3'
                    except Exception as e:
                        print(f"\n⚠️  입력 오류 발생: {e}. 둘 다 사용합니다.")
                        logger.error(f"[DEBUG] 입력 오류: {e}. 둘 다 사용.")
                        choice = '3'
                    
                    if choice == '1':
                        # Test A만 사용
                        categories['Word Test'] = files_a
                        logger.info(f"[DEBUG]   사용자 선택: Test A만 사용 ({len(files_a)}개)")
                        print(f"    ✅ Test A {len(files_a)}개 선택됨")
                    elif choice == '2':
                        # Test B만 사용
                        categories['Word Test'] = files_b
                        logger.info(f"[DEBUG]   사용자 선택: Test B만 사용 ({len(files_b)}개)")
                        print(f"    ✅ Test B {len(files_b)}개 선택됨")
                    else:
                        # 둘 다 사용 (기본값)
                        categories['Word Test'] = files  # 원본 그대로
                        logger.info(f"[DEBUG]   사용자 선택: 둘 다 사용 ({len(files)}개)")
                        print(f"    ✅ 둘 다 사용 ({len(files)}개)")
                else:
                    # A, B가 섞여있지 않으면 그냥 통과
                    logger.info(f"[DEBUG]   A/B 타입이 섞여있지 않음 - 그대로 사용 ({len(files)}개)")
            
            # 3-4. 파일 목록 확인 및 수정
            print(f"\n[3-4단계] 파일 목록 확인")
            print(f"\n카테고리별 파일 목록:")
            for cat_name, files in categories.items():
                print(f"\n  [{cat_name}] ({len(files)}개)")
                for idx, file_path in enumerate(files, 1):
                    print(f"    {idx}. {file_path.relative_to(book_path)}")
            
            # 사용자 확인
            yn = input("\n이대로 병합할까요? (y/n, 기본값: y): ").strip().lower()
            if yn == 'n':
                # 파일 제외/포함 로직 (기존과 유사)
                print("파일 제외/포함 기능은 추후 구현 예정입니다.")
            
            # 3-5. 유닛 정보 추출 (LC/RC에 따라 처리)
            print(f"\n[3-5단계] 유닛 정보 추출")
            logger.info(f"[DEBUG] ===== 유닛 정보 추출 시작 =====")
            unit_page_lengths_dict = {}
            
            # LC/RC의 경우 각 파일 타입이 유닛별 파일로 구성됨
            # LC: Word List, Word Test (각각 유닛별 파일)
            # RC: Word List, Word Test, Translation Sheet, Unscramble Sheet, Unit Test (각각 유닛별 파일)
            unit_based_categories = ['Word List', 'Word Test', 'Translation Sheet', 'Unscramble Sheet', 'Unit Test']
            logger.debug(f"[DEBUG] 유닛별 파일 카테고리: {unit_based_categories}")
            
            for cat_name, files in categories.items():
                logger.info(f"[DEBUG] 카테고리 처리: {cat_name} ({len(files)}개 파일)")
                if not files:
                    logger.warning(f"[DEBUG]   ⚠️  파일이 없어 건너뜀")
                    continue
                
                # 유닛별 파일인지 확인 (파일이 여러 개이고, 파일명에 유닛 번호가 있는 경우)
                # (Unit Test는 이미 [3-3.5단계]에서 처리되었으므로 여기서는 건너뜀)
                is_unit_based = False
                has_letter_suffix = False  # 함수 스코프에서 초기화
                if len(files) > 1:
                    # 파일명에 유닛 번호가 있는지 확인
                    unit_numbers = [self._extract_unit_number(f) for f in files]
                    has_unit_numbers = any(unit_num > 0 for unit_num in unit_numbers)
                    
                    # 파일명에 "A", "B" 같은 알파벳 접미사가 있는지 확인 (예: Word List A, Word List B)
                    # 파일명 끝에 단일 알파벳이 있는지 확인
                    # 패턴: 공백/언더스코어 + 단일 알파벳 + 끝 (또는 확장자)
                    def has_letter_suffix_pattern(file_path: Path) -> bool:
                        name = file_path.stem  # 확장자 제외
                        # 파일명 끝에 " A", " B", "_A", "_B" 같은 패턴이 있는지 확인
                        # 예: "Word Test A" -> " A" 매칭, "Word Test" -> 매칭 안 됨
                        return bool(re.search(r'[_\s]([A-Z])$', name, re.IGNORECASE))
                    
                    has_letter_suffix = any(has_letter_suffix_pattern(f) for f in files)
                    
                    logger.debug(f"[DEBUG]   파일 수: {len(files)}, 유닛 번호 존재: {has_unit_numbers}, 유닛 번호: {unit_numbers}")
                    logger.debug(f"[DEBUG]   알파벳 접미사 존재: {has_letter_suffix}")
                    logger.debug(f"[DEBUG]   카테고리명이 유닛별 카테고리 목록에 있는지: {cat_name in unit_based_categories}")
                    
                    # 유닛 번호가 있고, 알파벳 접미사가 없으면 유닛별 파일로 판단
                    # 알파벳 접미사가 있으면 사용자 선택 후 통합 파일로 처리 (각 파일이 여러 유닛 포함)
                    if has_letter_suffix:
                        # 알파벳 접미사(A, B 등)가 있으면 사용자에게 선택 질문
                        # 선택 질문은 아래 통합 파일 처리 부분에서 진행
                        is_unit_based = False
                        logger.debug(f"[DEBUG]   알파벳 접미사 감지됨 (A, B 등) - 사용자 선택 필요")
                    elif has_unit_numbers:
                        # 유닛 번호가 있으면 유닛별 파일로 판단
                        is_unit_based = True
                        logger.debug(f"[DEBUG]   ✅ 유닛별 파일로 판단됨 (유닛 번호 있음)")
                    elif cat_name in unit_based_categories:
                        # 카테고리명이 유닛별 카테고리이면 유닛별 파일로 판단
                        is_unit_based = True
                        logger.debug(f"[DEBUG]   ✅ 유닛별 파일로 판단됨 (카테고리명 기준)")
                    else:
                        # 그 외는 통합 파일로 판단
                        is_unit_based = False
                        logger.debug(f"[DEBUG]   ❌ 통합 파일로 판단됨")
                else:
                    logger.debug(f"[DEBUG]   파일이 1개뿐이므로 통합 파일로 판단")
                
                if is_unit_based:
                    # 유닛별 파일인 경우
                    print(f"  [{cat_name}] 유닛별 파일로 처리 ({len(files)}개 파일)")
                    logger.info(f"[DEBUG]   유닛별 파일 처리 시작")
                    unit_page_lengths = []
                    pdf_paths = []
                    
                    # 유닛 번호 순서대로 정렬
                    sorted_files = sorted(files, key=lambda p: self._extract_unit_number(p))
                    logger.debug(f"[DEBUG]   정렬된 파일 순서:")
                    for f in sorted_files:
                        logger.debug(f"[DEBUG]     Unit {self._extract_unit_number(f)}: {f.name}")
                    
                    for file_path in sorted_files:
                        unit_num = self._extract_unit_number(file_path)
                        logger.debug(f"[DEBUG]   파일 처리: Unit {unit_num} - {file_path.name}")
                        try:
                            reader = PdfReader(str(file_path))
                            page_count = len(reader.pages)
                            unit_page_lengths.append(page_count)
                            pdf_paths.append(str(file_path))
                            logger.info(f"[DEBUG]     ✅ Unit {unit_num}: {page_count}페이지")
                            print(f"    Unit {unit_num}: {page_count}페이지")
                        except Exception as e:
                            logger.error(f"[DEBUG]     ❌ PDF 읽기 실패: {e}")
                            logger.warning(f"PDF 읽기 실패 ({file_path}): {e}")
                            unit_page_lengths.append(0)
                            pdf_paths.append(str(file_path))
                    
                    categories[cat_name] = {
                        "pdf_paths": pdf_paths,
                        "unit_page_lengths": unit_page_lengths
                    }
                    unit_page_lengths_dict[cat_name] = unit_page_lengths
                    logger.info(f"[DEBUG]   ✅ 완료: {len(unit_page_lengths)}개 유닛, 총 {sum(unit_page_lengths)}페이지")
                else:
                    # 통합 파일인 경우 (한 파일에 여러 유닛 포함)
                    # has_letter_suffix가 True인 경우도 여기서 처리 (A, B 등)
                    if has_letter_suffix and len(files) > 1:
                        # 알파벳 접미사가 있는 여러 파일 (예: Word Test A, Word Test B)
                        # 사용자에게 선택권 제공
                        print(f"\n  [{cat_name}] 여러 파일 발견 ({len(files)}개):")
                        sorted_files = sorted(files, key=lambda p: p.name)
                        for idx, file_path in enumerate(sorted_files, 1):
                            # 알파벳 접미사 추출 (A, B 등)
                            suffix_match = re.search(r'[_\s]([A-Z])$', file_path.stem, re.IGNORECASE)
                            suffix = suffix_match.group(1) if suffix_match else ""
                            display_name = file_path.name
                            if suffix:
                                display_name = f"{file_path.name} (버전 {suffix})"
                            print(f"    {idx}. {display_name}")
                        print(f"    {len(files) + 1}. 모두 사용 (전체 병합)")
                        
                        try:
                            choice_input = input(f"\n  사용할 파일을 선택하세요 (번호 입력, 기본값: {len(files) + 1} 모두 사용): ").strip()
                        except (KeyboardInterrupt, EOFError) as e:
                            print("\n⚠️  입력이 중단되었습니다. 모든 파일을 사용합니다.")
                            logger.warning(f"[DEBUG] 입력 중단: {e}. 모든 파일 사용.")
                            choice_input = str(len(files) + 1)
                        except Exception as e:
                            print(f"\n⚠️  입력 오류 발생: {e}. 모든 파일을 사용합니다.")
                            logger.error(f"[DEBUG] 입력 오류: {e}. 모든 파일 사용.")
                            choice_input = str(len(files) + 1)
                        
                        selected_files = []
                        if not choice_input:
                            # 기본값: 모두 사용
                            selected_files = sorted_files
                            logger.info(f"[DEBUG] 사용자 선택: 모두 사용 ({len(selected_files)}개 파일)")
                        else:
                            try:
                                choice = int(choice_input)
                                if 1 <= choice <= len(files):
                                    selected_files = [sorted_files[choice - 1]]
                                    logger.info(f"[DEBUG] 사용자 선택: {sorted_files[choice - 1].name}")
                                elif choice == len(files) + 1:
                                    selected_files = sorted_files
                                    logger.info(f"[DEBUG] 사용자 선택: 모두 사용 ({len(selected_files)}개 파일)")
                                else:
                                    print(f"    ⚠️  잘못된 번호입니다. 모든 파일을 사용합니다.")
                                    logger.warning(f"[DEBUG] 잘못된 번호: {choice}. 모든 파일 사용.")
                                    selected_files = sorted_files
                            except ValueError:
                                print(f"    ⚠️  잘못된 입력입니다. 모든 파일을 사용합니다.")
                                logger.warning(f"[DEBUG] 잘못된 입력: {choice_input}. 모든 파일 사용.")
                                selected_files = sorted_files
                        
                        if not selected_files:
                            print(f"    ⚠️  [{cat_name}] 건너뜀 (선택된 파일 없음)")
                            logger.info(f"[DEBUG]   사용자 요청으로 [{cat_name}] 건너뜀")
                            continue
                        
                        # 선택된 파일들을 통합 파일로 처리
                        # 여러 파일이 선택된 경우, 각 파일을 통합 파일로 처리하고 합침
                        if len(selected_files) == 1:
                            # 파일이 1개만 선택된 경우
                            file_path = selected_files[0]
                            logger.debug(f"[DEBUG]   단일 파일 처리: {file_path.name}")
                            unit_page_lengths = self._extract_unit_page_lengths(file_path)
                            categories[cat_name] = {
                                "pdf_path": str(file_path),
                                "unit_page_lengths": unit_page_lengths
                            }
                            unit_page_lengths_dict[cat_name] = unit_page_lengths
                            logger.info(f"[DEBUG]     ✅ 유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                            print(f"    ✅ 유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                        else:
                            # 여러 파일이 선택된 경우 - 각 파일을 통합 파일로 처리하고 합침
                            logger.info(f"[DEBUG]   여러 파일 통합 처리 시작: {len(selected_files)}개 파일")
                            all_unit_page_lengths = []
                            file_unit_info = []
                            current_unit_index = 0
                            
                            for file_path in sorted(selected_files, key=lambda p: p.name):
                                logger.debug(f"[DEBUG]     파일 처리: {file_path.name}")
                                unit_page_lengths = self._extract_unit_page_lengths(file_path)
                                unit_count = len(unit_page_lengths)
                                
                                file_unit_info.append({
                                    "pdf_path": str(file_path),
                                    "start_unit_index": current_unit_index,
                                    "unit_count": unit_count,
                                    "unit_page_lengths": unit_page_lengths
                                })
                                
                                all_unit_page_lengths.extend(unit_page_lengths)
                                current_unit_index += unit_count
                                logger.info(f"[DEBUG]       ✅ {file_path.name}: {unit_count}개 유닛, {sum(unit_page_lengths)}페이지")
                            
                            categories[cat_name] = {
                                "pdf_path": str(selected_files[0]),  # 첫 번째 파일 경로 (참조용)
                                "pdf_paths": [str(f) for f in selected_files],  # 모든 파일 경로
                                "unit_page_lengths": all_unit_page_lengths,
                                "file_unit_info": file_unit_info,
                                "is_multi_file_combined": True
                            }
                            unit_page_lengths_dict[cat_name] = all_unit_page_lengths
                            logger.info(f"[DEBUG]     ✅ 통합 완료: 총 {len(all_unit_page_lengths)}개 유닛, {sum(all_unit_page_lengths)}페이지")
                            print(f"    ✅ 통합 완료: 총 {len(all_unit_page_lengths)}개 유닛, {sum(all_unit_page_lengths)}페이지")
                    
                    elif len(files) == 1:
                        # 파일이 1개인 경우 - 사용자 확인
                        file_path = files[0]
                        print(f"    파일: {file_path.name}")
                        print(f"    이 파일을 통합 파일로 처리하시겠습니까? (한 파일에 여러 유닛이 포함된 경우)")
                        
                        try:
                            confirm = input("  처리할까요? (y/n, 기본값: y): ").strip().lower()
                        except (KeyboardInterrupt, EOFError) as e:
                            print("\n⚠️  입력이 중단되었습니다. 통합 파일로 처리합니다.")
                            logger.warning(f"[DEBUG] 입력 중단: {e}. 통합 파일로 처리.")
                            confirm = 'y'
                        except Exception as e:
                            print(f"\n⚠️  입력 오류 발생: {e}. 통합 파일로 처리합니다.")
                            logger.error(f"[DEBUG] 입력 오류: {e}. 통합 파일로 처리.")
                            confirm = 'y'
                        
                        if confirm == 'n':
                            print(f"    ⚠️  [{cat_name}] 건너뜀")
                            logger.info(f"[DEBUG]   사용자 요청으로 [{cat_name}] 건너뜀")
                            continue  # 이 카테고리 건너뛰기
                        
                        logger.debug(f"[DEBUG]   파일 처리: {file_path.name}")
                        unit_page_lengths = self._extract_unit_page_lengths(file_path)
                        categories[cat_name] = {
                            "pdf_path": str(file_path),
                            "unit_page_lengths": unit_page_lengths
                        }
                        unit_page_lengths_dict[cat_name] = unit_page_lengths
                        logger.info(f"[DEBUG]     ✅ 유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                        print(f"    ✅ 유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                    else:
                        # 파일이 여러 개인 경우 (예: Word List A, Word List B)
                        # 사용자에게 선택권 제공
                        print(f"\n  [{cat_name}] 여러 파일 발견 ({len(files)}개):")
                        sorted_files = sorted(files, key=lambda p: p.name)
                        for idx, file_path in enumerate(sorted_files, 1):
                            print(f"    {idx}. {file_path.name}")
                        print(f"    {len(files) + 1}. 모두 사용 (전체 병합)")
                        
                        try:
                            choice_input = input(f"\n  사용할 파일을 선택하세요 (번호 입력, 기본값: {len(files) + 1} 모두 사용): ").strip()
                        except (KeyboardInterrupt, EOFError) as e:
                            print("\n⚠️  입력이 중단되었습니다. 모든 파일을 사용합니다.")
                            logger.warning(f"[DEBUG] 입력 중단: {e}. 모든 파일 사용.")
                            choice_input = str(len(files) + 1)
                        except Exception as e:
                            print(f"\n⚠️  입력 오류 발생: {e}. 모든 파일을 사용합니다.")
                            logger.error(f"[DEBUG] 입력 오류: {e}. 모든 파일 사용.")
                            choice_input = str(len(files) + 1)
                        
                        selected_files = []
                        if not choice_input:
                            # 기본값: 모두 사용
                            selected_files = sorted_files
                            logger.info(f"[DEBUG] 사용자 선택: 모두 사용 ({len(selected_files)}개 파일)")
                        else:
                            try:
                                choice = int(choice_input)
                                if 1 <= choice <= len(files):
                                    selected_files = [sorted_files[choice - 1]]
                                    logger.info(f"[DEBUG] 사용자 선택: {selected_files[0].name}")
                                elif choice == len(files) + 1:
                                    selected_files = sorted_files
                                    logger.info(f"[DEBUG] 사용자 선택: 모두 사용 ({len(selected_files)}개 파일)")
                                else:
                                    print(f"⚠️  잘못된 번호입니다. 모든 파일을 사용합니다.")
                                    logger.warning(f"[DEBUG] 잘못된 번호 입력: {choice}. 모든 파일 사용.")
                                    selected_files = sorted_files
                            except ValueError:
                                # 파일명으로 검색
                                matching_files = [f for f in sorted_files if choice_input.lower() in f.name.lower()]
                                if matching_files:
                                    selected_files = matching_files
                                    logger.info(f"[DEBUG] 사용자 선택 (파일명 검색): {[f.name for f in selected_files]}")
                                else:
                                    print(f"⚠️  일치하는 파일이 없습니다. 모든 파일을 사용합니다.")
                                    logger.warning(f"[DEBUG] 일치하는 파일 없음: {choice_input}. 모든 파일 사용.")
                                    selected_files = sorted_files
                        
                        if len(selected_files) == 1:
                            # 파일이 1개 선택된 경우
                            file_path = selected_files[0]
                            logger.debug(f"[DEBUG]   선택된 파일 처리: {file_path.name}")
                            unit_page_lengths = self._extract_unit_page_lengths(file_path)
                            categories[cat_name] = {
                                "pdf_path": str(file_path),
                                "unit_page_lengths": unit_page_lengths
                            }
                            unit_page_lengths_dict[cat_name] = unit_page_lengths
                            logger.info(f"[DEBUG]     ✅ 유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                            print(f"    ✅ 선택된 파일: {file_path.name}")
                            print(f"    유닛 수: {len(unit_page_lengths)}, 페이지: {unit_page_lengths}")
                        else:
                            # 여러 파일 선택된 경우 (모두 사용)
                            logger.info(f"[DEBUG]   여러 통합 파일 처리: 각 파일에서 유닛 추출 후 합침")
                            all_unit_page_lengths = []
                            file_unit_info = []  # 각 파일의 정보: (파일경로, 시작유닛인덱스, 유닛수)
                            
                            logger.debug(f"[DEBUG]   정렬된 파일 순서:")
                            for f in selected_files:
                                logger.debug(f"[DEBUG]     {f.name}")
                            
                            start_unit_index = 0
                            for file_path in selected_files:
                                logger.debug(f"[DEBUG]   파일 처리: {file_path.name}")
                                unit_page_lengths = self._extract_unit_page_lengths(file_path)
                                if unit_page_lengths:
                                    file_unit_info.append({
                                        "pdf_path": str(file_path),
                                        "start_unit_index": start_unit_index,
                                        "unit_count": len(unit_page_lengths),
                                        "unit_page_lengths": unit_page_lengths
                                    })
                                    all_unit_page_lengths.extend(unit_page_lengths)
                                    start_unit_index += len(unit_page_lengths)
                                    logger.info(f"[DEBUG]     ✅ {file_path.name}: {len(unit_page_lengths)}개 유닛 추가 (시작 인덱스: {file_unit_info[-1]['start_unit_index']}), 페이지: {unit_page_lengths}")
                                    print(f"    {file_path.name}: {len(unit_page_lengths)}개 유닛, 페이지: {unit_page_lengths}")
                                else:
                                    logger.warning(f"[DEBUG]     ⚠️  {file_path.name}: 유닛 추출 실패")
                            
                            # 여러 파일의 유닛을 합쳤으므로, 각 유닛이 어느 파일의 어느 위치에 있는지 추적
                            categories[cat_name] = {
                                "unit_page_lengths": all_unit_page_lengths,
                                "file_unit_info": file_unit_info,  # 각 파일의 유닛 정보
                                "is_multi_file_combined": True  # 여러 파일을 합쳤다는 플래그
                            }
                            unit_page_lengths_dict[cat_name] = all_unit_page_lengths
                            logger.info(f"[DEBUG]   ✅ 완료: 총 {len(all_unit_page_lengths)}개 유닛 (여러 파일 합침), 총 {sum(all_unit_page_lengths)}페이지")
                            print(f"    총 유닛 수: {len(all_unit_page_lengths)}, 총 페이지: {sum(all_unit_page_lengths)}")
            
            # 유닛 수 확인
            logger.info(f"[DEBUG] ===== 유닛 수 확인 =====")
            unit_counts = [len(upl) for upl in unit_page_lengths_dict.values()]
            logger.info(f"[DEBUG] 카테고리별 유닛 수: {unit_counts}")
            logger.info(f"[DEBUG] 카테고리별 상세 정보:")
            for cat_name, upl in unit_page_lengths_dict.items():
                logger.info(f"[DEBUG]   {cat_name}: {len(upl)}개 유닛, 페이지: {upl}")
            
            if len(set(unit_counts)) != 1:
                print(f"⚠️  경고: 카테고리별 유닛 수가 일치하지 않습니다: {unit_counts}")
                logger.warning(f"[DEBUG] ⚠️  카테고리별 유닛 수 불일치: {unit_counts}")
                max_units = max(unit_counts) if unit_counts else 0
                print(f"최대 유닛 수({max_units})를 사용합니다.")
                logger.info(f"[DEBUG] 최대 유닛 수 사용: {max_units}")
                total_units = max_units
            else:
                total_units = unit_counts[0] if unit_counts else 0
                logger.info(f"[DEBUG] ✅ 모든 카테고리 유닛 수 일치: {total_units}")
            
            logger.info(f"[DEBUG] 최종 총 유닛 수: {total_units}")
            
            # 3-6. 병합 순서 설정
            print(f"\n[3-6단계] 병합 순서 설정")
            category_list = list(categories.keys())
            print("카테고리 목록:")
            for idx, cat in enumerate(category_list, 1):
                print(f"  {idx}. {cat}")
            
            order_input = input("병합 순서를 번호로 입력하세요 (예: 1,2,3 또는 Enter=자동순서): ").strip()
            if order_input:
                try:
                    order_numbers = [int(x.strip()) for x in order_input.split(',') if x.strip()]
                    merge_order = []
                    for num in order_numbers:
                        if 1 <= num <= len(category_list):
                            merge_order.append(category_list[num-1])
                    if not merge_order:
                        merge_order = category_list
                except ValueError:
                    merge_order = category_list
            else:
                merge_order = category_list
            
            print(f"병합 순서: {' → '.join(merge_order)}")
            
            # 3-7. Review Test 처리
            review_tests_config = []
            for review_path in review_tests:
                # 파일명에서 구간 추출
                m = re.search(r'Units?[\s_]*(\d{1,2})[\s\-~]+(\d{1,2})', review_path.name, re.IGNORECASE)
                if m:
                    start_unit = int(m.group(1))
                    end_unit = int(m.group(2))
                else:
                    start_unit = end_unit = total_units  # 기본값: 마지막 유닛
                
                try:
                    reader = PdfReader(str(review_path))
                    total_pages = len(reader.pages)
                    review_tests_config.append({
                        "cat_name": review_path.stem,
                        "pdf_path": str(review_path),
                        "unit_page_lengths": [total_pages],
                        "start_unit": start_unit,
                        "end_unit": end_unit
                    })
                except Exception as e:
                    logger.warning(f"Review Test 파일 읽기 실패 ({review_path}): {e}")
            
            # 설정 저장
            configs[book_title] = {
                "book_title": book_title,
                "book_type": book_type,
                "level": level,
                "total_units": total_units,
                "categories": categories,
                "merge_order": merge_order,
                "review_tests": review_tests_config
            }
            
            print(f"\n✅ [{book_title}] 설정 완료")
        
        return configs
    
    def _extract_unit_number(self, path: Path) -> int:
        """파일 경로에서 유닛 번호 추출"""
        match = re.search(r"unit[ _-]?(\d{1,2})", str(path), re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_unit_page_lengths(self, pdf_path: Path) -> List[int]:
        """PDF에서 유닛별 페이지 길이 추출 (기존 로직 재사용)"""
        # 기존 config.py의 extract_unit_page_lengths 로직 재사용
        unit_pattern = re.compile(r'u\s*n\s*i\s*t\s*[\.:∙-]?\s*(\d{1,2})', re.IGNORECASE)
        
        def normalize_text(text):
            """PDF 텍스트 정규화"""
            text = text.replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            text = re.sub(r'U\s+n\s*i\s+t', 'Unit', text, flags=re.IGNORECASE)
            text = re.sub(r'U\s+nit', 'Unit', text, flags=re.IGNORECASE)
            text = re.sub(r'Un\s+it', 'Unit', text, flags=re.IGNORECASE)
            text = re.sub(r'Uni\s+t', 'Unit', text, flags=re.IGNORECASE)
            return text
        
        def is_toc_page(text):
            """목차 페이지인지 확인"""
            toc_keywords = ['목차', 'contents', 'table of contents', 'index']
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in toc_keywords):
                return True
            unit_matches = re.findall(r'unit\s*\d{1,2}', text_lower)
            if len(set(unit_matches)) >= 3:
                return True
            return False
        
        try:
            reader = PdfReader(str(pdf_path))
            
            # 목차 페이지 감지
            first_page_text = reader.pages[0].extract_text() or ""
            is_toc = is_toc_page(first_page_text)
            
            if is_toc:
                print(f"[안내] 카테고리: {pdf_path.name}")
                print(f"[안내] 첫 번째 페이지가 목차로 감지되었습니다.")
                confirm = input("목차 페이지를 제외하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                start_page = 1 if confirm == 'y' else 0
            else:
                start_page = 0
            
            unit_indices = []
            unit_numbers = []
            last_unit_num = None
            first_unit_found = False
            
            for i, page in enumerate(reader.pages[start_page:], start_page):
                raw_text = page.extract_text() or ""
                
                if not raw_text.strip():
                    continue
                
                text = normalize_text(raw_text)
                found = unit_pattern.search(text)
                
                if found:
                    unit_num = int(found.group(1))
                    if not first_unit_found and i == start_page + 1 and len(unit_indices) == 0:
                        unit_indices.append(start_page)
                        unit_numbers.append(unit_num)
                        last_unit_num = unit_num
                        first_unit_found = True
                    elif unit_num != last_unit_num:
                        unit_indices.append(i)
                        unit_numbers.append(unit_num)
                        last_unit_num = unit_num
            
            if not unit_indices:
                print(f"[안내] {pdf_path.name}에서 유닛이 감지되지 않았습니다.")
                manual_input = input("유닛 수를 직접 입력하시겠습니까? (y/n, 기본값: n): ").strip().lower()
                if manual_input == 'y':
                    try:
                        unit_count = int(input("유닛 수를 입력하세요: "))
                        total_pages = len(reader.pages) - start_page
                        pages_per_unit = total_pages // unit_count
                        unit_page_lengths = [pages_per_unit] * unit_count
                        remainder = total_pages % unit_count
                        if remainder > 0:
                            unit_page_lengths[-1] += remainder
                        return unit_page_lengths
                    except ValueError:
                        print("올바른 숫자를 입력해주세요.")
                return [len(reader.pages) - start_page]
            
            unit_indices.append(len(reader.pages))
            unit_page_lengths = [unit_indices[i+1] - unit_indices[i] for i in range(len(unit_indices)-1)]
            return unit_page_lengths
            
        except Exception as e:
            logger.error(f"PDF 읽기 실패 ({pdf_path}): {e}")
            return []
