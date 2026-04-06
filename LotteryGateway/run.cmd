@echo off
setlocal

rem Localiza o JDK 17 embarcado no JetBrains/NetBeans ou similar (para fugir da incompatibilidade do Java 25 com Lombok)
for /f "delims=" %%i in ('powershell -Command "$jh = (Get-ChildItem -Path 'C:\Program Files' -Recurse -Filter 'java.exe' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'jdk-17|jbr' } | Select-Object -First 1).Directory.Parent.FullName; $jh"') do set "JAVA_HOME=%%i"

if "%JAVA_HOME%"=="" (
    echo [ERRO] Nao foi possivel localizar um JDK 17 no sistema. O Java 25 padrão causa problemas com o Lombok.
    echo Por favor, certifique-se de configurar a JAVA_HOME para Java 17.
    exit /b 1
)

echo Usando JAVA_HOME: %JAVA_HOME%
set PATH=%JAVA_HOME%\bin;%PATH%

echo Iniciando compilacao do Maven...
call mvnw.cmd clean spring-boot:run
endlocal
