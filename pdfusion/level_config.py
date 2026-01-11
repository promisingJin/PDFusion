"""
레벨별 설정 관리 모듈
레벨별로 병합할 파일 규칙을 정의하고 관리
"""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class LevelConfig:
    """레벨별 설정 관리 클래스"""
    
    def __init__(self):
        # 레벨별 파일 규칙 정의
        # 예: Level 1은 ['Unit Test', 'Grammar'] 파일만, Level 2는 ['Vocabulary', 'Reading'] 파일만
        self.level_rules: Dict[str, Dict] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """기본 레벨별 규칙 초기화"""
        # LC/RC에 따른 규칙은 get_files_for_level에서 처리
        # 여기서는 기본 레벨 규칙만 정의
        self.level_rules = {
            'Level 1': {
                'include_patterns': [],
                'exclude_patterns': [
                    r'answer',
                    r'답지',
                    r'정답',
                ],
                'required_files': [],
            },
            # 모든 레벨에 동일한 기본 규칙 적용
        }
    
    def detect_level(self, path: Path) -> Optional[str]:
        """
        경로에서 레벨 정보 추출
        
        Args:
            path: 파일 또는 디렉토리 경로
            
        Returns:
            레벨 문자열 (예: 'Level 1') 또는 None
        """
        path_str = str(path).lower()
        logger.debug(f"[DEBUG] 레벨 감지 시도: {path}")
        logger.debug(f"[DEBUG] 경로 문자열 (소문자): {path_str}")
        
        # 레벨 패턴 매칭 (다양한 패턴 지원)
        level_patterns = [
            r'level\s*(\d+)',           # "Level 1", "Level 2"
            r'_l(\d+)_',                # "_L1_", "_L2_" (파일명 패턴)
            r'[_\s]l(\d+)[_\s]',       # " L1 ", "_L1_"
            r'\bl(\d+)\b',             # "L1", "L2" (단어 경계)
            r'레벨\s*(\d+)',            # "레벨 1"
        ]
        
        logger.debug(f"[DEBUG] 레벨 패턴 {len(level_patterns)}개 확인 중...")
        for idx, pattern in enumerate(level_patterns, 1):
            match = re.search(pattern, path_str, re.IGNORECASE)
            logger.debug(f"[DEBUG]   패턴 {idx}: {pattern} -> 매칭: {bool(match)}")
            if match:
                level_num = match.group(1)
                level_name = f"Level {level_num}"
                logger.info(f"[DEBUG] ✅ 레벨 감지 성공! {level_name} (경로: {path}, 패턴: {pattern})")
                print(f"[DEBUG] 레벨 감지: {level_name} (패턴: {pattern})")
                return level_name
        
        logger.debug(f"[DEBUG] ❌ 레벨 감지 실패: {path}")
        return None
    
    def extract_book_number(self, path: Path) -> Optional[int]:
        """
        파일명/경로에서 책 번호 추출 (예: Bricks Reading 60 → 60)
        
        Args:
            path: 파일 또는 디렉토리 경로
            
        Returns:
            책 번호 (정수) 또는 None
        """
        path_str = str(path)
        logger.debug(f"[DEBUG] 책 번호 추출 시도: {path}")
        
        # 다양한 패턴으로 숫자 추출
        # 예: "Bricks Reading 60", "Reading 80 Nonfiction", "60_L1"
        number_patterns = [
            r'reading\s+(\d+)',          # "Reading 60", "Reading 80"
            r'listening\s+(\d+)',       # "Listening 60", "Listening 80"
            r'\b(\d+)\s*[_\s]',        # "60_", "80 Nonfiction"
            r'[_\s](\d+)[_\s]',        # "_60_", "_80_"
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, path_str, re.IGNORECASE)
            if match:
                try:
                    number = int(match.group(1))
                    logger.debug(f"[DEBUG] ✅ 책 번호 추출 성공: {number} (경로: {path}, 패턴: {pattern})")
                    return number
                except ValueError:
                    continue
        
        logger.debug(f"[DEBUG] ❌ 책 번호 추출 실패: {path}")
        return None
    
    def get_zip_patterns(self, book_type: Optional[str] = None, book_path: Optional[Path] = None) -> List[str]:
        """
        zip 파일 필터링용 패턴 리스트 반환 (문자열 형식)
        
        Args:
            book_type: 책 타입 ('LC' 또는 'RC')
            book_path: 책 폴더 경로 (책 번호 추출용)
            
        Returns:
            zip 파일명 매칭용 문자열 패턴 리스트 (예: ['word list', 'word test', ...])
        """
        if not book_type:
            return []
        
        book_number = None
        if book_path:
            book_number = self.extract_book_number(book_path)
        
        # LC 타입
        if book_type.upper() == 'LC':
            return ['word list', 'word test', 'wordlist', 'wordtest']
        
        # RC 타입: 책 번호에 따라 다른 패턴
        elif book_type.upper() == 'RC':
            if book_number is not None:
                if book_number <= 60:
                    # 60 이하: Word List, Word Writing, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
                    base_patterns = ['word list', 'word writing', 'word test', 'translation sheet', 
                                    'unscramble sheet', 'unit test']
                elif book_number >= 100:
                    # 100 이상: Word List, Word Test, Translation Sheet, Unscramble Sheet, Grammar Sheet, Unit Test
                    base_patterns = ['word list', 'word test', 'translation sheet', 'unscramble sheet', 
                                    'grammar sheet', 'unit test']
                elif book_number >= 80:
                    # 80-99: Word List, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
                    base_patterns = ['word list', 'word test', 'translation sheet', 'unscramble sheet', 
                                    'unit test']
                else:
                    # 61-79: Word List, Word Test, Translation Sheet, Unscramble Sheet
                    base_patterns = ['word list', 'word test', 'translation sheet', 'unscramble sheet']
            else:
                # 숫자를 추출할 수 없으면 기본 패턴 사용
                base_patterns = ['word list', 'word test', 'translation sheet', 'unscramble sheet', 'unit test']
            
            # 공백 없는 변형도 추가 (wordlist, wordtest 등)
            patterns = []
            for pattern in base_patterns:
                patterns.append(pattern)  # 원본 패턴
                patterns.append(pattern.replace(' ', ''))  # 공백 제거 버전
            
            return patterns
        
        # 알 수 없는 타입
        return []
    
    def get_files_for_level(self, level: str, all_files: List[Path], 
                           book_type: Optional[str] = None, book_path: Optional[Path] = None,
                           skip_required_check: bool = False) -> Optional[List[Path]]:
        """
        레벨 및 책 타입에 맞는 파일 필터링
        
        Args:
            level: 레벨 문자열 (예: 'Level 1')
            all_files: 모든 파일 경로 리스트
            book_type: 책 타입 ('LC' 또는 'RC', 필수)
            book_path: 책 폴더 경로 (RC 타입일 때 숫자 추출용)
            
        Returns:
            필터링된 파일 경로 리스트
        """
        logger.info(f"[DEBUG] ===== 파일 필터링 시작 =====")
        logger.info(f"[DEBUG] 레벨: {level}, 책 타입: {book_type}")
        logger.info(f"[DEBUG] 전체 파일 수: {len(all_files)}개")
        
        if not book_type:
            logger.warning("[DEBUG] ⚠️  책 타입이 지정되지 않았습니다. 모든 파일 반환.")
            return all_files
        
        # 기본 규칙 가져오기 (없으면 빈 규칙 사용)
        rules = self.level_rules.get(level, {
            'include_patterns': [],
            'exclude_patterns': [],
            'required_files': []
        })
        logger.debug(f"[DEBUG] 레벨 규칙: {rules}")
        
        filtered_files = []
        required_patterns = []  # 필수 파일 패턴
        optional_required_groups = []  # 선택적 필수 그룹 (여러 패턴 중 하나라도 있으면 OK)
        
        # LC/RC별 포함 패턴 정의
        if book_type.upper() == 'LC':
            # LC: Word Test와 Word List만
            include_patterns = [
                r'word\s*test',
                r'word\s*list',
            ]
            logger.info(f"[DEBUG] LC 타입: Word Test, Word List만 포함")
        elif book_type.upper() == 'RC':
            # RC 타입: 파일명의 숫자에 따라 다른 패턴 적용
            book_number = None
            if book_path:
                book_number = self.extract_book_number(book_path)
                logger.info(f"[DEBUG] RC 타입 - 책 번호 추출: {book_number}")
            
            # 숫자에 따라 다른 패턴 정의
            if book_number is not None:
                if book_number <= 60:
                    # 60 이하: Word List, Word Writing 또는 Word Test (둘 중 하나라도 있으면 포함), Translation Sheet, Unscramble Sheet, Unit Test
                    # Level 3 등 특정 레벨에서는 Word Test도 포함될 수 있음
                    include_patterns = [
                        r'word\s*list',
                        r'word\s*writing',
                        r'word\s*test',  # Word Test도 포함 패턴에 추가
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'unit\s*test',
                    ]
                    # 필수 파일: Word Writing과 Word Test는 둘 중 하나만 있어도 됨 (선택적)
                    required_patterns = [
                        r'word\s*list',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'unit\s*test',
                    ]
                    # Word Writing 또는 Word Test 중 하나는 있어야 함 (선택적 필수 그룹)
                    optional_required_groups = [
                        [r'word\s*writing', r'word\s*test'],  # 둘 중 하나라도 있으면 OK
                    ]
                    logger.info(f"[DEBUG] RC 타입 (숫자 {book_number} ≤ 60): Word List, Word Writing/Word Test (선택), Translation Sheet, Unscramble Sheet, Unit Test 포함")
                elif book_number >= 100:
                    # 100 이상: Word List, Word Test, Translation Sheet, Unscramble Sheet, Grammar Sheet, Unit Test
                    include_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'grammar\s*sheet',
                        r'unit\s*test',
                    ]
                    required_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'grammar\s*sheet',
                        r'unit\s*test',
                    ]
                    logger.info(f"[DEBUG] RC 타입 (숫자 {book_number} ≥ 100): Word List, Word Test, Translation Sheet, Unscramble Sheet, Grammar Sheet, Unit Test 포함 (모두 필수)")
                elif book_number >= 80:
                    # 80-99: Word List, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
                    include_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'unit\s*test',
                    ]
                    required_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                        r'unit\s*test',
                    ]
                    logger.info(f"[DEBUG] RC 타입 (숫자 {book_number} 80-99): Word List, Word Test, Translation Sheet, Unscramble Sheet, Unit Test 포함 (모두 필수)")
                else:
                    # 61-79: 기본 패턴 (Word List, Word Test, Translation Sheet, Unscramble Sheet)
                    include_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                    ]
                    required_patterns = [
                        r'word\s*list',
                        r'word\s*test',
                        r'translation\s*sheet',
                        r'unscramble\s*sheet',
                    ]
                    logger.info(f"[DEBUG] RC 타입 (숫자 {book_number} 61-79): Word List, Word Test, Translation Sheet, Unscramble Sheet 포함 (모두 필수)")
            else:
                # 숫자를 추출할 수 없으면 기본 패턴 사용
                include_patterns = [
                    r'word\s*list',
                    r'word\s*test',
                    r'translation\s*sheet',
                    r'unscramble\s*sheet',
                ]
                required_patterns = [
                    r'word\s*list',
                    r'word\s*test',
                    r'translation\s*sheet',
                    r'unscramble\s*sheet',
                ]
                logger.warning(f"[DEBUG] RC 타입 - 책 번호를 추출할 수 없어 기본 패턴 사용")
        else:
            # 알 수 없는 타입: 모든 파일 포함
            include_patterns = []
            required_patterns = []
            logger.warning(f"[DEBUG] ⚠️  알 수 없는 책 타입: {book_type}. 모든 파일 포함.")
        
        logger.debug(f"[DEBUG] 포함 패턴: {include_patterns}")
        logger.debug(f"[DEBUG] 필수 패턴: {required_patterns}")
        logger.debug(f"[DEBUG] 제외 패턴: {rules.get('exclude_patterns', [])}")
        logger.debug(f"[DEBUG] 선택적 필수 그룹: {optional_required_groups}")
        
        # 디버그: Word Test 관련 파일 확인
        word_test_files = [f for f in all_files if 'test' in f.name.lower() and 'word' in f.name.lower()]
        logger.info(f"[DEBUG] Word Test 관련 파일 발견: {len(word_test_files)}개")
        for f in word_test_files:
            logger.info(f"[DEBUG]   - {f.name}")
        
        included_count = 0
        excluded_count = 0
        
        for file_path in all_files:
            file_name = file_path.name.lower()
            file_str = str(file_path).lower()
            logger.debug(f"[DEBUG] 파일 검사: {file_path.name}")
            
            # 제외 패턴 확인
            excluded = False
            for exclude_pattern in rules.get('exclude_patterns', []):
                if re.search(exclude_pattern, file_str, re.IGNORECASE):
                    logger.debug(f"[DEBUG]   ❌ 제외됨 (패턴: {exclude_pattern})")
                    excluded = True
                    excluded_count += 1
                    break
            
            if excluded:
                continue
            
            # LC/RC별 포함 패턴 확인
            included = False
            matched_pattern = None
            if include_patterns:
                for include_pattern in include_patterns:
                    if re.search(include_pattern, file_str, re.IGNORECASE):
                        matched_pattern = include_pattern
                        logger.debug(f"[DEBUG]   ✅ 포함됨 (패턴: {include_pattern})")
                        included = True
                        included_count += 1
                        break
                if not included:
                    logger.debug(f"[DEBUG]   ❌ 포함 패턴 불일치 - 모든 패턴 확인:")
                    for pattern in include_patterns:
                        logger.debug(f"[DEBUG]     - {pattern}: {bool(re.search(pattern, file_str, re.IGNORECASE))}")
            else:
                # 패턴이 없으면 모두 포함
                included = True
                included_count += 1
                logger.debug(f"[DEBUG]   ✅ 포함됨 (패턴 없음 - 모두 포함)")
            
            # 필수 파일 확인
            if rules.get('required_files'):
                for required in rules['required_files']:
                    if required.lower() in file_str:
                        included = True
                        logger.debug(f"[DEBUG]   ✅ 필수 파일로 포함됨: {required}")
                        break
            
            if included:
                filtered_files.append(file_path)
                logger.debug(f"[DEBUG]   최종 결과: ✅ 포함")
            else:
                logger.debug(f"[DEBUG]   최종 결과: ❌ 제외")
        
        # 필수 파일 검증
        if required_patterns and not skip_required_check:
            logger.info(f"[DEBUG] ===== 필수 파일 검증 시작 =====")
            found_required = set()
            for required_pattern in required_patterns:
                for file_path in filtered_files:
                    file_str = str(file_path).lower()
                    if re.search(required_pattern, file_str, re.IGNORECASE):
                        found_required.add(required_pattern)
                        logger.debug(f"[DEBUG]   ✅ 필수 파일 발견: {required_pattern} -> {file_path.name}")
                        break
            
            missing_required = set(required_patterns) - found_required
            
            # 선택적 필수 그룹 검증 (여러 패턴 중 하나라도 있으면 OK)
            if optional_required_groups:
                logger.info(f"[DEBUG] ===== 선택적 필수 그룹 검증 시작 =====")
                for group in optional_required_groups:
                    group_found = False
                    for pattern in group:
                        for file_path in filtered_files:
                            file_str = str(file_path).lower()
                            if re.search(pattern, file_str, re.IGNORECASE):
                                group_found = True
                                logger.debug(f"[DEBUG]   ✅ 선택적 필수 그룹 중 하나 발견: {pattern} -> {file_path.name}")
                                break
                        if group_found:
                            break
                    if not group_found:
                        logger.warning(f"[DEBUG]   ⚠️  선택적 필수 그룹 누락: {group} (경고만, 계속 진행)")
                        # 선택적 필수 그룹은 경고만 하고 계속 진행
            
            if missing_required:
                logger.error(f"[DEBUG] ❌ 필수 파일 누락: {missing_required}")
                # 필터링된 파일과 누락 정보를 함께 반환하기 위해 특별한 처리
                # config_v5.py에서 필수 파일 검증을 별도로 수행하고 사용자에게 선택권 제공
                # 여기서는 필터링된 파일을 반환하되, 누락 정보를 로그에 기록
                logger.warning(f"[DEBUG] 필수 파일 누락 감지: {missing_required}")
                # 필터링된 파일은 반환하되, 누락 정보를 속성으로 저장
                # 하지만 반환 타입이 List[Path]이므로, None을 반환하고 config_v5.py에서 처리
                return None  # None 반환하여 config_v5.py에서 사용자 선택 처리
        
        logger.info(f"[DEBUG] 필터링 결과: {len(filtered_files)}/{len(all_files)}개 파일 선택됨")
        logger.info(f"[DEBUG] 포함: {included_count}개, 제외: {excluded_count}개")
        print(f"[DEBUG] 필터링 완료: {len(filtered_files)}/{len(all_files)}개 파일")
        return filtered_files
    
    def add_level_rule(self, level: str, include_patterns: List[str] = None,
                      exclude_patterns: List[str] = None, required_files: List[str] = None):
        """
        레벨별 규칙 추가/수정
        
        Args:
            level: 레벨 문자열
            include_patterns: 포함할 파일 패턴 리스트
            exclude_patterns: 제외할 파일 패턴 리스트
            required_files: 필수 파일명 리스트
        """
        self.level_rules[level] = {
            'include_patterns': include_patterns or [],
            'exclude_patterns': exclude_patterns or [],
            'required_files': required_files or [],
        }
        logger.info(f"레벨 '{level}' 규칙 추가/수정됨")
    
    def get_all_levels(self) -> List[str]:
        """정의된 모든 레벨 리스트 반환"""
        return list(self.level_rules.keys())
    
    def has_level(self, level: str) -> bool:
        """레벨 규칙 존재 여부 확인"""
        return level in self.level_rules
