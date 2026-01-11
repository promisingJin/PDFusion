"""
압축 파일 처리 모듈
zip 파일 자동 감지 및 압축 해제 기능 제공
"""

import os
import zipfile
import logging
from pathlib import Path
from typing import List, Optional
import shutil

logger = logging.getLogger(__name__)


class ZipExtractor:
    """압축 파일 추출 클래스"""
    
    def __init__(self, extract_to: Optional[str] = None):
        """
        Args:
            extract_to: 압축 해제할 디렉토리 (None이면 원본과 같은 위치)
        """
        self.extract_to = extract_to
        self.extracted_paths = []
        
    def find_zip_files(self, directory: str) -> List[Path]:
        """
        디렉토리에서 zip 파일 찾기
        
        Args:
            directory: 탐색할 디렉토리 경로
            
        Returns:
            찾은 zip 파일 경로 리스트
        """
        directory_path = Path(directory)
        zip_files = list(directory_path.rglob("*.zip"))
        
        logger.info(f"디렉토리 '{directory}'에서 {len(zip_files)}개의 zip 파일 발견")
        for zip_file in zip_files:
            logger.debug(f"  - {zip_file}")
            
        return zip_files
    
    def extract_zip(self, zip_path: Path, extract_dir: Optional[Path] = None, 
                   remove_after_extract: bool = False) -> Optional[Path]:
        """
        zip 파일 압축 해제
        
        Args:
            zip_path: 압축 해제할 zip 파일 경로
            extract_dir: 압축 해제할 디렉토리 (None이면 zip 파일과 같은 위치)
            remove_after_extract: 압축 해제 후 원본 zip 파일 삭제 여부
            
        Returns:
            압축 해제된 디렉토리 경로 (실패시 None)
        """
        if not zip_path.exists():
            logger.error(f"zip 파일을 찾을 수 없음: {zip_path}")
            return None
        
        if extract_dir is None:
            # zip 파일과 같은 위치에 압축 해제
            # 파일명에서 공백 제거 및 정규화
            folder_name = zip_path.stem.strip()  # 앞뒤 공백 제거
            extract_dir = zip_path.parent / folder_name
        else:
            folder_name = zip_path.stem.strip()
            extract_dir = Path(extract_dir) / folder_name
        
        try:
            logger.info(f"압축 해제 중: {zip_path.name} -> {extract_dir}")
            logger.debug(f"[DEBUG] 폴더명 (공백 제거 후): '{folder_name}'")
            
            # 기존 디렉토리가 있으면 삭제
            if extract_dir.exists():
                logger.warning(f"기존 디렉토리 삭제: {extract_dir}")
                shutil.rmtree(extract_dir)
            
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            # zip 파일 압축 해제 (경로 정규화 포함)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # zip 내부 파일 목록 확인
                logger.debug(f"[DEBUG] zip 내부 파일 목록:")
                for member in zip_ref.namelist()[:5]:  # 처음 5개만 로그
                    logger.debug(f"[DEBUG]   - {member}")
                
                # 안전한 압축 해제: 각 파일을 개별적으로 처리하여 경로 문제 해결
                for member_info in zip_ref.infolist():
                    member_name = member_info.filename
                    
                    # 경로 정규화: 앞뒤 공백 제거, 위험한 경로 제거
                    safe_name = member_name.strip().lstrip('/\\')
                    # 상대 경로로 변환하여 경로 탐색 공격 방지
                    safe_name = safe_name.replace('..', '').replace('\\', os.sep).replace('/', os.sep)
                    
                    if not safe_name:
                        continue
                    
                    # 최종 파일 경로 생성
                    target_path = extract_dir / safe_name
                    
                    # 디렉토리인 경우
                    if member_name.endswith('/') or member_info.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"[DEBUG] 디렉토리 생성: {target_path}")
                    else:
                        # 파일인 경우
                        # 부모 디렉토리 생성
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 파일 추출
                        try:
                            with zip_ref.open(member_info) as source:
                                with open(target_path, 'wb') as target:
                                    target.write(source.read())
                            logger.debug(f"[DEBUG] 파일 추출: {member_name} -> {target_path}")
                        except Exception as e:
                            logger.warning(f"[DEBUG] 파일 추출 실패 ({member_name}): {e}")
                            # 실패한 경우 원본 경로로 시도
                            try:
                                target_path_alt = extract_dir / member_name.replace('\\', os.sep).replace('/', os.sep)
                                target_path_alt.parent.mkdir(parents=True, exist_ok=True)
                                with zip_ref.open(member_info) as source:
                                    with open(target_path_alt, 'wb') as target:
                                        target.write(source.read())
                                logger.debug(f"[DEBUG] 대체 경로로 추출 성공: {target_path_alt}")
                            except Exception as e2:
                                logger.error(f"[DEBUG] 대체 경로로도 추출 실패: {e2}")
            
            logger.info(f"압축 해제 완료: {extract_dir}")
            self.extracted_paths.append(extract_dir)
            
            # 압축 해제 후 원본 삭제
            if remove_after_extract:
                zip_path.unlink()
                logger.info(f"원본 zip 파일 삭제: {zip_path}")
            
            return extract_dir
            
        except Exception as e:
            logger.error(f"압축 해제 실패 ({zip_path}): {e}")
            return None
    
    def extract_all_zips(self, directory: str, remove_after_extract: bool = False) -> List[Path]:
        """
        디렉토리 내 모든 zip 파일 압축 해제
        
        Args:
            directory: 탐색할 디렉토리 경로
            remove_after_extract: 압축 해제 후 원본 zip 파일 삭제 여부
            
        Returns:
            압축 해제된 디렉토리 경로 리스트
        """
        zip_files = self.find_zip_files(directory)
        extracted_dirs = []
        
        for zip_file in zip_files:
            extracted_dir = self.extract_zip(zip_file, remove_after_extract=remove_after_extract)
            if extracted_dir:
                extracted_dirs.append(extracted_dir)
        
        logger.info(f"총 {len(extracted_dirs)}개의 zip 파일 압축 해제 완료")
        return extracted_dirs
    
    def cleanup_extracted(self):
        """압축 해제된 디렉토리 정리"""
        for path in self.extracted_paths:
            if path.exists():
                try:
                    shutil.rmtree(path)
                    logger.info(f"정리 완료: {path}")
                except Exception as e:
                    logger.warning(f"정리 실패 ({path}): {e}")
