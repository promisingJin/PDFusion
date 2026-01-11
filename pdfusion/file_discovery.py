"""
자동 파일 탐색 모듈
prac book 폴더 구조에 의존하지 않고 자동으로 PDF 파일 탐색 및 분류
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
import re

logger = logging.getLogger(__name__)


class FileDiscovery:
    """자동 파일 탐색 클래스"""
    
    def __init__(self):
        # 제외할 파일 패턴
        self.exclude_patterns = [
            r'answer',
            r'답지',
            r'정답',
        ]
        
        # Review Test 패턴
        self.review_test_patterns = [
            r'review\s*test',
            r'리뷰\s*테스트',
        ]
    
    def find_all_pdfs(self, directory: Path, recursive: bool = True) -> List[Path]:
        """
        디렉토리에서 모든 PDF 파일 찾기
        
        Args:
            directory: 탐색할 디렉토리 경로
            recursive: 재귀 탐색 여부
            
        Returns:
            찾은 PDF 파일 경로 리스트
        """
        if recursive:
            pdf_files = list(directory.rglob("*.pdf"))
        else:
            pdf_files = list(directory.glob("*.pdf"))
        
        logger.info(f"디렉토리 '{directory}'에서 {len(pdf_files)}개의 PDF 파일 발견")
        return pdf_files
    
    def filter_excluded_files(self, pdf_files: List[Path]) -> List[Path]:
        """
        제외 패턴에 해당하는 파일 필터링
        
        Args:
            pdf_files: PDF 파일 경로 리스트
            
        Returns:
            필터링된 PDF 파일 경로 리스트
        """
        filtered = []
        
        for pdf_file in pdf_files:
            file_str = str(pdf_file).lower()
            
            excluded = False
            for pattern in self.exclude_patterns:
                if re.search(pattern, file_str, re.IGNORECASE):
                    logger.debug(f"제외됨: {pdf_file}")
                    excluded = True
                    break
            
            if not excluded:
                filtered.append(pdf_file)
        
        logger.info(f"제외 필터링: {len(filtered)}/{len(pdf_files)}개 파일 남음")
        return filtered
    
    def find_review_tests(self, pdf_files: List[Path]) -> List[Path]:
        """
        Review Test 파일 찾기
        
        Args:
            pdf_files: PDF 파일 경로 리스트
            
        Returns:
            Review Test 파일 경로 리스트
        """
        review_tests = []
        
        for pdf_file in pdf_files:
            file_str = str(pdf_file).lower()
            
            for pattern in self.review_test_patterns:
                if re.search(pattern, file_str, re.IGNORECASE):
                    review_tests.append(pdf_file)
                    logger.debug(f"Review Test 발견: {pdf_file}")
                    break
        
        logger.info(f"Review Test 파일 {len(review_tests)}개 발견")
        return review_tests
    
    def categorize_files(self, pdf_files: List[Path]) -> Dict[str, List[Path]]:
        """
        파일을 카테고리별로 분류
        파일 타입(Word List, Word Test 등)별로 그룹화하고, 각 타입 내에서 유닛별로 정렬
        
        Args:
            pdf_files: PDF 파일 경로 리스트
            
        Returns:
            카테고리별 파일 딕셔너리 (각 카테고리는 유닛 순서대로 정렬된 파일 리스트)
        """
        categories = {}
        
        # 파일 타입 패턴 정의
        file_type_patterns = {
            'Word List': [r'word\s*list', r'wordlist'],
            'Word Test': [r'word\s*test', r'wordtest'],
            'Translation Sheet': [r'translation\s*sheet', r'translationsheet'],
            'Unscramble Sheet': [r'unscramble\s*sheet', r'unscramblesheet'],
            'Unit Test': [r'unit\s*test', r'unittest'],
        }
        
        # 유닛 번호 추출 함수
        def extract_unit_number(path: Path) -> int:
            """파일 경로에서 유닛 번호 추출"""
            # 다양한 패턴 시도
            patterns = [
                r'unit[ _-]?(\d{1,2})',
                r'u[ _-]?(\d{1,2})',
                r'_u(\d{1,2})',
            ]
            for pattern in patterns:
                match = re.search(pattern, str(path), re.IGNORECASE)
                if match:
                    return int(match.group(1))
            return 0  # 유닛 번호를 찾을 수 없으면 0
        
        # 파일 타입 추출 함수
        def extract_file_type(path: Path) -> Optional[str]:
            """파일 경로에서 파일 타입 추출"""
            path_str = str(path).lower()
            # Unit Test는 우선 처리 (다른 패턴과 겹칠 수 있음)
            if re.search(r'unit\s*test', path_str, re.IGNORECASE):
                return 'Unit Test'
            # 나머지 타입 확인
            for file_type, patterns in file_type_patterns.items():
                if file_type == 'Unit Test':  # 이미 처리했으므로 건너뛰기
                    continue
                for pattern in patterns:
                    if re.search(pattern, path_str, re.IGNORECASE):
                        return file_type
            return None
        
        logger.debug(f"[DEBUG] ===== 파일 분류 시작 =====")
        logger.debug(f"[DEBUG] 분류할 파일 수: {len(pdf_files)}개")
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            logger.debug(f"[DEBUG] 파일 {idx}/{len(pdf_files)}: {pdf_file.name}")
            
            # Review Test는 별도 처리
            is_review_test = any(
                re.search(pattern, str(pdf_file).lower(), re.IGNORECASE)
                for pattern in self.review_test_patterns
            )
            if is_review_test:
                logger.debug(f"[DEBUG]   Review Test로 분류되어 제외됨")
                continue
            
            # 파일 타입 추출
            file_type = extract_file_type(pdf_file)
            logger.debug(f"[DEBUG]   파일 타입 추출 결과: {file_type}")
            
            # 유닛 번호 추출
            unit_num = extract_unit_number(pdf_file)
            logger.debug(f"[DEBUG]   유닛 번호 추출 결과: {unit_num}")
            
            if file_type:
                # 파일 타입별로 그룹화
                if file_type not in categories:
                    categories[file_type] = []
                    logger.debug(f"[DEBUG]   새 카테고리 생성: {file_type}")
                categories[file_type].append(pdf_file)
                logger.debug(f"[DEBUG]   ✅ {file_type} 카테고리에 추가됨 (Unit {unit_num})")
            else:
                # 파일 타입을 찾을 수 없으면 파일명을 카테고리로 사용
                category_name = self._normalize_category_name(pdf_file.stem)
                if category_name not in categories:
                    categories[category_name] = []
                    logger.debug(f"[DEBUG]   새 카테고리 생성: {category_name}")
                categories[category_name].append(pdf_file)
                logger.debug(f"[DEBUG]   ✅ {category_name} 카테고리에 추가됨 (Unit {unit_num})")
        
        # 각 카테고리 내에서 유닛 번호 순서대로 정렬
        logger.debug(f"[DEBUG] 카테고리별 유닛 번호 순서대로 정렬 중...")
        for category_name in categories:
            before_sort = [extract_unit_number(f) for f in categories[category_name]]
            categories[category_name].sort(key=lambda p: extract_unit_number(p))
            after_sort = [extract_unit_number(f) for f in categories[category_name]]
            logger.debug(f"[DEBUG]   {category_name}: 정렬 전 {before_sort} -> 정렬 후 {after_sort}")
        
        logger.info(f"[DEBUG] 파일 분류 완료: {len(categories)}개 카테고리")
        for cat, files in categories.items():
            logger.info(f"[DEBUG]   카테고리 '{cat}': {len(files)}개 파일")
            # 각 파일의 유닛 번호도 로그에 출력
            for f in files:
                unit_num = extract_unit_number(f)
                logger.debug(f"[DEBUG]     - {f.name} -> Unit {unit_num}")
                print(f"[DEBUG]     {cat}: {f.name} -> Unit {unit_num}")
        
        return categories
    
    def _normalize_category_name(self, name: str) -> str:
        """카테고리명 정규화"""
        # 공백 제거, 대소문자 통일 등
        name = name.strip()
        # 필요시 추가 정규화 로직
        return name
    
    def discover(self, directory: Path, exclude_answers: bool = True) -> Dict[str, List[Path]]:
        """
        디렉토리에서 파일 탐색 및 분류 (종합)
        
        Args:
            directory: 탐색할 디렉토리 경로
            exclude_answers: Answer 파일 제외 여부
            
        Returns:
            {'all': [...], 'review_tests': [...], 'categories': {...}}
        """
        # 모든 PDF 파일 찾기
        all_pdfs = self.find_all_pdfs(directory)
        
        # Answer 파일 제외
        if exclude_answers:
            all_pdfs = self.filter_excluded_files(all_pdfs)
        
        # Review Test 분리
        review_tests = self.find_review_tests(all_pdfs)
        main_pdfs = [p for p in all_pdfs if p not in review_tests]
        
        # 카테고리별 분류
        categories = self.categorize_files(main_pdfs)
        
        return {
            'all': all_pdfs,
            'main': main_pdfs,
            'review_tests': review_tests,
            'categories': categories,
        }
