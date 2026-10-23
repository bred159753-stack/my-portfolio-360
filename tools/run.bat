@echo off
chcp 65001 >nul
setlocal
rem 產生網頁用 WebP 壓縮圖並更新 portfolio_data.json（雙擊即可執行）
set "PYTHONIOENCODING=utf-8"

rem 切換到專案根目錄（本檔所在 tools 資料夾的上一層）
cd /d "%~dp0.."

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [錯誤] 找不到 Python，請先安裝 https://www.python.org/downloads/ （安裝時勾選 Add python.exe to PATH）
    goto :end
)

%PY% -c "import PIL" >nul 2>nul
if errorlevel 1 (
    echo 尚未安裝 Pillow，正在安裝...
    %PY% -m pip install --user pillow
    if errorlevel 1 (
        echo [錯誤] Pillow 安裝失敗，請手動執行：%PY% -m pip install pillow
        goto :end
    )
)

%PY% "tools\build_web_images.py" %*
if errorlevel 1 echo [錯誤] 轉檔過程發生問題，請查看上方訊息。

:end
echo.
pause
endlocal
