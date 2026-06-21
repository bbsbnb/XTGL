@echo off
title 工程项目证据链管理系统

:MENU
cls
echo ============================================
echo    🏗️  工程项目证据链管理系统
echo ============================================
echo.
echo  ┌─ 检查工具 ─────────────────────────┐
echo  │  1. 🔍 检查当前项目                 │
echo  │  2. 🔍 扫描所有项目                 │
echo  │  3. 📁 新建项目                     │
echo  │  4. 📊 导出证据清单                 │
echo  └────────────────────────────────────┘
echo.
echo  ┌─ 数据库索引工具 ───────────────────┐
echo  │  5. 📋 列出所有记录                 │
echo  │  6. ➕ 添加新记录                   │
echo  │  7. 🔎 搜索记录                    │
echo  │  8. 📊 统计报告                    │
echo  │  9. 📂 查看所有项目                │
echo  └────────────────────────────────────┘
echo.
echo  ┌─ Web 管理界面 ────────────────────┐
echo  │  W. 🌐 启动 Web 管理界面           │
echo  └────────────────────────────────────┘
echo.
echo  ┌─ 系统 ────────────────────────────┐
echo  │  A. 📂 打开系统文件夹              │
echo  │  X. ❌ 退出                       │
echo  └────────────────────────────────────┘
echo.
echo ============================================

set /p CHOICE="请选择: "

if /i "%CHOICE%"=="1" goto CHECK_CURRENT
if /i "%CHOICE%"=="2" goto SCAN_ALL
if /i "%CHOICE%"=="3" goto INIT_PROJECT
if /i "%CHOICE%"=="4" goto EXPORT
if /i "%CHOICE%"=="5" goto DB_LIST
if /i "%CHOICE%"=="6" goto DB_ADD
if /i "%CHOICE%"=="7" goto DB_SEARCH
if /i "%CHOICE%"=="8" goto DB_STATS
if /i "%CHOICE%"=="9" goto DB_PROJECTS
if /i "%CHOICE%"=="A" goto OPEN_FOLDER
if /i "%CHOICE%"=="a" goto OPEN_FOLDER
if /i "%CHOICE%"=="W" goto WEB_START
if /i "%CHOICE%"=="w" goto WEB_START
if /i "%CHOICE%"=="X" exit
if /i "%CHOICE%"=="x" exit

echo 无效选择，请重新输入...
timeout /t 2 >nul
goto MENU

:CHECK_CURRENT
cls
echo 🔍 检查当前项目...
python "%~dp0模板与规则\evidence_check.py"
echo.
pause
goto MENU

:SCAN_ALL
cls
echo 🔍 扫描所有项目...
python "%~dp0模板与规则\evidence_check.py" --scan-all "%~dp0"
echo.
pause
goto MENU

:INIT_PROJECT
cls
set /p PNAME="请输入新项目名称: "
python "%~dp0模板与规则\evidence_check.py" --init "%PNAME%"
echo.
pause
goto MENU

:EXPORT
cls
set /p PPATH="请输入项目文件夹名称（或路径）: "
python "%~dp0模板与规则\evidence_check.py" --export "%PPATH%"
echo.
pause
goto MENU

:DB_LIST
cls
echo 📋 列出所有记录（可筛选项目名）
set /p PFILTER="项目名称（回车=全部）: "
python "%~dp0模板与规则\evidence_db.py" list "%PFILTER%"
echo.
pause
goto MENU

:DB_ADD
cls
python "%~dp0模板与规则\evidence_db.py" add
echo.
pause
goto MENU

:DB_SEARCH
cls
set /p KW="请输入搜索关键词: "
python "%~dp0模板与规则\evidence_db.py" search "%KW%"
echo.
pause
goto MENU

:DB_STATS
cls
set /p PFILTER="项目名称（回车=全部）: "
python "%~dp0模板与规则\evidence_db.py" stats "%PFILTER%"
echo.
pause
goto MENU

:DB_PROJECTS
cls
python "%~dp0模板与规则\evidence_db.py" projects
echo.
pause
goto MENU

:OPEN_FOLDER
explorer "%~dp0"
goto MENU

:WEB_START
cls
echo.
echo ============================================
echo    🌐 启动 Web 管理界面
echo ============================================
echo.
echo  服务器启动后, 在浏览器中访问:
echo  http://localhost:5000
echo.
echo  按 Ctrl+C 停止服务器
echo.
echo ============================================
echo.
cd /d "%~dp0"
python "模板与规则\evidence_web.py"
echo.
pause
goto MENU
