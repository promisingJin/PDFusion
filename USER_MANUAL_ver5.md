# PDFusion ver_5 사용자 매뉴얼

## 📌 빠른 시작 가이드

### 실행 명령어

```bash
# 방법 1: main_v5.py 직접 실행 (권장)
python main_v5.py

# 방법 2: main.py 실행 (ver_5로 자동 전환)
python main.py
```

### 실행 위치

프로젝트 루트 디렉토리에서 실행:
```bash
cd C:\Users\PC\PycharmProjects\PDFusion
python main_v5.py
```

---

## 🎯 오늘 구현 완료된 기능 목록

### ✅ 핵심 기능

1. **자동 압축 파일 처리**
   - 최상위 폴더의 zip 파일 자동 탐색 및 압축 해제
   - 내부 zip 파일(책 폴더 내부) 자동 탐색 및 압축 해제
   - `_Eng` 파일 자동 제외

2. **LC/RC 자동 감지**
   - 폴더명에서 "Listening" 또는 "Reading" 자동 감지
   - LC (Listening Comprehension) / RC (Reading Comprehension) 자동 분류

3. **레벨 자동 감지**
   - "Level 1", "Level 2", "Level 3" 등 자동 감지
   - "_L1_", "_L2_" 등 파일명 패턴도 인식

4. **레벨별 파일 자동 필터링**
   - 책 타입(LC/RC)과 책 번호에 따라 필요한 파일만 자동 포함
   - 필수 파일 누락 시 사용자 선택 기능

5. **Unit Test 파일 선택**
   - ALL 파일 vs 개별 Unit 파일 선택 옵션
   - `_Eng` 폴더 자동 제외

6. **Word Test A/B 선택**
   - Word Test A와 B가 모두 있을 때 선택 옵션
   - A만, B만, 또는 둘 다 사용 가능

7. **유닛별 PDF 자동 병합**
   - 각 유닛별로 PDF 파일 자동 병합
   - 전체 합본 PDF 자동 생성

---

## 📋 실행 순서 및 사용법

### 1단계: 프로그램 실행

```bash
python main_v5.py
```

**출력 예시:**
```
============================================================
PDFusion - 유닛별 PDF 자동 병합 도구 (ver_5)
============================================================
[확인] config_v5.py 사용 중
```

### 2단계: 최상위 폴더 경로 입력

```
최상위 폴더 경로를 입력하세요: C:\Users\PC\downloads
```

**주의사항:**
- 전체 경로를 입력하세요 (상대 경로도 가능)
- 폴더 경로에 공백이 있어도 됩니다
- 경로 끝에 `\` 또는 `/`는 생략 가능합니다

### 3단계: 압축 파일 처리 (있을 경우)

**시나리오 A: 압축 파일이 있는 경우**
```
압축 파일 3개 발견:
  1. Bricks Reading 50 Nonfiction Level 1.zip
  2. Bricks Reading 60 Level 1.zip
  3. Bricks Reading 80 Level 1.zip

압축 해제할 파일을 선택하세요:
  - 'all' 또는 Enter: 모두 압축 해제
  - 번호 입력 (예: 1,3): 선택한 파일만 압축 해제
  - 'skip': 압축 해제 건너뛰기
선택: all
```

**시나리오 B: 압축 파일이 없는 경우**
- 이 단계는 자동으로 건너뜁니다

### 4단계: 책 폴더 선택

```
책 폴더 5개 발견:
  1. Bricks Reading 50 Nonfiction Level 1
  2. Bricks Reading 50 Nonfiction Level 3
  3. Bricks Reading 60 Level 1
  4. Bricks Reading 80 Level 1
  5. Bricks Reading 170 Nonfiction Level 1

