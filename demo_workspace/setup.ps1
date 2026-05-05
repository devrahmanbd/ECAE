Write-Host "Installing Visual Studio Code..."
$VSCodeUrl = "https://aka.ms/win32-x64-user-stable"
$VSCodeInstaller = "vscode_installer.exe"

Invoke-WebRequest -Uri $VSCodeUrl -OutFile $VSCodeInstaller

Start-Process -FilePath $VSCodeInstaller -ArgumentList "--silent --install-dir C:\Program Files\Microsoft VS Code" -Wait

Write-Host "Installing Python..."
$PythonUrl = "https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe"
$PythonInstaller = "python_installer.exe"

Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonInstaller
Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

Write-Host "Verifying Python installation..."
$pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313" # Adjust path if needed
$env:Path += ";$pythonPath"
$env:Path += ";$pythonPath\Scripts"

Write-Host "Installing Python modules from requirements.txt..."
$pythonExe = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r .\requirements.txt
} else {
    Write-Host "Python installation failed. Please check the log."
}

Write-Host "Installation complete!"
