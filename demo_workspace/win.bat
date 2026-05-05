@echo off

start "" "powershell.exe" -File "install.ps1"
timeout /t 10 /nobreak

start "" "powershell.exe" -NoExit -File "tab1.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab2.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab3.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab4.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab5.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab6.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab7.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab8.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab9.ps1"
timeout /t 5 /nobreak

start "" "powershell.exe" -NoExit -File "tab10.ps1"
timeout /t 5 /nobreak