처리할 책을 선택하세요 (번호 입력, 여러 개는 쉼표로 구분, Enter=전체):
```

**입력 예시:**
- `1` → 첫 번째 책만 처리
- `1,3,5` → 1, 3, 5번 책 처리
- `Enter` → 모든 책 처리

### 5단계: LC/RC 자동 감지

```
[3-1단계] LC/RC 감지
✅ 책 타입 감지: RC (방법: path)
```

**자동 처리:**
- 폴더명에 "Reading"이 있으면 → RC
- 폴더명에 "Listening"이 있으면 → LC
- 사용자 입력 불필요

### 6단계: 레벨 자동 감지

```
[3-2단계] 레벨 감지
✅ 레벨 감지: Level 3
```

**자동 처리:**
- "Level 1", "Level 2", "Level 3" 등 자동 감지
- 사용자 입력 불필요

### 7단계: 내부 압축 파일 처리 (있을 경우)

```
[3-2.5단계] 내부 압축 파일 처리
내부 압축 파일 3개 발견 (자동 압축 해제):
  1. Bricks Reading 50 Nonfiction_L3_Translation Sheet.zip
  2. Bricks Reading 50 Nonfiction_L3_Unit Test.zip
  3. Bricks Reading 50 Nonfiction_L3_Word Test.zip
  ✅ 압축 해제 완료
```

**자동 처리:**
- 책 타입과 책 번호에 따라 필요한 zip 파일만 자동 압축 해제
- `_Eng` zip 파일은 자동 제외
- 사용자 입력 불필요

### 8단계: Unit Test 파일 선택 (있을 경우)

```
[3-3.5단계] Unit Test 파일 처리
  [Unit Test] ALL 파일과 개별 Unit 파일이 모두 발견되었습니다:
    - ALL 파일: 1개
      • Bricks Reading 50 Nonfiction_L3_Unit Test_ALL.pdf
    - 개별 Unit 파일: 16개
      (Unit 1~16)

  사용할 파일을 선택하세요:
    1. ALL 파일 사용 (통합 파일로 처리)
    2. 개별 Unit 파일 사용 (유닛별 파일로 처리)
  선택 (1/2, 기본값: 2): 1
```

**선택 옵션:**
- `1` 또는 `Enter` → ALL 파일 사용 (한 파일에 모든 유닛 포함)
- `2` → 개별 Unit 파일 사용 (각 파일이 하나의 유닛)

### 9단계: Word Test A/B 선택 (있을 경우)

```
[3-3.6단계] Word Test 파일 처리
  [Word Test] A 타입과 B 타입이 모두 발견되었습니다:
    - A 타입: 1개
      • Bricks Reading 170 Nonfiction_L1_Word Test A.pdf
    - B 타입: 1개
      • Bricks Reading 170 Nonfiction_L1_Word Test B.pdf

  사용할 Word Test 타입을 선택하세요:
    1. Test A만 사용
    2. Test B만 사용
    3. 둘 다 사용 (기본값)
  선택 (1/2/3, 기본값: 3): 3
```

**선택 옵션:**
- `1` → Test A만 사용
- `2` → Test B만 사용
- `3` 또는 `Enter` → 둘 다 사용

### 10단계: 필수 파일 누락 시 선택 (있을 경우)

```
⚠️  [경고] 필수 파일이 누락되었습니다!
   누락된 파일 패턴: word\s*writing
   현재 필터링된 파일 목록:
     - Bricks Reading 50 Nonfiction_L3_Word List.pdf
     - Bricks Reading 50 Nonfiction_L3_Translation Sheet.pdf
     - Bricks Reading 50 Nonfiction_L3_Unscramble Sheet.pdf
     - Bricks Reading 50 Nonfiction_L3_Unit Test_ALL.pdf

  선택하세요:
    1. 누락된 파일 없이 계속 진행 (기본값)
    2. 병합 중단
  선택 (1/2, 기본값: 1): 1
```

**선택 옵션:**
- `1` 또는 `Enter` → 누락된 파일 없이 계속 진행
- `2` → 병합 중단

### 11단계: 파일 목록 확인

```
[3-4단계] 파일 목록 확인

카테고리별 파일 목록:

  [Word List] (1개)
    1. Bricks Reading 50 Nonfiction_L3_Word List.pdf

  [Word Test] (1개)
    1. Bricks Reading 50 Nonfiction_L3_Word Test\Bricks Reading 50 Nonfiction_L3_Word Test.pdf

  [Translation Sheet] (1개)
    1. Bricks Reading 50 Nonfiction_L3_Translation Sheet\Bricks Reading 50 Nonfiction_L3_Translation Sheet.pdf

  [Unit Test] (1개)
    1. Bricks Reading 50 Nonfiction_L3_Unit Test\Bricks Reading 50 Nonfiction_L3_Unit Test_ALL.pdf

  [Unscramble Sheet] (1개)
    1. Bricks Reading 50 Nonfiction_L3_Unscramble Sheet\Bricks Reading 50 Nonfiction_L3_Unscramble Sheet.pdf

