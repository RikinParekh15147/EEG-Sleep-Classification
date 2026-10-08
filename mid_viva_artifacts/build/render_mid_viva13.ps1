$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$outputRoot = Join-Path $taskRoot 'mid_viva_artifacts/output'
$renderRoot = Join-Path $PSScriptRoot 'renders13'
New-Item -ItemType Directory -Path $renderRoot -Force | Out-Null
$app = New-Object -ComObject PowerPoint.Application
$bounds = @()
try {
    $deck = $app.Presentations.Open((Join-Path $outputRoot 'EEG_Sleep_Mid_Viva_13_Slides.pptx'), $true, $false, $false)
    $deck.Export($renderRoot, 'PNG', 1600, 900)
    $deck.SaveAs((Join-Path $outputRoot 'EEG_Sleep_Mid_Viva_13_Slides.pdf'),32)
    foreach ($slide in $deck.Slides) {
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                $r=$shape.TextFrame.TextRange
                $bounds += @{slide=$slide.SlideIndex;text=$r.Text;left=$shape.Left;top=$shape.Top;width=$shape.Width;height=$shape.Height;boundWidth=$r.BoundWidth;boundHeight=$r.BoundHeight}
            }
        }
    }
    $bounds | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'text_bounds13.json') -Encoding UTF8
    Write-Output "Rendered $($deck.Slides.Count) slides and exported PDF"
    $bounds | Where-Object { $_.boundWidth -gt ($_.width+2) -or $_.boundHeight -gt ($_.height+2) } | ConvertTo-Json -Depth 4
    $deck.Close()
} finally { $app.Quit() }
