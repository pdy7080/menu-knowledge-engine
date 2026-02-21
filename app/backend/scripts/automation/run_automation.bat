@echo off
REM ============================================
REM Menu Knowledge Engine - Automation Runner
REM Windows Task Scheduler에서 호출하는 배치 파일
REM ============================================

REM 작업 디렉토리 설정
cd /d "C:\project\menu\app\backend\scripts"

REM Python 경로 (시스템 PATH에 있으면 python, 아니면 절대경로 지정)
set PYTHON=python

REM 로그 디렉토리 생성
if not exist "C:\project\menu\app\backend\data\automation\logs" (
    mkdir "C:\project\menu\app\backend\data\automation\logs"
)

REM 인자 확인 (기본: all)
set JOB=%1
if "%JOB%"=="" set JOB=all

REM 실행 시간 기록
echo [%date% %time%] Starting job: %JOB% >> "C:\project\menu\app\backend\data\automation\logs\task_scheduler.log"

REM 파이프라인 실행
%PYTHON% -m automation.run_pipeline --job %JOB%

REM 종료 코드 기록
echo [%date% %time%] Job %JOB% finished with exit code: %ERRORLEVEL% >> "C:\project\menu\app\backend\data\automation\logs\task_scheduler.log"