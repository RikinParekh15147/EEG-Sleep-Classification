param()
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
        throw 'Install MiKTeX or TeX Live with pdflatex and bibtex, or upload this docs folder to Overleaf.'
    }
    if (-not (Get-Command bibtex -ErrorAction SilentlyContinue)) {
        throw 'BibTeX is required to build the references.'
    }
    if (-not (Test-Path -LiteralPath 'sn-jnl.cls')) {
        throw 'Missing official Springer class. See TEMPLATE.md.'
    }
    & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
    if ($LASTEXITCODE -ne 0) { throw 'First pdflatex pass failed. Inspect main.log.' }
    & bibtex main
    if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed. Inspect main.blg.' }
    1..2 | ForEach-Object {
        & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
        if ($LASTEXITCODE -ne 0) { throw 'pdflatex failed. Inspect main.log.' }
    }
    Write-Output 'Built docs/main.pdf'
} finally {
    Pop-Location
}
