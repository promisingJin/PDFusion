# PDFusion 버전 가이드 (Version Guide)

## 📌 현재 상태 요약

**현재 작업 브랜치:** `ver4`  
**실제 사용 중인 버전:** `ver_5` (코드 내부)  
**최신 커밋:** 2026-01-11 (ver5 업데이트)

---

## 🔍 버전 구조 이해하기

### Git 브랜치 vs 코드 버전

이 프로젝트는 **Git 브랜치 이름**과 **코드 내부 버전**이 다릅니다:

| Git 브랜치 | 코드 버전 | 주요 파일 | 상태 |
|-----------|----------|----------|------|
| `ver2` | ver_2 | `config.py`, `__init__.py` | 구버전 (보관용) |
| `ver3` | ver_3 | `config.py`, `__init__.py` | 구버전 (보관용) |
| `ver4` (현재) | **ver_5** | `config_v5.py`, `__init__v5.py` | **현재 사용 중** |

**⚠️ 주의:** 현재 `ver4` 브랜치에 있지만, 실제로는 `ver_5` 코드를 사용하고 있습니다!

---

## 📂 파일별 버전 구분

### 메인 진입점

| 파일 | 사용 버전 | 설명 |
|------|----------|------|
| `main.py` | **ver_5** | 현재 ver_5 사용 (config_v5.py 호출) |
| `main_v5.py` | **ver_5** | main.py와 동일 (별칭) |

**실행 방법:**
```bash
# 둘 다 동일하게 ver_5 실행
python main.py
python main_v5.py
```

### 설정 관리 모듈

| 파일 | 버전 | 클래스 | 상태 |
|------|------|--------|------|
| `pdfusion/config.py` | ver_2/3/4 | `ConfigManager` | 구버전 (보관용) |
| `pdfusion/config_v5.py` | **ver_5** | `ConfigManagerV5` | **현재 사용 중** |

### 패키지 초기화

| 파일 | 버전 | Export 클래스 | 상태 |
|------|------|--------------|------|
| `pdfusion/__init__.py` | ver_2/3/4 | `ConfigManager` | 구버전 (보관용) |
| `pdfusion/__init__v5.py` | **ver_5** | `ConfigManagerV5` | **현재 사용 중** |

---

## 🔄 버전별 주요 차이점

### ver_2/3/4 (구버전)

**특징:**
- `ConfigManager` 클래스 사용
- `pdfusion/__init__.py`의 `main()` 함수 호출
- 수동 파일 선택 및 설정
- 압축 파일 처리 없음
- LC/RC 자동 감지 없음
- 레벨별 필터링 없음

**실행 방식:**
```python
# main.py (구버전)
from pdfusion import main
main()
```

**주요 파일:**
- `pdfusion/config.py` - 기본 설정 관리
- `pdfusion/__init__.py` - 패키지 초기화

---

### ver_5 (현재 버전) ⭐

**특징:**
- `ConfigManagerV5` 클래스 사용
- 직접 import 방식 (`from pdfusion.config_v5 import ConfigManagerV5`)
- **자동 압축 파일 처리** (zip 파일 자동 탐색 및 해제)
- **LC/RC 자동 감지** (Listening → LC, Reading → RC)
- **레벨 자동 감지** (Level 1, Level 2, _L1_, _L2_ 등)
- **레벨별 파일 자동 필터링** (책 타입과 번호에 따라)
- **Unit Test 선택 기능** (ALL vs 개별 Unit)
- **Word Test A/B 선택 기능**
- **필수 파일 누락 시 사용자 선택**
- **내부 zip 파일 처리** (책 폴더 내부의 zip도 자동 처리)

**실행 방식:**
```python
# main.py / main_v5.py (현재)
from pdfusion.config_v5 import ConfigManagerV5
from pdfusion.merger import PDFMerger

config_manager = ConfigManagerV5()
configs = config_manager.get_user_input()
# ... 병합 처리
```

**주요 파일:**
- `pdfusion/config_v5.py` - 고급 설정 관리
- `pdfusion/__init__v5.py` - 패키지 초기화 (ver_5)
- `pdfusion/book_type_detector.py` - LC/RC 감지
- `pdfusion/level_config.py` - 레벨별 규칙 관리
- `pdfusion/file_discovery.py` - 파일 탐색 및 분류
- `pdfusion/extractor.py` - zip 파일 처리

---

## 📊 버전별 기능 비교표

| 기능 | ver_2/3/4 | ver_5 |
|------|-----------|-------|
| **기본 PDF 병합** | ✅ | ✅ |
| **유닛별 병합** | ✅ | ✅ |
| **Review Test 처리** | ✅ | ✅ |
| **압축 파일 자동 처리** | ❌ | ✅ |
| **LC/RC 자동 감지** | ❌ | ✅ |
| **레벨 자동 감지** | ❌ | ✅ |
| **레벨별 파일 필터링** | ❌ | ✅ |
| **내부 zip 처리** | ❌ | ✅ |
| **Unit Test 선택** | ❌ | ✅ |
| **Word Test A/B 선택** | ❌ | ✅ |
| **필수 파일 검증** | ❌ | ✅ |
| **_Eng 파일 제외** | ❌ | ✅ |

