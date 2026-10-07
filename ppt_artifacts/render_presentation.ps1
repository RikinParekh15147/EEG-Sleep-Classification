param([string]$PresentationPath,[string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
Write-Output 'Starting PowerPoint COM renderer'
$app = New-Object -ComObject PowerPoint.Application
$app.Visible = -1
$app.DisplayAlerts = 1
$app.AutomationSecurity = 3
Write-Output 'PowerPoint started'
$deck = $null
try {
    $deck = $app.Presentations.Open($PresentationPath, -1, 0, -1)
    Write-Output "Opened presentation: $($deck.Slides.Count) slides"
    $deck.Export($OutputDirectory, 'PNG', 1920, 1080)
    Write-Output 'Exported slide PNGs'
    $deck.SaveAs((Join-Path $OutputDirectory 'presentation.pdf'), 32)
    $rows = @()
    foreach ($slide in $deck.Slides) {
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTable -eq -1) {
                foreach ($r in 1..$shape.Table.Rows.Count) {
                    foreach ($c in 1..$shape.Table.Columns.Count) {
                        $cs = $shape.Table.Cell($r, $c).Shape
                        $rows += [pscustomobject]@{
                            slide=$slide.SlideIndex; shape="Table cell $r,$c"; text=$cs.TextFrame.TextRange.Text
                            left=$cs.Left; top=$cs.Top; width=$cs.Width; height=$cs.Height
                            boundHeight=$cs.TextFrame2.TextRange.BoundHeight; boundWidth=$cs.TextFrame2.TextRange.BoundWidth
                            fontSize=$cs.TextFrame2.TextRange.Font.Size
                        }
                    }
                }
            }
            if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
                $tf = $shape.TextFrame2
                $rows += [pscustomobject]@{
                    slide=$slide.SlideIndex; shape=$shape.Name; text=$shape.TextFrame.TextRange.Text
                    left=$shape.Left; top=$shape.Top; width=$shape.Width; height=$shape.Height
                    boundHeight=$tf.TextRange.BoundHeight; boundWidth=$tf.TextRange.BoundWidth
                    fontSize=$tf.TextRange.Font.Size
                }
            }
        }
    }
    $rows | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory 'powerpoint_text_bounds.json')
    Write-Output "PowerPoint opened successfully: $($deck.Slides.Count) slides rendered."
} finally {
    if ($null -ne $deck) { $deck.Close() }
    $app.Quit()
}
