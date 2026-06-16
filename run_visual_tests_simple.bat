@echo off
REM Visual Test - Simple Version

echo ================================
echo Visual HTML Test
echo ================================
echo.

if not exist "test_results\html" mkdir test_results\html

call venv\Scripts\activate

pytest -m visual -v -s

echo.
echo ================================
echo Test Done
echo ================================
echo.

explorer test_results\html

pause
