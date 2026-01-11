# 트러블슈팅 로그 (Troubleshooting Log) - 2025-01-13

## 개요

오늘 개발 과정에서 발생한 주요 문제들과 해결 과정을 기록합니다. 각 이슈는 **문제 상황 → 원인 분석 → 시도한 해결책 → 최종 해결** 순서로 정리했습니다.

---

## Issue #1: Word Test A/B 선택 질문이 표시되지 않음

### 🔴 문제 상황

**증상:**
```
카테고리별 파일 목록:
  [Word Test] (2개)
    1. Bricks Reading 170 Nonfiction_L1_Word Test\Bricks Reading 170 Nonfiction_L1_Word Test A.pdf
    2. Bricks Reading 170 Nonfiction_L1_Word Test\Bricks Reading 170 Nonfiction_L1_Word Test B.pdf

이대로 병합할까요? (y/n, 기본값: y):
```

- Word Test A와 B 파일이 모두 있는데도 사용자 선택 질문이 표시되지 않음
- `[3-5단계] 유닛 정보 추출` 단계에서 `has_letter_suffix` 감지가 작동하지 않음

**로그 분석:**
- `[3-5단계]` 로그가 전혀 출력되지 않음
- `has_letter_suffix` 변수가 제대로 감지되지 않음

### 🔍 원인 분석

1. **정규표현식 패턴 문제**
   ```python
   # 기존 패턴: 너무 넓은 매칭
   pattern = r'\b[A-Z]\b'  # "Word Test"에서 'T'도 매칭됨
   ```

2. **변수 스코프 문제**
   ```python
   if len(files) > 1:
       has_letter_suffix = any(...)  # 이 블록 안에서만 정의됨
   else:
       # has_letter_suffix를 사용하려고 하면 NameError 발생 가능
   ```

3. **로직 실행 순서 문제**
   - `[3-4단계]`에서 사용자 확인 후 `[3-5단계]`가 실행됨
   - 하지만 Word Test 선택은 그 전에 처리되어야 함

### 🛠️ 시도한 해결책

#### 시도 1: 정규표현식 패턴 수정
```python
# 파일명 끝의 단일 알파벳만 감지하도록 수정
pattern = r'[_\s]([A-Z])$'  # "Word Test A"에서 'A'만 매칭
```

**결과:** ❌ 여전히 선택 질문이 나오지 않음

#### 시도 2: 변수 스코프 수정
```python
has_letter_suffix = False  # 함수 스코프에서 초기화
if len(files) > 1:
    has_letter_suffix = any(...)
```

**결과:** ⚠️ 변수 오류는 해결되었지만 여전히 선택 질문이 나오지 않음

#### 시도 3: 별도 단계로 분리
```python
# [3-3.6단계] Word Test 파일 처리 추가
if 'Word Test' in categories:
    # A/B 타입 감지 및 사용자 선택 로직
```

**결과:** ✅ 성공! 선택 질문이 정상적으로 표시됨

### ✅ 최종 해결책

**구현 위치:** `pdfusion/config_v5.py` - `[3-3.6단계]` 추가

```python
# 3-3.6. Word Test 파일 처리 (A/B 타입 선택)
if 'Word Test' in categories:
    print(f"\n[3-3.6단계] Word Test 파일 처리")
    files = categories['Word Test']
    
    # A 타입과 B 타입 파일 분리
    files_a = [f for f in files if is_test_a(f)]
    files_b = [f for f in files if is_test_b(f)]
    
    if files_a and files_b:
        # 사용자에게 선택 옵션 제공
        print(f"  1. Test A만 사용")
        print(f"  2. Test B만 사용")
        print(f"  3. 둘 다 사용 (기본값)")
        choice = input("  선택 (1/2/3, 기본값: 3): ").strip()
        # ... 선택에 따라 파일 필터링
```

### 📚 배운 점

- **특수한 파일 타입은 별도 단계로 처리**: 일반적인 파일 처리 로직보다 먼저 처리해야 함
- **사용자 상호작용은 가능한 한 빨리**: 파일 목록 확인 전에 선택 질문을 받는 것이 UX에 유리
- **정규표현식은 구체적으로**: 넓은 패턴보다는 정확한 패턴이 안전함

---

## Issue #2: 필수 파일 누락 시 병합이 강제 중단됨

### 🔴 문제 상황

