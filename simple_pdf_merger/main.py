#!/usr/bin/env python3
"""
SimplePDFMerger - 간단한 PDF 병합 도구
메인 실행 파일
"""

import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import sys
import os
# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merger import SimplePDFMerger


def main():
    """메인 함수"""
    print("\n=== SimplePDFMerger - 간단한 PDF 병합 도구 ===\n")
    
    # 사용자 입력 받기
    print("병합 방법을 선택하세요:")
    print("1. 파일 목록 직접 입력")
    print("2. 디렉토리 내 모든 PDF 파일 병합")
    
    while True:
        choice = input("\n선택 (1 또는 2): ").strip()
        if choice in ['1', '2']:
            break
        print("1 또는 2를 입력해주세요.")
    
    merger = SimplePDFMerger()
    
    if choice == '1':
        # 파일 목록 직접 입력
        print("\n병합할 PDF 파일 경로를 입력하세요 (한 줄에 하나씩, 빈 줄로 종료):")
        pdf_files = []
        while True:
            file_path = input("파일 경로: ").strip()
            if not file_path:
                break
            pdf_files.append(file_path)
        
        if not pdf_files:
            print("병합할 파일이 없습니다.")
            return
        
        output_filename = input("출력 파일명 (기본값: merged.pdf): ").strip() or "merged.pdf"
        
        success = merger.merge_files(pdf_files, output_filename)
        
    else:
        # 디렉토리 내 모든 PDF 파일 병합
        directory_path = input("PDF 파일이 있는 디렉토리 경로: ").strip()
        output_filename = input("출력 파일명 (기본값: merged.pdf): ").strip() or "merged.pdf"
        
        success = merger.merge_directory(directory_path, output_filename)
    
    # 결과 출력
    if success:
        print("\n✅ PDF 병합이 성공적으로 완료되었습니다!")
        print(f"출력 위치: {merger.output_dir.absolute()}")
    else:
        print("\n❌ PDF 병합에 실패했습니다.")
    
    # 로그 출력
    print("\n=== 병합 로그 ===")
    for log_entry in merger.get_merge_log():
        print(f"- {log_entry}")


if __name__ == "__main__":
    main() 