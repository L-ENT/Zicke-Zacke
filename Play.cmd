@echo off
setlocal
cd /d "%~dp0"
set "GAME_JAR=build\ChickenChaChaCha.jar"
if /i "%~1"=="--build" goto build
if exist "%GAME_JAR%" goto play

:build
if not exist "build\classes" mkdir "build\classes"
javac --release 17 -encoding UTF-8 -d "build\classes" src\main\java\sanga\*.java
if errorlevel 1 goto failed
jar --create --file "%GAME_JAR%" --main-class sanga.Server -C "build\classes" sanga -C . web
if errorlevel 1 goto failed
if /i "%~1"=="--build" exit /b 0

:play
set "GAME_PORT=8080"
if not "%~1"=="" set "GAME_PORT=%~1"
java -jar "%GAME_JAR%" "%GAME_PORT%" --open
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Use Java 17 or newer. Building from source also needs javac and jar.
pause
exit /b 1