**증상:**
```
Bricks Reading 50 Nonfiction Level 3 교재를 진행하려 보니, 
이 폴더 안에는 Word Writing Sheet이 없어서 pdf 병합 진행이 되지 않았어.
```

**에러 메시지:**
```
❌ [오류] 필수 파일이 누락되었습니다!
   누락된 파일 패턴: word\s*writing
   필터링된 파일 목록:
     - Bricks Reading 50 Nonfiction_L3_Word List.pdf
     - Bricks Reading 50 Nonfiction_L3_Translation Sheet.pdf
     - ...
⚠️  필수 파일이 없으면 병합을 진행할 수 없습니다.
```

**로그:**
```
INFO:pdfusion.level_config:[DEBUG] ❌ 필수 파일 누락: {missing_required}
INFO:pdfusion.config_v5:[DEBUG] ❌ 필수 파일 누락으로 병합 중단
```

### 🔍 원인 분석

1. **하드코딩된 필수 파일 규칙**
   ```python
   # level_config.py
   if book_number <= 60:
       required_patterns = [
           r'word\s*list',
           r'word\s*writing',  # 필수로 설정됨
           r'translation\s*sheet',
           r'unscramble\s*sheet',
           r'unit\s*test',
       ]
   ```

2. **None 반환으로 인한 강제 중단**
   ```python
   if missing_required:
       return []  # 빈 리스트 반환 → 병합 중단
   ```

3. **실제 상황과 규칙의 불일치**
   - Level 3에서는 Word Test가 필요할 수도 있음
   - Word Writing이 없어도 Word Test가 있으면 병합 가능해야 함

### 🛠️ 시도한 해결책

#### 시도 1: 필수 파일 검증을 선택적으로 만들기
```python
def get_files_for_level(..., skip_required_check: bool = False):
    if required_patterns and not skip_required_check:
        # 필수 파일 검증
```

**결과:** ⚠️ 부분적 해결 - 하지만 사용자 선택 기능이 없음

#### 시도 2: None 반환 후 사용자 선택 처리
```python
# level_config.py
if missing_required:
    return None  # None 반환하여 config_v5.py에서 처리

# config_v5.py
if filtered_pdfs is None:
    # 필수 검증 없이 필터링만 수행
    filtered_pdfs = self.level_config.get_files_for_level(..., skip_required_check=True)
    # 사용자에게 선택권 제공
```

**결과:** ✅ 성공! 사용자가 계속 진행할지 선택 가능

#### 시도 3: 선택적 필수 그룹 시스템 도입
```python
# Word Writing 또는 Word Test 중 하나만 있어도 OK
optional_required_groups = [
    [r'word\s*writing', r'word\s*test'],
]
```

**결과:** ✅ 성공! 둘 중 하나만 있어도 경고만 표시하고 계속 진행

### ✅ 최종 해결책

**구현 위치:** 
- `pdfusion/level_config.py`: 선택적 필수 그룹 검증 로직 추가
- `pdfusion/config_v5.py`: 사용자 선택 처리 로직 추가

```python
# level_config.py
optional_required_groups = [
    [r'word\s*writing', r'word\s*test'],  # 둘 중 하나만 있어도 OK
]

# 선택적 필수 그룹 검증
if optional_required_groups:
    for group in optional_required_groups:
        group_found = False
        for pattern in group:
            # 패턴 매칭 확인
            if found:
                group_found = True
                break
        if not group_found:
            logger.warning(f"선택적 필수 그룹 누락: {group} (경고만, 계속 진행)")

# config_v5.py
if filtered_pdfs is None:
    # 필수 검증 없이 필터링만 수행
    filtered_pdfs = self.level_config.get_files_for_level(..., skip_required_check=True)
    
    # 누락된 필수 파일 확인 및 사용자 선택
    if missing_required:
        print(f"  선택하세요:")
        print(f"    1. 누락된 파일 없이 계속 진행 (기본값)")
        print(f"    2. 병합 중단")
        choice = input("  선택 (1/2, 기본값: 1): ").strip()
```

### 📚 배운 점

- **유연한 검증 시스템의 중요성**: 모든 파일을 필수로 만들면 실제 상황에서 유연성이 떨어짐
- **사용자 선택권 제공**: 시스템이 강제로 중단하기보다는 사용자가 판단할 수 있도록
- **선택적 필수 그룹 개념**: "A 또는 B 중 하나" 같은 유연한 규칙이 필요함

---

