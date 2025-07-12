"""
간단한 PDF 병합 기능을 제공하는 모듈
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

# PyPDF2 버전 호환성 처리
try:
    from pypdf import PdfReader, PdfWriter  # 최신 버전
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter  # 구 버전
    except ImportError:
        raise ImportError("pypdf 또는 PyPDF2 라이브러리가 설치되어 있지 않습니다. pip install pypdf")

logger = logging.getLogger(__name__)


class SimplePDFMerger:
    """간단한 PDF 병합 클래스"""
    
    def __init__(self, output_dir: str = "merged_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.merge_log = []
        
        logger.info(f"SimplePDFMerger 초기화 완료")
        logger.debug(f"출력 디렉토리: {self.output_dir.absolute()}")
    
    def merge_files(self, pdf_files: List[str], output_filename: str = "merged.pdf") -> bool:
        """
        여러 PDF 파일을 하나로 병합
        
        Args:
            pdf_files: 병합할 PDF 파일 경로 리스트
            output_filename: 출력 파일명
            
        Returns:
            병합 성공 여부
        """
        if not pdf_files:
            logger.error("병합할 PDF 파일이 없습니다.")
            return False
        
        # 파일 존재 여부 확인
        valid_files = []
        for file_path in pdf_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                logger.warning(f"파일을 찾을 수 없음: {file_path}")
        
        if not valid_files:
            logger.error("유효한 PDF 파일이 없습니다.")
            return False
        
        try:
            writer = PdfWriter()
            total_pages = 0
            
            logger.info(f"PDF 병합 시작: {len(valid_files)}개 파일")
            
            for i, file_path in enumerate(valid_files, 1):
                logger.info(f"[{i}/{len(valid_files)}] 처리 중: {os.path.basename(file_path)}")
                
                try:
                    reader = PdfReader(file_path)
                    file_pages = len(reader.pages)
                    
                    for page in reader.pages:
                        writer.add_page(page)
                    
                    total_pages += file_pages
                    logger.info(f"  - {file_pages}페이지 추가됨 (누적: {total_pages}페이지)")
                    
                except Exception as e:
                    logger.error(f"파일 처리 오류 ({file_path}): {e}")
                    self.merge_log.append(f"오류: {os.path.basename(file_path)} - {e}")
                    continue
            
            if total_pages == 0:
                logger.error("추가된 페이지가 없습니다.")
                return False
            
            # 병합된 PDF 저장
            output_path = self.output_dir / output_filename
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            logger.info(f"병합 완료: {output_path.absolute()}")
            logger.info(f"총 페이지 수: {total_pages}")
            
            self.merge_log.append(f"성공: {len(valid_files)}개 파일 병합 완료")
            self.merge_log.append(f"출력 파일: {output_path}")
            self.merge_log.append(f"총 페이지 수: {total_pages}")
            
            return True
            
        except Exception as e:
            logger.error(f"병합 과정에서 오류 발생: {e}")
            self.merge_log.append(f"오류: 병합 실패 - {e}")
            return False
    
    def merge_directory(self, directory_path: str, output_filename: str = "merged.pdf", 
                       file_pattern: str = "*.pdf") -> bool:
        """
        디렉토리 내의 모든 PDF 파일을 병합
        
        Args:
            directory_path: PDF 파일이 있는 디렉토리 경로
            output_filename: 출력 파일명
            file_pattern: 파일 패턴 (기본값: *.pdf)
            
        Returns:
            병합 성공 여부
        """
        if not os.path.isdir(directory_path):
            logger.error(f"디렉토리를 찾을 수 없음: {directory_path}")
            return False
        
        # 디렉토리 내 PDF 파일 찾기
        pdf_files = []
        for file_path in Path(directory_path).glob(file_pattern):
            pdf_files.append(str(file_path))
        
        if not pdf_files:
            logger.error(f"디렉토리에서 PDF 파일을 찾을 수 없음: {directory_path}")
            return False
        
        # 파일명으로 정렬
        pdf_files.sort()
        
        logger.info(f"디렉토리에서 {len(pdf_files)}개 PDF 파일 발견")
        for file_path in pdf_files:
            logger.debug(f"  - {os.path.basename(file_path)}")
        
        return self.merge_files(pdf_files, output_filename)
    
    def get_merge_log(self) -> List[str]:
        """병합 로그 반환"""
        return self.merge_log.copy()
    
    def clear_log(self):
        """로그 초기화"""
        self.merge_log.clear() 