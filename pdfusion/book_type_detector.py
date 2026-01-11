"""
책 타입 감지 모듈 (LC/RC)
파일명, 폴더명, PDF 내용을 기반으로 LC/RC 자동 감지
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class BookTypeDetector:
    """책 타입(LC/RC) 감지 클래스"""
    
    # LC/RC 패턴 정의
    LC_PATTERNS = [
        r'\bLC\b',
        r'\bL\.C\.',
        r'left\s*cover',
        r'왼쪽',
        r'좌측',
        r'_LC[_\s]',  # 파일명 패턴: _LC_ 또는 _LC
        r'[_\s]LC[_\s]',
    ]
    
    RC_PATTERNS = [
        r'\bRC\b',
        r'\bR\.C\.',
        r'right\s*cover',
        r'오른쪽',
        r'우측',
        r'_RC[_\s]',  # 파일명 패턴: _RC_ 또는 _RC
        r'[_\s]RC[_\s]',
    ]
    
    def __init__(self):
        self.lc_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.LC_PATTERNS]
        self.rc_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.RC_PATTERNS]
    
    def detect_from_path(self, path: Path) -> Optional[str]:
        """
        경로(파일명/폴더명)에서 LC/RC 감지
        
        Args:
            path: 파일 또는 폴더 경로
            
        Returns:
            'LC', 'RC', 또는 None
        """
        path_str = str(path).lower()
        logger.debug(f"[DEBUG] 경로에서 LC/RC 감지 시도: {path}")
        logger.debug(f"[DEBUG] 경로 문자열 (소문자): {path_str}")
        
        # 간단한 규칙: Listening → LC, Reading → RC
        if 'listening' in path_str:
            logger.info(f"[DEBUG] ✅ LC 감지 성공! (Listening 발견: {path})")
            print(f"[DEBUG] LC 감지: {path.name} (Listening 포함)")
            return 'LC'
        
        if 'reading' in path_str:
            logger.info(f"[DEBUG] ✅ RC 감지 성공! (Reading 발견: {path})")
            print(f"[DEBUG] RC 감지: {path.name} (Reading 포함)")
            return 'RC'
        
        # 기존 패턴도 확인 (백업)
        logger.debug(f"[DEBUG] 기존 LC 패턴 {len(self.lc_patterns)}개 확인 중...")
        for idx, pattern in enumerate(self.lc_patterns):
            match = pattern.search(path_str)
            logger.debug(f"[DEBUG]   패턴 {idx+1}: {pattern.pattern} -> 매칭: {bool(match)}")
            if match:
                logger.info(f"[DEBUG] ✅ LC 감지 성공! (경로: {path}, 패턴: {pattern.pattern})")
                print(f"[DEBUG] LC 감지: {path.name} (패턴: {pattern.pattern})")
                return 'LC'
        
        logger.debug(f"[DEBUG] RC 패턴 {len(self.rc_patterns)}개 확인 중...")
        for idx, pattern in enumerate(self.rc_patterns):
            match = pattern.search(path_str)
            logger.debug(f"[DEBUG]   패턴 {idx+1}: {pattern.pattern} -> 매칭: {bool(match)}")
            if match:
                logger.info(f"[DEBUG] ✅ RC 감지 성공! (경로: {path}, 패턴: {pattern.pattern})")
                print(f"[DEBUG] RC 감지: {path.name} (패턴: {pattern.pattern})")
                return 'RC'
        
        logger.debug(f"[DEBUG] ❌ LC/RC 감지 실패: {path}")
        return None
    
    def detect_from_pdf_content(self, pdf_path: Path, max_pages: int = 3) -> Optional[str]:
        """
        PDF 내용에서 LC/RC 감지 (처음 몇 페이지만 확인)
        
        Args:
            pdf_path: PDF 파일 경로
            max_pages: 확인할 최대 페이지 수
            
        Returns:
            'LC', 'RC', 또는 None
        """
        try:
            reader = PdfReader(str(pdf_path))
            pages_to_check = min(max_pages, len(reader.pages))
            
            for i in range(pages_to_check):
                text = reader.pages[i].extract_text() or ""
                text_lower = text.lower()
                
                # LC 패턴 확인
                for pattern in self.lc_patterns:
                    if pattern.search(text_lower):
                        logger.debug(f"LC 감지 (PDF 내용, 페이지 {i+1}): {pdf_path}")
                        return 'LC'
                
                # RC 패턴 확인
                for pattern in self.rc_patterns:
                    if pattern.search(text_lower):
                        logger.debug(f"RC 감지 (PDF 내용, 페이지 {i+1}): {pdf_path}")
                        return 'RC'
            
            return None
            
        except Exception as e:
            logger.warning(f"PDF 내용 분석 실패 ({pdf_path}): {e}")
            return None
    
    def detect_from_directory(self, directory: Path) -> Optional[str]:
        """
        디렉토리 내 파일들을 분석하여 LC/RC 감지
        
        Args:
            directory: 분석할 디렉토리 경로
            
        Returns:
            'LC', 'RC', 또는 None
        """
        logger.debug(f"[DEBUG] 디렉토리 분석 시작: {directory}")
        
        # 1. 디렉토리명에서 감지
        logger.debug(f"[DEBUG] [1단계] 디렉토리명에서 감지 시도")
        book_type = self.detect_from_path(directory)
        if book_type:
            logger.info(f"[DEBUG] ✅ 디렉토리명에서 {book_type} 감지 성공")
            return book_type
        
        # 2. 하위 디렉토리명에서 감지
        logger.debug(f"[DEBUG] [2단계] 하위 디렉토리명에서 감지 시도")
        subdirs = [d for d in directory.iterdir() if d.is_dir()]
        logger.debug(f"[DEBUG] 하위 디렉토리 {len(subdirs)}개 발견")
        for idx, subdir in enumerate(subdirs, 1):
            logger.debug(f"[DEBUG]   하위 디렉토리 {idx}/{len(subdirs)}: {subdir.name}")
            book_type = self.detect_from_path(subdir)
            if book_type:
                logger.info(f"[DEBUG] ✅ 하위 디렉토리명에서 {book_type} 감지 성공: {subdir.name}")
                return book_type
        
        # 3. PDF 파일명에서 감지
        logger.debug(f"[DEBUG] [3단계] PDF 파일명에서 감지 시도")
        pdf_files = list(directory.rglob("*.pdf"))
        logger.debug(f"[DEBUG] PDF 파일 {len(pdf_files)}개 발견, 처음 10개 확인")
        for idx, pdf_file in enumerate(pdf_files[:10], 1):
            logger.debug(f"[DEBUG]   PDF 파일 {idx}/10: {pdf_file.name}")
            book_type = self.detect_from_path(pdf_file)
            if book_type:
                logger.info(f"[DEBUG] ✅ PDF 파일명에서 {book_type} 감지 성공: {pdf_file.name}")
                return book_type
        
        # 4. 파일 타입 기반 감지 (새로운 방법)
        # Translation Sheet나 Unscramble Sheet가 있으면 RC, 없으면 LC
        logger.debug(f"[DEBUG] [4단계] 파일 타입 기반 감지 시도")
        has_translation = any('translation' in f.name.lower() and 'sheet' in f.name.lower() for f in pdf_files)
        has_unscramble = any('unscramble' in f.name.lower() and 'sheet' in f.name.lower() for f in pdf_files)
        has_word_test = any('word' in f.name.lower() and 'test' in f.name.lower() for f in pdf_files)
        has_word_list = any('word' in f.name.lower() and 'list' in f.name.lower() for f in pdf_files)
        
        logger.debug(f"[DEBUG] 파일 타입 분석:")
        logger.debug(f"[DEBUG]   Translation Sheet: {has_translation}")
        logger.debug(f"[DEBUG]   Unscramble Sheet: {has_unscramble}")
        logger.debug(f"[DEBUG]   Word Test: {has_word_test}")
        logger.debug(f"[DEBUG]   Word List: {has_word_list}")
        
        if has_translation or has_unscramble:
            logger.info(f"[DEBUG] ✅ 파일 타입 기반으로 RC 감지 성공 (Translation/Unscramble Sheet 존재)")
            print(f"[DEBUG] RC 감지: Translation Sheet 또는 Unscramble Sheet 파일 발견")
            return 'RC'
        elif has_word_test or has_word_list:
            logger.info(f"[DEBUG] ✅ 파일 타입 기반으로 LC 감지 성공 (Word Test/List만 존재)")
            print(f"[DEBUG] LC 감지: Word Test/List만 발견 (Translation/Unscramble Sheet 없음)")
            return 'LC'
        
        # 5. PDF 내용에서 감지 (처음 몇 개만)
        logger.debug(f"[DEBUG] [5단계] PDF 내용에서 감지 시도")
        logger.debug(f"[DEBUG] PDF 내용 분석: 처음 3개 파일 확인")
        for idx, pdf_file in enumerate(pdf_files[:3], 1):
            logger.debug(f"[DEBUG]   PDF 내용 분석 {idx}/3: {pdf_file.name}")
            book_type = self.detect_from_pdf_content(pdf_file)
            if book_type:
                logger.info(f"[DEBUG] ✅ PDF 내용에서 {book_type} 감지 성공: {pdf_file.name}")
                return book_type
        
        logger.warning(f"[DEBUG] ❌ 모든 방법으로 LC/RC를 감지할 수 없음: {directory}")
        return None
    
    def detect(self, path: Path) -> Dict[str, Optional[str]]:
        """
        종합적인 LC/RC 감지 (여러 방법 시도)
        
        Args:
            path: 파일 또는 디렉토리 경로
            
        Returns:
            {'type': 'LC'|'RC'|None, 'method': 'path'|'content'|'directory'|None}
        """
        path = Path(path)
        logger.info(f"[DEBUG] ===== LC/RC 감지 시작 =====")
        logger.info(f"[DEBUG] 대상 경로: {path}")
        logger.info(f"[DEBUG] 경로 타입: {'디렉토리' if path.is_dir() else '파일'}")
        
        # 1. 경로에서 감지
        logger.info(f"[DEBUG] [방법 1] 경로에서 직접 감지 시도")
        book_type = self.detect_from_path(path)
        if book_type:
            logger.info(f"[DEBUG] ✅ [방법 1] 성공! 타입: {book_type}, 방법: path")
            return {'type': book_type, 'method': 'path'}
        
        # 2. 디렉토리인 경우 디렉토리 분석
        if path.is_dir():
            logger.info(f"[DEBUG] [방법 2] 디렉토리 분석 시도")
            book_type = self.detect_from_directory(path)
            if book_type:
                logger.info(f"[DEBUG] ✅ [방법 2] 성공! 타입: {book_type}, 방법: directory")
                return {'type': book_type, 'method': 'directory'}
        
        # 3. PDF 파일인 경우 내용 분석
        if path.suffix.lower() == '.pdf':
            logger.info(f"[DEBUG] [방법 3] PDF 내용 분석 시도")
            book_type = self.detect_from_pdf_content(path)
            if book_type:
                logger.info(f"[DEBUG] ✅ [방법 3] 성공! 타입: {book_type}, 방법: content")
                return {'type': book_type, 'method': 'content'}
        
        logger.warning(f"[DEBUG] ❌ 모든 방법 실패. LC/RC를 감지할 수 없습니다.")
        return {'type': None, 'method': None}