## Issue #3: Word Test 파일이 압축 파일로 있어서 포함되지 않음

### 🔴 문제 상황

**증상:**
```
카테고리별 파일 목록:
  [Word List] (1개)
  [Translation Sheet] (1개)
  [Unit Test] (1개)
  [Unscramble Sheet] (1개)

=> Word Test가 포함되지 않았습니다.
```

**사용자 피드백:**
```
Bricks Reading 50 Nonfiction_L3_Word Test
이게 폴더 명인데 압축 해제되어있지 않았습니다.
```

**로그 분석:**
```
INFO:pdfusion.extractor:디렉토리에서 12개의 zip 파일 발견
내부 압축 파일 3개 발견 (자동 압축 해제):
  1. Bricks Reading 50 Nonfiction_L3_Translation Sheet.zip
  2. Bricks Reading 50 Nonfiction_L3_Unit Test.zip
  3. Bricks Reading 50 Nonfiction_L3_Unscramble Sheet.zip
```

- Word Test zip 파일이 발견되지 않음
- 내부 zip 필터링에서 Word Test가 제외됨

### 🔍 원인 분석

**문제 코드:**
```python
# config_v5.py - 내부 zip 필터링 로직
if book_number <= 60:
    target_patterns = [
        'word list', 
        'word writing',  # Word Writing은 포함
        'translation sheet', 
        'unscramble sheet', 
        'unit test'
        # Word Test가 누락됨!
    ]
```

**원인:**
- `level_config.py`에서는 Word Test를 포함 패턴에 추가했지만
- `config_v5.py`의 내부 zip 필터링 로직은 업데이트되지 않음
- 두 곳의 규칙이 동기화되지 않음

### 🛠️ 시도한 해결책

#### 시도 1: 로그 확인으로 문제 파악
```python
# level_config.py에 디버그 로그 추가
word_test_files = [f for f in all_files if 'test' in f.name.lower() and 'word' in f.name.lower()]
logger.info(f"[DEBUG] Word Test 관련 파일 발견: {len(word_test_files)}개")
```

**결과:** ⚠️ 파일 탐색 단계에서는 발견되지 않음 → 압축 해제가 안 된 것이 원인

#### 시도 2: 내부 zip 필터링 패턴 수정
```python
if book_number <= 60:
    target_patterns = [
        'word list', 
        'word writing', 
        'word test',  # 추가!
        'translation sheet', 
        'unscramble sheet', 
        'unit test'
    ]
```

**결과:** ✅ 성공! Word Test zip 파일이 발견되고 압축 해제됨

### ✅ 최종 해결책

**구현 위치:** `pdfusion/config_v5.py` - 내부 zip 필터링 로직

```python
if book_number <= 60:
    # 60 이하: Word List, Word Writing, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
    target_patterns = [
        'word list', 
        'word writing', 
        'word test',  # 추가됨
        'translation sheet', 
        'unscramble sheet', 
        'unit test',
        'wordlist', 
        'wordwriting', 
        'wordtest',  # 추가됨
        'translationsheet', 
        'unscramblesheet', 
        'unittest'
    ]
```

### 📚 배운 점

- **규칙 동기화의 중요성**: 여러 곳에서 같은 규칙을 사용할 때 일관성 유지 필요
- **단계별 검증**: 파일 필터링 로직과 압축 해제 로직이 같은 규칙을 사용하는지 확인
- **로그를 통한 문제 추적**: 각 단계에서 어떤 파일이 발견되는지 로그로 확인

---

## Issue #4: 정규표현식 패턴 매칭 실패

### 🔴 문제 상황

**증상:**
- Word Test A/B 파일 감지가 제대로 되지 않음
- 정규표현식 패턴이 너무 넓게 매칭되거나 너무 좁게 매칭됨

**터미널 테스트:**
```bash
python -c "import re; from pathlib import Path; f1 = Path('Bricks Reading 170 Nonfiction_L1_Word Test A.pdf'); pattern = r'\b[A-Z]\b'; print(bool(re.search(pattern, f1.stem, re.IGNORECASE)))"
```

**결과:** `True` (하지만 'T'도 매칭되어 원하는 결과가 아님)

### 🔍 원인 분석

**문제 패턴:**
```python
pattern = r'\b[A-Z]\b'  # 단어 경계 사이의 단일 알파벳
# "Word Test A"에서 'T'도 매칭됨
```

