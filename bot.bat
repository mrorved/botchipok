@echo off
chcp 65001 >nul
title ShopAdmin — Запуск

echo.
echo  ╔══════════════════════════════════════╗
echo  ║        ShopAdmin — Запуск            ║
echo  ╚══════════════════════════════════════╝
echo.

:: --- Проверка Docker ---
docker info >nul 2>&1
if errorlevel 1 (
    echo  [ОШИБКА] Docker не запущен или не установлен.
    echo  Запустите Docker Desktop и попробуйте снова.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker запущен

:: --- Создание папки data ---
if not exist "data" (
    mkdir data
    echo  [OK] Папка data создана
) else (
    echo  [OK] Папка data уже существует
)

:: --- Проверка .env ---
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo.
        echo  [!] Файл .env создан из .env.example
        echo  [!] ОБЯЗАТЕЛЬНО заполните BOT_TOKEN и ADMIN_TELEGRAM_ID
        echo  [!] Откройте .env в блокноте, заполните и перезапустите батник.
        echo.
        start notepad ".env"
        pause
        exit /b 0
    ) else (
        echo  [ОШИБКА] Файл .env не найден и .env.example тоже отсутствует.
        pause
        exit /b 1
    )
) else (
    echo  [OK] Файл .env найден
)

:: --- Проверка что BOT_TOKEN заполнен ---
findstr /C:"BOT_TOKEN=YOUR_BOT_TOKEN_HERE" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  [!] BOT_TOKEN не заполнен в .env!
    echo  [!] Откройте .env, вставьте токен от @BotFather и перезапустите.
    echo.
    start notepad ".env"
    pause
    exit /b 0
)

:: --- Спросить режим запуска ---
echo.
echo  Выберите режим запуска:
echo  [1] Запустить (пересобрать образы)
echo  [2] Запустить (без пересборки, быстрее)
echo  [3] Остановить все сервисы
echo  [4] Показать логи
echo  [5] Выход
echo.
set /p choice=" Ваш выбор (1-5): "

if "%choice%"=="1" goto BUILD
if "%choice%"=="2" goto START
if "%choice%"=="3" goto STOP
if "%choice%"=="4" goto LOGS
if "%choice%"=="5" exit /b 0

echo  Неверный выбор.
pause
exit /b 0


:BUILD
echo.
echo  Сборка и запуск (это может занять 3-5 минут при первом запуске)...
echo.
docker-compose up --build -d
goto DONE

:START
echo.
echo  Запуск сервисов...
echo.
docker-compose up -d
goto DONE

:STOP
echo.
echo  Остановка сервисов...
docker-compose down
echo  [OK] Сервисы остановлены.
pause
exit /b 0

:LOGS
echo.
echo  Логи (Ctrl+C для выхода)...
echo.
docker-compose logs -f
exit /b 0


:DONE
if errorlevel 1 (
    echo.
    echo  [ОШИБКА] Что-то пошло не так. Смотрите вывод выше.
    pause
    exit /b 1
)

echo.
echo  ══════════════════════════════════════════
echo   Сервисы запущены!
echo.
echo   Веб-панель:  http://localhost:3000
echo   Логин:       admin
echo   Пароль:      admin123
echo.
echo   API Swagger: http://localhost:8000/docs
echo  ══════════════════════════════════════════
echo.

set /p open=" Открыть браузер? (y/n): "
if /i "%open%"=="y" start http://localhost:3000

echo.
pause