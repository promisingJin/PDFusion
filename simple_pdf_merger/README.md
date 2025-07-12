# SimplePDFMerger

간단하고 빠른 PDF 병합 도구입니다.

## 기능

- 여러 PDF 파일을 하나로 병합
- 디렉토리 내 모든 PDF 파일 자동 병합
- 파일명 순서로 자동 정렬
- 상세한 로그 및 오류 처리

## 설치

```bash
pip install pypdf
```

## 사용법

### 1. 명령줄에서 실행

```bash
python simple_pdf_merger/main.py
```

### 2. Python 코드에서 사용

```python
from simple_pdf_merger import SimplePDFMerger

# 병합기 초기화
merger = SimplePDFMerger()

# 방법 1: 파일 목록 직접 지정
pdf_files = [
    "file1.pdf",
    "file2.pdf", 
    "file3.pdf"
]
success = merger.merge_files(pdf_files, "output.pdf")

# 방법 2: 디렉토리 내 모든 PDF 파일 병합
success = merger.merge_directory("pdf_folder", "output.pdf")

# 로그 확인
for log in merger.get_merge_log():
    print(log)
```

## 주요 메서드

### `merge_files(pdf_files, output_filename)`
- 여러 PDF 파일을 하나로 병합
- `pdf_files`: 병합할 PDF 파일 경로 리스트
- `output_filename`: 출력 파일명

### `merge_directory(directory_path, output_filename, file_pattern)`
- 디렉토리 내의 모든 PDF 파일을 병합
- `directory_path`: PDF 파일이 있는 디렉토리
- `output_filename`: 출력 파일명
- `file_pattern`: 파일 패턴 (기본값: "*.pdf")

### `get_merge_log()`
- 병합 과정의 로그 반환

## 출력

병합된 PDF 파일은 `merged_output` 디렉토리에 저장됩니다.

## 예제

```python
from simple_pdf_merger import SimplePDFMerger

merger = SimplePDFMerger()

# 여러 파일 병합
files = ["chapter1.pdf", "chapter2.pdf", "chapter3.pdf"]
merger.merge_files(files, "complete_book.pdf")

# 폴더 내 모든 PDF 병합
merger.merge_directory("documents", "all_documents.pdf")
``` 