**원하는 동작:**
- 파일명 끝의 " A" 또는 " B"만 감지
- "Word Test"의 'T'는 감지하지 않음

### 🛠️ 시도한 해결책

#### 시도 1: 파일명 끝 패턴으로 수정
```python
pattern = r'[_\s]([A-Z])$'  # 파일명 끝의 단일 알파벳
```

**결과:** ✅ 성공! "Word Test A"에서 'A'만 정확히 매칭

**최종 구현:**
```python
def is_test_a(file_path: Path) -> bool:
    name = file_path.stem.lower()
    return bool(re.search(r'test\s*[_\s]a\b', name, re.IGNORECASE)) or \
           bool(re.search(r'[_\s]a\.pdf$', file_path.name, re.IGNORECASE))
```

### 📚 배운 점

- **정규표현식은 구체적으로**: 넓은 패턴보다는 정확한 패턴이 안전함
- **테스트를 통한 검증**: 실제 파일명으로 패턴을 테스트해보는 것이 중요
- **여러 패턴 조합**: 하나의 패턴으로 모든 경우를 커버하기 어려우면 여러 패턴 조합

---

## Issue #5: 변수 스코프 문제로 인한 NameError

### 🔴 문제 상황

**증상:**
```python
# level_config.py
if len(files) > 1:
    has_letter_suffix = any(...)  # 이 블록 안에서만 정의됨

# 나중에 사용하려고 하면
if has_letter_suffix:  # NameError: name 'has_letter_suffix' is not defined
```

### 🔍 원인 분석

- Python의 변수 스코프 규칙
- `if` 블록 안에서 정의된 변수는 해당 블록 밖에서 접근 불가
- `len(files) == 1`인 경우 `has_letter_suffix`가 정의되지 않음

### ✅ 최종 해결책

**구현:**
```python
# 함수 스코프에서 초기화
has_letter_suffix = False

if len(files) > 1:
    has_letter_suffix = any(has_letter_suffix_pattern(f) for f in files)
```

### 📚 배운 점

- **변수 초기화 위치**: 사용하기 전에 적절한 스코프에서 초기화
- **Python 스코프 규칙**: 블록 안에서 정의된 변수는 밖에서 접근 불가

---

## Issue #6: 로그에서 오타 발견 (실제 오류는 아님)

### 🔴 문제 상황

**로그:**
```
WARNING:pdfusion.level_config:[DEBUG]   ⚠️  선택적 필수 그룹 누락: ['word\\s*writting', 'word\\s*test']
```

- 로그에 `writting` (오타)이 표시됨
- 하지만 실제 코드에는 `writing` (정확한 철자)

### 🔍 원인 분석

- 로그 출력 시 정규표현식 패턴이 문자열로 변환되면서 표시됨
- 실제 코드에는 문제가 없었음
- 로그만 확인하면 오타로 보일 수 있음

### ✅ 해결책

- 실제 코드 확인 후 문제 없음을 확인
- 로그 출력 형식을 개선하여 더 명확하게 표시

### 📚 배운 점

- **로그와 실제 코드 구분**: 로그만 보고 판단하지 말고 실제 코드 확인
- **디버깅 시 전체 맥락 파악**: 한 부분만 보지 말고 전체 흐름 확인

---

## 종합 회고

### 가장 어려웠던 부분

1. **Word Test A/B 선택 질문이 나오지 않는 문제**
   - 여러 곳을 수정해도 해결되지 않아서 답답했음
   - 결국 별도 단계로 분리하는 것이 해결책이었음

2. **필수 파일 검증 로직의 유연성 확보**
   - 하드코딩된 규칙을 유연하게 만드는 것이 어려웠음
   - 선택적 필수 그룹 개념을 도입하여 해결

### 가장 효과적이었던 해결 방법

1. **단계별 분리**: 특수한 파일 타입을 별도 단계로 처리
2. **사용자 선택권 제공**: 시스템이 강제로 중단하기보다는 사용자가 판단
3. **규칙 동기화**: 여러 곳에서 사용하는 규칙을 일관되게 유지

### 앞으로 개선할 점

1. **설정 파일 기반 규칙 관리**: 하드코딩 대신 JSON/YAML 설정 파일 사용
2. **자동 테스트**: 각 단계별로 자동 테스트 추가
3. **더 상세한 로그**: 문제 발생 시 원인을 쉽게 파악할 수 있도록

---

**작성일:** 2025-01-13  
**버전:** PDFusion ver_5
