# Script para instalar idioma español en Tesseract OCR
# Ejecutar como Administrador en PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalador de Idioma Español - Tesseract" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Tesseract está instalado
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (-not (Test-Path $tesseractPath)) {
    Write-Host "ERROR: Tesseract no se encuentra en la ruta esperada." -ForegroundColor Red
    Write-Host "Ruta esperada: $tesseractPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Tesseract encontrado en: $tesseractPath" -ForegroundColor Green

# Verificar carpeta tessdata
$tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
if (-not (Test-Path $tessdataPath)) {
    Write-Host "Creando carpeta tessdata..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $tessdataPath | Out-Null
}

# URL del archivo de idioma español
$url = "https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata"
$outputFile = Join-Path $tessdataPath "spa.traineddata"

Write-Host ""
Write-Host "Descargando idioma español desde GitHub..." -ForegroundColor Yellow
Write-Host "URL: $url" -ForegroundColor Gray
Write-Host "Destino: $outputFile" -ForegroundColor Gray
Write-Host ""

try {
    # Descargar el archivo
    Invoke-WebRequest -Uri $url -OutFile $outputFile -UseBasicParsing
    
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length / 1MB
        Write-Host "✓ Archivo descargado exitosamente ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "ERROR: El archivo no se descargó correctamente." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR al descargar: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solución alternativa:" -ForegroundColor Yellow
    Write-Host "1. Abre tu navegador y ve a: https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata" -ForegroundColor Cyan
    Write-Host "2. Guarda el archivo como 'spa.traineddata' en:" -ForegroundColor Cyan
    Write-Host "   $tessdataPath" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Verificando instalación..." -ForegroundColor Yellow

# Verificar que Tesseract puede ver el idioma
try {
    $langs = & tesseract --list-langs 2>&1
    if ($langs -match "spa") {
        Write-Host "✓ Idioma español instalado correctamente!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Idiomas disponibles:" -ForegroundColor Cyan
        $langs | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    } else {
        Write-Host "⚠ ADVERTENCIA: El archivo se descargó pero Tesseract no lo reconoce." -ForegroundColor Yellow
        Write-Host "Intenta reiniciar el servidor Django o reiniciar tu terminal." -ForegroundColor Yellow
    }
} catch {
    Write-Host "No se pudo verificar, pero el archivo está en su lugar." -ForegroundColor Yellow
    Write-Host "Reinicia el servidor Django y prueba nuevamente." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalación completada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Reinicia el servidor Django si está corriendo" -ForegroundColor White
Write-Host "2. Prueba subir una factura nuevamente" -ForegroundColor White
Write-Host ""

