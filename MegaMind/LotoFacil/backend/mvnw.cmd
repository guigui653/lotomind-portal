@REM Maven Wrapper script for Windows
@REM Downloads Maven if not present and runs it

@echo off
setlocal

set MAVEN_PROJECTBASEDIR=%~dp0
set MAVEN_USER_HOME=%USERPROFILE%\.m2
set MAVEN_HOME=%MAVEN_USER_HOME%\wrapper\dists\apache-maven-3.9.6

if exist "%MAVEN_HOME%\bin\mvn.cmd" goto runMaven

echo Downloading Maven 3.9.6...
mkdir "%MAVEN_HOME%" 2>nul

powershell -Command "& { Invoke-WebRequest -Uri 'https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.6/apache-maven-3.9.6-bin.zip' -OutFile '%TEMP%\maven.zip' }"
powershell -Command "& { Expand-Archive -Path '%TEMP%\maven.zip' -DestinationPath '%MAVEN_USER_HOME%\wrapper\dists' -Force }"

:runMaven
"%MAVEN_HOME%\bin\mvn.cmd" %*
