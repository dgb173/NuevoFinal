# Script para subir el proyecto actualizado a GitHub
# Ejecutar como administrador si es necesario

Write-Host "=== CONFIGURACION DEL PROYECTO PARA GITHUB ===" -ForegroundColor Green

# Verificar si Git está disponible
$gitPath = $null
$possiblePaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Git\bin\git.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $gitPath = $path
        break
    }
}

if (-not $gitPath) {
    Write-Host "Git no encontrado. Instalando Git..." -ForegroundColor Yellow
    try {
        winget install --id Git.Git -e --source winget --silent
        Write-Host "Git instalado. Por favor, reinicia PowerShell y ejecuta este script nuevamente." -ForegroundColor Green
        exit
    }
    catch {
        Write-Host "Error instalando Git. Instala Git manualmente desde https://git-scm.com/" -ForegroundColor Red
        exit
    }
}

Write-Host "Git encontrado en: $gitPath" -ForegroundColor Green

# Cambiar al directorio del proyecto
Set-Location $PSScriptRoot

# Configurar alias para git
Set-Alias git $gitPath

# Verificar si es un repositorio git
if (-not (Test-Path ".git")) {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Yellow
    & $gitPath init
    & $gitPath branch -M main
}

# Configurar usuario si no está configurado
$userName = & $gitPath config user.name
$userEmail = & $gitPath config user.email

if (-not $userName) {
    $inputName = Read-Host "Ingresa tu nombre de usuario de GitHub"
    & $gitPath config user.name "$inputName"
}

if (-not $userEmail) {
    $inputEmail = Read-Host "Ingresa tu email de GitHub"
    & $gitPath config user.email "$inputEmail"
}

# Agregar archivos
Write-Host "Agregando archivos al repositorio..." -ForegroundColor Yellow
& $gitPath add .

# Crear commit
$commitMessage = "Actualización del proyecto - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
& $gitPath commit -m "$commitMessage"

# Verificar si hay remote origin configurado
$remoteUrl = & $gitPath remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host ""
    Write-Host "=== CONFIGURACION DEL REPOSITORIO REMOTO ===" -ForegroundColor Cyan
    Write-Host "Para conectar con GitHub, necesitas:"
    Write-Host "1. Crear un repositorio en GitHub (https://github.com/new)"
    Write-Host "2. Copiar la URL del repositorio (ejemplo: https://github.com/tu-usuario/tu-repo.git)"
    Write-Host ""
    
    $repoUrl = Read-Host "Ingresa la URL del repositorio de GitHub"
    if ($repoUrl) {
        & $gitPath remote add origin $repoUrl
        Write-Host "Repositorio remoto configurado: $repoUrl" -ForegroundColor Green
    }
}

# Subir cambios
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Yellow
try {
    & $gitPath push -u origin main
    Write-Host ""
    Write-Host "=== PROYECTO SUBIDO EXITOSAMENTE ===" -ForegroundColor Green
    Write-Host "Tu proyecto ha sido actualizado en GitHub." -ForegroundColor Green
    Write-Host ""
    Write-Host "Para desplegar en Streamlit Cloud:" -ForegroundColor Cyan
    Write-Host "1. Ve a https://streamlit.io/cloud"
    Write-Host "2. Conecta tu cuenta de GitHub"
    Write-Host "3. Selecciona tu repositorio"
    Write-Host "4. Configura el archivo principal como: streamlit_app_final.py"
    Write-Host "5. Haz clic en Deploy"
}
catch {
    Write-Host ""
    Write-Host "Error al subir cambios. Posibles soluciones:" -ForegroundColor Red
    Write-Host "1. Verifica tus credenciales de GitHub"
    Write-Host "2. Asegúrate de que el repositorio existe"
    Write-Host "3. Ejecuta manualmente: git push -u origin main"
    Write-Host ""
    Write-Host "Comando para configurar remote manualmente:" -ForegroundColor Yellow
    Write-Host "git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git"
}

Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")