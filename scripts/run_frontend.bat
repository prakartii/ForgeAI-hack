@echo off
REM Start FailureFoundry React/Tailwind Frontend Development Server
set "PATH=C:\Program Files\nodejs;%PATH%"
echo Starting FailureFoundry Frontend on http://localhost:5173 ...

cd "%~dp0..\frontend"
npm run dev
