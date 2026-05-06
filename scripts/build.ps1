param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if ($Clean) {
    if (Test-Path build)   { Remove-Item -Recurse -Force build }
    if (Test-Path dist)    { Remove-Item -Recurse -Force dist }
    if (Test-Path "HardwareOptimizer.spec") { Remove-Item -Force "HardwareOptimizer.spec" }
}

py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install pyinstaller

py -m PyInstaller `
    --noconfirm `
    --windowed `
    --name HardwareOptimizer `
    --collect-submodules PySide6 `
    --collect-submodules wmi `
    --collect-submodules psutil `
    app/main.py

Write-Host ""
Write-Host "Build concluido. Executavel em: dist/HardwareOptimizer/HardwareOptimizer.exe"
Write-Host "Para validar em maquina limpa:"
Write-Host "  1. Copie a pasta dist/HardwareOptimizer/ para a maquina alvo."
Write-Host "  2. Execute HardwareOptimizer.exe sem privilegios elevados."
Write-Host "  3. Confirme que a coleta funciona e o relatorio gera JSON e HTML."
