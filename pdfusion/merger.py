"""
PDF 병합 핵심 기능을 담당하는 모듈
"""

import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import traceback
from datetime import datetime

# PyPDF2 버전 호환성 처리
try:
    from pypdf import PdfReader, PdfWriter  # 최신 버전
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter  # 구 버전
    except ImportError:
        raise ImportError("pypdf 또는 PyPDF2 라이브러리가 설치되어 있지 않습니다. pip install pypdf")

logger = logging.getLogger(__name__)


class PDFMerger:
    """PDF 병합 클래스"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.merge_log = []
        self.stats = {
            "total_files_processed": 0,
            "total_pages_merged": 0,
            "errors": 0,
            "warnings": 0
        }
        
        logger.info(f"PDFMerger 초기화 완료")
        logger.debug(f"출력 디렉토리: {self.output_dir.absolute()}")
        
    def validate_pdf_files(self, config: Dict) -> bool:
        """PDF 파일들의 존재 여부 및 페이지 수 검증"""
        logger.info("PDF 파일 검증 시작")
        validation_errors = []
        validation_warnings = []
        
        # 카테고리 PDF 파일 확인
        for category, info in config["categories"].items():
            pdf_path = info["pdf_path"]
            logger.debug(f"카테고리 '{category}' 파일 확인: {pdf_path}")
            
            if not os.path.exists(pdf_path):
                validation_errors.append(f"카테고리 '{category}': 파일을 찾을 수 없음 - {pdf_path}")
                logger.warning(f"파일 없음: {pdf_path}")
            else:
                # 파일이 존재하는 경우 페이지 수도 확인
                try:
                    reader = PdfReader(pdf_path)
                    total_pages = len(reader.pages)
                    pages_per_unit = info["pages_per_unit"]
                    max_units = total_pages // pages_per_unit
                    
                    logger.debug(f"  - 총 페이지: {total_pages}, 유닛당 페이지: {pages_per_unit}, 최대 유닛: {max_units}")
                    
                    if max_units < config["total_units"]:
                        warning_msg = f"카테고리 '{category}': 최대 {max_units}개 유닛만 가능 (요청: {config['total_units']}개)"
                        validation_warnings.append(warning_msg)
                        logger.warning(f"  - 경고: {warning_msg}")
                        
                except Exception as e:
                    error_msg = f"카테고리 '{category}': PDF 읽기 오류 - {str(e)}"
                    validation_errors.append(error_msg)
                    logger.error(f"파일 읽기 오류 ({pdf_path}): {e}")
        
        # Review Test PDF 파일 확인 (리스트 구조)
        for review in config.get("review_tests", []):
            review_path = review["pdf_path"]
            logger.debug(f"Review Test 파일 확인: {review_path}")
            if not review_path:
                validation_errors.append("Review Test: 파일 경로가 지정되지 않음")
            elif not os.path.exists(review_path):
                validation_errors.append(f"Review Test: 파일을 찾을 수 없음 - {review_path}")
                logger.warning(f"Review Test 파일 없음: {review_path}")
            else:
                try:
                    reader = PdfReader(review_path)
                    total_pages = len(reader.pages)
                    pages_per_unit = review["pages_per_unit"]
                    max_units = total_pages // pages_per_unit
                    logger.debug(f"  - Review Test 총 페이지: {total_pages}, 유닛당 페이지: {pages_per_unit}, 최대 유닛: {max_units}")
                    for unit in review["units"]:
                        if unit > max_units:
                            warning_msg = f"Review Test: Unit {unit}는 최대 범위({max_units}) 초과"
                            validation_warnings.append(warning_msg)
                            logger.warning(warning_msg)
                except Exception as e:
                    error_msg = f"Review Test: PDF 읽기 오류 - {str(e)}"
                    validation_errors.append(error_msg)
                    logger.error(f"Review Test 파일 읽기 오류: {e}")
        
        # 검증 결과 출력
        if validation_errors:
            logger.error("PDF 파일 검증 실패:")
            print("\n[오류] 다음 문제들을 해결해주세요:")
            for error in validation_errors:
                logger.error(f"  - {error}")
                print(f"  ❌ {error}")
            self.stats["errors"] += len(validation_errors)
        
        if validation_warnings:
            logger.warning("PDF 파일 검증 경고:")
            print("\n[경고] 다음 사항들을 확인해주세요:")
            for warning in validation_warnings:
                logger.warning(f"  - {warning}")
                print(f"  ⚠️  {warning}")
            self.stats["warnings"] += len(validation_warnings)
        
        if not validation_errors:
            logger.info("모든 PDF 파일 검증 완료 - 오류 없음")
            if not validation_warnings:
                print("✅ 모든 PDF 파일이 정상적으로 확인되었습니다.")
            return True
        
        return False
    
    def calculate_page_range(self, unit_number: int, pages_per_unit: int) -> Tuple[int, int]:
        """
        특정 유닛의 페이지 범위 계산
        
        Args:
            unit_number: 유닛 번호 (사람 기준: 1, 2, 3, ...)
            pages_per_unit: 유닛당 페이지 수
            
        Returns:
            (start_index, end_index): PyPDF2 라이브러리용 0-based 인덱스
        """
        # 사람 기준 Unit 번호를 0-based 인덱스로 변환
        start_index = (unit_number - 1) * pages_per_unit
        end_index = start_index + pages_per_unit
        
        logger.debug(f"Unit{unit_number} 페이지 범위 계산: "
                    f"사람기준 {start_index + 1}~{end_index}페이지 → "
                    f"인덱스 [{start_index}:{end_index})")
        
        return start_index, end_index
    
    def extract_unit_pages(self, pdf_path: str, unit_number: int, pages_per_unit: int) -> Optional[List]:
        """
        PDF에서 특정 유닛의 페이지들 추출
        
        Args:
            pdf_path: PDF 파일 경로
            unit_number: 유닛 번호 (사람 기준: 1, 2, 3, ...)
            pages_per_unit: 유닛당 페이지 수
            
        Returns:
            추출된 페이지 객체 리스트 (실패시 None)
        """
        logger.debug(f"페이지 추출 시작: {pdf_path}, Unit{unit_number}, {pages_per_unit}페이지/유닛")
        
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            logger.debug(f"PDF 총 페이지 수: {total_pages}")
            
            # 0-based 인덱스 계산
            start_index, end_index = self.calculate_page_range(unit_number, pages_per_unit)
            
            # 페이지 범위 검증
            if start_index >= total_pages:
                error_msg = (f"페이지 범위 초과: {os.path.basename(pdf_path)}에서 Unit{unit_number} "
                           f"시작 페이지({start_index+1})가 총 페이지({total_pages})를 초과")
                logger.error(error_msg)
                self.merge_log.append(f"오류: {error_msg}")
                self.stats["errors"] += 1
                return None
            
            if end_index > total_pages:
                # 부분적으로 페이지가 있는 경우
                available_pages = total_pages - start_index
                warning_msg = (f"페이지 부족: {os.path.basename(pdf_path)}에서 Unit{unit_number} "
                             f"({available_pages}/{pages_per_unit}페이지만 사용 가능)")
                logger.warning(warning_msg)
                self.merge_log.append(f"경고: {warning_msg}")
                self.stats["warnings"] += 1
                end_index = total_pages
            
            # 페이지 추출 (0-based 인덱스 사용)
            pages = []
            for page_index in range(start_index, end_index):
                logger.debug(f"페이지 추출 중: 인덱스 {page_index} (사람기준 {page_index+1}페이지)")
                pages.append(reader.pages[page_index])
            
            logger.info(f"    {os.path.basename(pdf_path)} Unit{unit_number}: "
                       f"{start_index+1}~{end_index}페이지 추출 완료 ({len(pages)}페이지)")
            return pages
            
        except Exception as e:
            error_msg = f"Unit{unit_number} 추출 실패: {str(e)}"
            logger.error(f"{pdf_path}에서 {error_msg}")
            logger.debug(f"상세 오류: {traceback.format_exc()}")
            self.merge_log.append(f"오류: {os.path.basename(pdf_path)}에서 {error_msg}")
            self.stats["errors"] += 1
            return None
    
    def merge_unit_pdf(self, unit_number: int, config: Dict) -> bool:
        """특정 유닛의 PDF 병합"""
        writer = PdfWriter()
        unit_name = f"Unit{unit_number:02d}"
        
        logger.info(f"\n=== {unit_name} 병합 시작 ===")
        logger.debug(f"병합 순서: {config['merge_order']}")
        
        total_pages_added = 0
        unit_success = True
        
        # 병합 순서에 따라 각 카테고리의 페이지 추가
        for i, category in enumerate(config["merge_order"], 1):
            logger.debug(f"[{i}/{len(config['merge_order'])}] 카테고리 '{category}' 처리 중...")
            
            if category not in config["categories"]:
                warning_msg = f"카테고리 '{category}'를 찾을 수 없음"
                logger.warning(warning_msg)
                self.merge_log.append(f"경고: {warning_msg}")
                self.stats["warnings"] += 1
                continue
            
            category_info = config["categories"][category]
            pdf_path = category_info["pdf_path"]
            pages_per_unit = category_info["pages_per_unit"]
            
            logger.debug(f"  - PDF 경로: {pdf_path}")
            logger.debug(f"  - 유닛당 페이지: {pages_per_unit}")
            
            pages = self.extract_unit_pages(pdf_path, unit_number, pages_per_unit)
            if pages:
                for j, page in enumerate(pages, 1):
                    writer.add_page(page)
                    logger.debug(f"    페이지 {j}/{len(pages)} 추가됨")
                
                total_pages_added += len(pages)
                logger.info(f"  - {category}: {len(pages)}페이지 추가 (누적: {total_pages_added}페이지)")
            else:
                warning_msg = f"{unit_name}에서 {category} 추출 실패"
                logger.warning(warning_msg)
                self.merge_log.append(f"경고: {warning_msg}")
                unit_success = False
        
        # Review Test 추가 (각 구간의 마지막 유닛에만 전체 PDF 추가)
        for review in config.get("review_tests", []):
            last_unit = max(review["units"])
            if unit_number == last_unit:
                logger.debug(f"Review Test 전체 추가 - Unit{unit_number}")
                try:
                    reader = PdfReader(review["pdf_path"])
                    for j, page in enumerate(reader.pages, 1):
                        writer.add_page(page)
                        logger.debug(f"    Review Test 페이지 {j}/{len(reader.pages)} 추가됨")
                    total_pages_added += len(reader.pages)
                    logger.info(f"  - Review Test: {len(reader.pages)}페이지 전체 추가 (누적: {total_pages_added}페이지)")
                except Exception as e:
                    warning_msg = f"{unit_name}에서 Review Test 전체 추가 실패: {e}"
                    logger.warning(warning_msg)
                    self.merge_log.append(f"경고: {warning_msg}")
                    unit_success = False
        
        # 페이지가 추가되지 않은 경우 처리
        if total_pages_added == 0:
            error_msg = f"{unit_name}: 추가된 페이지가 없음"
            logger.error(error_msg)
            self.merge_log.append(f"오류: {error_msg}")
            self.stats["errors"] += 1
            return False
        
        # 병합된 PDF 저장
        output_path = self.output_dir / f"{unit_name}.pdf"
        logger.debug(f"최종 저장 경로: {output_path.absolute()}")
        logger.debug(f"최종 페이지 수: {total_pages_added}")
        
        try:
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # 저장된 파일 크기 확인
            file_size = output_path.stat().st_size
            logger.debug(f"저장된 파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            logger.info(f"✅ {unit_name}.pdf 저장 완료 ({total_pages_added}페이지)")
            
            self.stats["total_pages_merged"] += total_pages_added
            self.stats["total_files_processed"] += 1
            
            return unit_success
            
        except Exception as e:
            error_msg = f"{unit_name}.pdf 저장 실패: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"상세 오류: {traceback.format_exc()}")
            self.merge_log.append(f"오류: {error_msg}")
            self.stats["errors"] += 1
            return False
    
    def merge_all_units(self, config: Dict) -> bool:
        """모든 유닛 병합 실행"""
        logger.info("="*60)
        logger.info("PDF 병합 작업 시작")
        logger.info("="*60)
        
        logger.debug(f"총 유닛 수: {config['total_units']}")
        logger.debug(f"카테고리 수: {len(config['categories'])}")
        # Review Test 활성화 로그 부분 수정
        logger.debug(f"Review Test 구간 수: {len(config.get('review_tests', []))}")
        
        if not self.validate_pdf_files(config):
            logger.error("PDF 파일 검증 실패 - 병합 작업 중단")
            print("\n병합 작업을 중단합니다. 위의 오류를 해결한 후 다시 시도해주세요.")
            return False
        
        success_count = 0
        total_units = config["total_units"]
        
        print(f"\n총 {total_units}개 유닛 병합을 시작합니다...")
        logger.info(f"총 {total_units}개 유닛 병합 시작...")
        
        for unit_number in range(1, total_units + 1):
            progress = unit_number / total_units * 100
            print(f"\r진행 중: {unit_number}/{total_units} ({progress:.1f}%)", end='', flush=True)
            logger.debug(f"\n진행상황: {unit_number}/{total_units} ({progress:.1f}%)")
            
            if self.merge_unit_pdf(unit_number, config):
                success_count += 1
                logger.debug(f"Unit{unit_number:02d} 성공 (성공률: {success_count}/{unit_number})")
            else:
                logger.error(f"Unit{unit_number:02d} 실패")
        
        print()  # 진행률 표시 후 줄바꿈
        
        # 최종 통계
        logger.info("="*60)
        logger.info(f"병합 작업 완료: {success_count}/{total_units} 유닛 성공")
        
        print(f"\n{'='*60}")
        print(f"병합 작업 완료!")
        print(f"{'='*60}")
        print(f"✅ 성공: {success_count}/{total_units} 유닛")
        print(f"📄 총 병합된 페이지: {self.stats['total_pages_merged']:,}페이지")
        print(f"📁 생성된 파일: {self.stats['total_files_processed']}개")
        
        if success_count < total_units:
            failed_count = total_units - success_count
            logger.warning(f"실패한 유닛: {failed_count}개")
            print(f"❌ 실패: {failed_count}개")
        
        if self.stats["warnings"] > 0:
            print(f"⚠️  경고: {self.stats['warnings']}개")
        
        if self.stats["errors"] > 0:
            print(f"❌ 오류: {self.stats['errors']}개")
        
        print(f"{'='*60}")
        
        # 로그 파일 저장
        self.save_merge_log()
        
        return success_count == total_units
    
    def merge_all_units_to_one(self, total_units: int, output_filename: str = "AllUnits.pdf"):
        """output_dir 내 UnitXX.pdf를 순서대로 하나로 합쳐 output_filename으로 저장"""
        from pypdf import PdfReader, PdfWriter
        writer = PdfWriter()
        unit_files = [self.output_dir / f"Unit{num:02d}.pdf" for num in range(1, total_units+1)]
        for unit_file in unit_files:
            if not unit_file.exists():
                logger.warning(f"{unit_file} 파일이 존재하지 않아 건너뜀")
                continue
            reader = PdfReader(str(unit_file))
            for page in reader.pages:
                writer.add_page(page)
        output_path = self.output_dir / output_filename
        with open(output_path, 'wb') as f:
            writer.write(f)
        logger.info(f"✅ 전체 합본 PDF 저장 완료: {output_path}")
        print(f"\n[완료] 전체 합본 PDF가 저장되었습니다: {output_path}")
    
    def save_merge_log(self):
        """병합 로그를 파일로 저장"""
        log_path = self.output_dir / f"merge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        logger.info(f"병합 보고서 저장 중: {log_path}")
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("PDF 병합 작업 보고서\n")
                f.write("="*60 + "\n")
                f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"출력 디렉토리: {self.output_dir.absolute()}\n")
                f.write("\n[통계]\n")
                f.write(f"- 처리된 파일: {self.stats['total_files_processed']}개\n")
                f.write(f"- 병합된 페이지: {self.stats['total_pages_merged']:,}페이지\n")
                f.write(f"- 경고: {self.stats['warnings']}개\n")
                f.write(f"- 오류: {self.stats['errors']}개\n")
                f.write("\n")
                
                if self.merge_log:
                    f.write("[상세 로그]\n")
                    f.write("-" * 40 + "\n")
                    for i, log_entry in enumerate(self.merge_log, 1):
                        f.write(f"{i:3d}. {log_entry}\n")
                else:
                    f.write("특별한 문제가 발생하지 않았습니다.\n")
                
                f.write("\n" + "="*60 + "\n")
            
            logger.info(f"병합 보고서 저장 완료")
            print(f"\n📋 상세 보고서가 저장되었습니다: {log_path.name}")
            
        except Exception as e:
            logger.error(f"병합 보고서 저장 실패: {e}")
            logger.debug(f"상세 오류: {traceback.format_exc()}")