이대로 병합할까요? (y/n, 기본값: y): y
```

**선택 옵션:**
- `y` 또는 `Enter` → 병합 진행
- `n` → 병합 중단

### 12단계: 병합 순서 설정

```
[3-6단계] 병합 순서 설정

카테고리 목록:
  1. Word List
  2. Word Test
  3. Translation Sheet
  4. Unit Test
  5. Unscramble Sheet

병합 순서를 입력하세요 (예: 1,2,3,4,5 또는 Enter=자동순서): Enter
```

**입력 예시:**
- `Enter` → 자동 순서 사용
- `1,2,3,4,5` → 지정한 순서로 병합
- `5,4,3,2,1` → 역순으로 병합

### 13단계: 병합 실행

```
[책: Bricks Reading 50 Nonfiction Level 3] 병합 시작
책 타입: RC
레벨: Level 3
============================================================

총 16개 유닛 병합을 시작합니다...
진행 중: 16/16 (100.0%)

============================================================
병합 작업 완료!
============================================================
✅ 성공: 16/16 유닛
📄 총 병합된 페이지: 480페이지
```

**자동 처리:**
- 각 유닛별 PDF 자동 생성
- 전체 합본 PDF (`AllUnits.pdf`) 자동 생성

### 14단계: 결과 확인

**출력 위치:**
```
output/
└── Bricks Reading 50 Nonfiction Level 3/
    ├── Unit01.pdf
    ├── Unit02.pdf
    ├── Unit03.pdf
    ...
    ├── Unit16.pdf
    └── AllUnits.pdf
