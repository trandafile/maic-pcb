@echo off
setlocal enabledelayedexpansion

:: ==========================================
::   UPLOAD PROGETTO SU GITHUB (PROTETTO)
:: ==========================================
echo.
echo ==========================================
echo    UPLOAD PROGETTO SU GITHUB (PROTETTO)
echo ==========================================
echo.

:: --- CONFIGURAZIONE ---
set REPO_URL=https://github.com/trandafile/maic-pcb.git

:: 1. PROTEZIONE SEGRETI (Sincronizzazione .gitignore)
echo [*] Verifica sicurezza .gitignore...
(
echo # Protezione automatica segreti
echo hipa/
echo __pycache__/
echo .venv/
echo /*.json
echo /*.toml
echo !pcb_stackup.json
echo .streamlit/
) > .gitignore

:: 2. AGGIORNAMENTO FILES (Usa . per catturare tutto tranne quanto in .gitignore)
echo [*] Staging file sicuri e completi...
git add .

:: 3. COMMIT
echo [*] Branch corrente: main
set /p msg="Inserisci messaggio commit (INVIO per automatico): "
if "%msg%"=="" set msg="Ripristino file progetto (no secrets)"

echo [*] Commit in corso...
git commit -m "%msg%"

:: 4. PUSH
echo [*] Push su GitHub...
git remote set-url origin %REPO_URL%
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo [!] ERRORE: Il push è stato rifiutato.
    echo     GitHub blocca automaticamente il caricamento se rileva chiavi API.
    echo     Verifica di NON avere file .json o .toml sensibili nella cartella.
) else (
    echo.
    echo ==========================================
    echo    SUCCESSO: FILE RIPRISTINATI E CARICATI.
    echo ==========================================
)

echo.
pause
