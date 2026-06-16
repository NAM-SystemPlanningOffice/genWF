@echo off
REM Visual Test Execution

echo ================================
echo Visual Test Execution
echo ================================
echo.
echo Saving HTML files to: test_results\html\
echo.

REM Create output directories
if not exist "test_results\html" mkdir test_results\html
if not exist "test_results\screenshots" mkdir test_results\screenshots

REM Activate virtual environment
call venv\Scripts\activate

echo Running tests...
echo.

REM Execute visual tests
pytest -m visual -v -s

echo.
echo ================================
echo Test Completed
echo ================================
echo.
echo Saved HTML files:
dir /b test_results\html\*.html
echo.
echo Open HTML files in browser to view
echo Example: start test_results\html\02_application_list.html
echo.

REM Open explorer automatically
explorer test_results\html

pause