---

## 🗂️ Git 히스토리 요약

### 커밋 타임라인

```
2025-07-12: Initial commit
2025-07-12: complete code
2025-07-13: ver2 브랜치 생성
2025-07-13: ver3 브랜치 생성 (ver2 병합)
2025-07-13: ver3 revert (일부 롤백)
2025-07-13: ver4 브랜치 생성 (PR #5)
2026-01-11: ver5 업데이트 (현재 HEAD)
```

### 주요 브랜치

- **`main`**: 메인 브랜치 (origin/main과 동기화)
- **`ver2`**: 두 번째 버전 (보관용)
- **`ver3`**: 세 번째 버전 (보관용)
- **`ver4`**: 네 번째 버전 (현재 작업 브랜치, 하지만 ver_5 코드 사용)

---

## 🎯 현재 사용 중인 버전 확인 방법

### 1. 실행 시 확인

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

### 2. 코드에서 확인

**`main.py` 또는 `main_v5.py` 파일 확인:**
```python
from pdfusion.config_v5 import ConfigManagerV5  # ← ver_5 사용
```

**`pdfusion/__init__.py` vs `pdfusion/__init__v5.py`:**
- `__init__.py`: `ConfigManager` (구버전)
- `__init__v5.py`: `ConfigManagerV5` (현재)

---

## 🔧 버전 전환 방법 (필요 시)

### ver_5 사용 (현재, 권장)

```bash
# 이미 ver_5 사용 중
python main_v5.py
# 또는
python main.py  # 둘 다 ver_5 사용
```

### 구버전 사용 (비권장, 테스트용)

구버전을 사용하려면:
1. `main.py`를 수정하여 `from pdfusion import main` 방식으로 변경
2. `pdfusion/__init__.py`의 `main()` 함수 사용
3. `ConfigManager` 클래스 사용

**⚠️ 주의:** 구버전은 많은 기능이 없으므로 권장하지 않습니다.

---

## 📝 버전별 파일 구조

### ver_2/3/4 구조
```
pdfusion/
├── __init__.py          # ConfigManager export
├── config.py            # ConfigManager 클래스
└── merger.py            # PDFMerger 클래스
```

### ver_5 구조 (현재)
```
pdfusion/
├── __init__.py          # 구버전 (보관용)
├── __init__v5.py        # ver_5 (현재)
├── config.py            # 구버전 (보관용)
├── config_v5.py         # ver_5 (현재) ⭐
├── merger.py            # PDFMerger (공통)
├── book_type_detector.py    # ver_5 전용
├── level_config.py          # ver_5 전용
├── file_discovery.py         # ver_5 전용
└── extractor.py              # ver_5 전용
```

---

## ❓ 자주 묻는 질문 (FAQ)

### Q1: 왜 브랜치 이름이 ver4인데 코드는 ver_5인가요?

**A:** Git 브랜치 이름(`ver4`)과 코드 내부 버전(`ver_5`)은 별개입니다. 
- Git 브랜치: 프로젝트 관리용
- 코드 버전: 실제 기능 버전

현재 `ver4` 브랜치에 있지만, 코드는 `ver_5` 기능을 사용하고 있습니다.

### Q2: main.py와 main_v5.py의 차이는?

**A:** 현재는 **차이가 없습니다**. 둘 다 `ver_5`를 사용합니다.
- `main.py`: 원래 구버전용이었지만 ver_5로 업데이트됨
- `main_v5.py`: ver_5 전용으로 명시적으로 만든 파일

### Q3: config.py와 config_v5.py를 모두 사용할 수 있나요?

**A:** 아니요. 현재는 **`config_v5.py`만 사용**합니다.
- `config.py`: 구버전 (보관용)
- `config_v5.py`: 현재 버전 (실제 사용)

### Q4: 어떤 파일을 실행해야 하나요?

**A:** 다음 중 아무거나 실행하면 됩니다:
```bash
python main.py
# 또는
python main_v5.py
```

둘 다 동일하게 `ver_5`를 실행합니다.

### Q5: 구버전으로 돌아가고 싶어요

**A:** 가능하지만 권장하지 않습니다. 구버전은 많은 기능이 없습니다:
- 압축 파일 자동 처리 없음
- LC/RC 자동 감지 없음
- 레벨별 필터링 없음

필요하다면 Git으로 이전 커밋을 체크아웃하세요:
```bash
git checkout <이전 커밋 해시>
```

---

## 🎯 결론

### 현재 상태
- **실제 사용 버전:** `ver_5` ⭐
- **Git 브랜치:** `ver4`
- **실행 파일:** `main.py` 또는 `main_v5.py` (둘 다 동일)
- **설정 모듈:** `config_v5.py`

### 권장 사항
1. **항상 `main_v5.py` 또는 `main.py` 실행** (둘 다 ver_5)
2. **`config_v5.py` 사용** (현재 버전)
3. **구버전 파일(`config.py`, `__init__.py`)은 수정하지 않기** (보관용)

---

**작성일:** 2025-01-13  
**최종 업데이트:** 2025-01-13  
**문서 버전:** 1.0