```

---

## ⚠️ 주의해야 할 사항

### 1. 경로 입력 시 주의사항

**✅ 올바른 예:**
```
C:\Users\PC\downloads
C:/Users/PC/downloads
downloads
```

**❌ 잘못된 예:**
```
C:\Users\PC\downloads\  (끝에 \ 있음)
"C:\Users\PC\downloads"  (따옴표 포함)
```

### 2. 압축 파일 처리

- **최상위 폴더의 zip 파일**: 사용자가 선택하여 압축 해제
- **내부 zip 파일**: 자동으로 압축 해제 (선택 불가)
- **`_Eng` zip 파일**: 자동으로 제외됨

### 3. 필수 파일 누락 시

- 필수 파일이 없어도 사용자가 계속 진행할 수 있음
- 하지만 병합 결과에 해당 파일이 포함되지 않음
- 가능하면 필요한 파일을 모두 준비하는 것이 좋음

### 4. Word Test A/B 선택

- A와 B가 모두 있을 때만 선택 질문이 나옴
- 하나만 있으면 자동으로 사용됨
- 둘 다 사용하면 각각의 유닛이 모두 포함됨

### 5. Unit Test 선택

- ALL 파일: 한 파일에 모든 유닛이 포함된 경우
- 개별 Unit 파일: 각 파일이 하나의 유닛인 경우
- 둘 다 있으면 사용자가 선택해야 함

### 6. 파일명 규칙

**자동 인식되는 파일 타입:**
- Word List
- Word Test
- Word Writing
- Translation Sheet
- Unscramble Sheet
- Unit Test
- Grammar Sheet

**제외되는 파일:**
- Answer, 답지, 정답이 포함된 파일
- `_Eng` 폴더의 파일
- Review Test (별도 처리)

### 7. 책 번호별 파일 규칙

**RC 타입, 책 번호 ≤ 60:**
- 포함: Word List, Word Writing, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
- 필수: Word List, Translation Sheet, Unscramble Sheet, Unit Test
- 선택적: Word Writing 또는 Word Test (둘 중 하나만 있어도 OK)

**RC 타입, 책 번호 61-79:**
- 포함: Word List, Word Test, Translation Sheet, Unscramble Sheet
- 모두 필수

**RC 타입, 책 번호 80-99:**
- 포함: Word List, Word Test, Translation Sheet, Unscramble Sheet, Unit Test
- 모두 필수

**RC 타입, 책 번호 ≥ 100:**
- 포함: Word List, Word Test, Translation Sheet, Unscramble Sheet, Grammar Sheet, Unit Test
- 모두 필수

**LC 타입:**
- 포함: Word List, Word Test
- 모두 필수

### 8. 출력 폴더

- 모든 결과는 `output/` 폴더에 저장됨
- 책 제목별로 하위 폴더가 자동 생성됨
- 기존 파일이 있으면 덮어쓰기됨

### 9. 에러 발생 시

**일반적인 에러:**
- 파일 경로 오류 → 경로를 다시 확인하세요
- PDF 읽기 오류 → PDF 파일이 손상되었는지 확인하세요
- 필수 파일 누락 → 파일을 준비하거나 계속 진행을 선택하세요

**로그 확인:**
- 프로그램 실행 시 로그가 콘솔에 출력됨
- 문제 발생 시 로그를 확인하여 원인 파악

### 10. 여러 책 처리 시

- 한 번에 여러 책을 선택하여 처리 가능
- 각 책마다 위의 단계가 반복됨
- 각 책의 결과는 별도 폴더에 저장됨

---

## 🔧 문제 해결 가이드

### Q1: "압축 파일이 발견되지 않습니다"

**원인:**
- 최상위 폴더에 zip 파일이 없음
- 또는 이미 압축 해제되어 있음

**해결:**
- 압축 파일이 이미 해제되어 있으면 그대로 진행
- 압축 파일이 필요하면 준비 후 다시 실행

### Q2: "필수 파일이 누락되었습니다"

**원인:**
- 필요한 파일이 폴더에 없음
- 또는 파일명이 규칙과 다름

**해결:**
- 필요한 파일을 준비하거나
- "1. 누락된 파일 없이 계속 진행" 선택

### Q3: "Word Test가 포함되지 않았습니다"

**원인:**
- Word Test 파일이 zip 파일로만 존재
- 내부 zip 필터링에서 제외됨

**해결:**
- Word Test zip 파일이 있는지 확인
- 있다면 자동으로 압축 해제되어야 함
- 여전히 문제가 있으면 로그 확인

### Q4: "병합 순서를 설정할 수 없습니다"

**원인:**
- 카테고리가 1개만 있음
- 또는 파일이 제대로 분류되지 않음

**해결:**
- 카테고리가 1개면 자동으로 처리됨
- 여러 카테고리가 있으면 순서 입력 가능

### Q5: "유닛이 감지되지 않습니다"

**원인:**
- PDF 파일에 유닛 정보가 없음
- 또는 PDF가 이미지로만 구성됨

**해결:**
- 수동으로 유닛 수 입력
- 또는 PDF 파일 확인

---

## 📝 실행 예시 (전체 흐름)

```bash
# 1. 프로그램 실행
python main_v5.py

# 2. 최상위 폴더 입력
최상위 폴더 경로를 입력하세요: C:\Users\PC\downloads

# 3. 압축 파일 선택 (있을 경우)
압축 파일 2개 발견:
  1. Bricks Reading 50 Nonfiction Level 1.zip
  2. Bricks Reading 50 Nonfiction Level 3.zip
선택: all

# 4. 책 폴더 선택
책 폴더 2개 발견:
  1. Bricks Reading 50 Nonfiction Level 1
  2. Bricks Reading 50 Nonfiction Level 3
처리할 책을 선택하세요: 2

# 5-13. 자동 처리 및 사용자 선택
[자동 처리 단계들...]

# 14. 결과 확인
output/Bricks Reading 50 Nonfiction Level 3/
  ├── Unit01.pdf
  ├── Unit02.pdf
  ...
  └── AllUnits.pdf
```

---

## 📚 추가 정보

### 지원하는 파일 형식
- PDF 파일만 지원
- ZIP 파일은 자동으로 압축 해제

### 시스템 요구사항
- Python 3.7 이상
- pypdf 라이브러리

### 버전 정보
- 현재 버전: ver_5 (3.0.0)
- 주요 변경사항: 자동화 강화, 유연한 파일 처리

---

**작성일:** 2025-01-13  
**버전:** PDFusion ver_5  
**작성자:** 개발팀
