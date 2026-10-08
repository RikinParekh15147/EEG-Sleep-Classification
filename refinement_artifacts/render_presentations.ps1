param([switch]$Original)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$renderRoot = Join-Path $PSScriptRoot $(if ($Original) {'source_renders'} else {'renders'})
New-Item -ItemType Directory -Path $renderRoot -Force | Out-Null
$pptApp = New-Object -ComObject PowerPoint.Application
$measurements = @()
try {
    foreach ($name in @('final_sleep_stage_project_presentation.pptx','sleep_stage_project_12_slides.pptx','mid.original_backup.pptx')) {
        $inputPath = Join-Path $(if ($Original) {Join-Path $PSScriptRoot 'originals'} else {$taskRoot}) $name
        $dest = Join-Path $renderRoot ([IO.Path]::GetFileNameWithoutExtension($name).Replace('.','_'))
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
        $deck = $pptApp.Presentations.Open($inputPath, $true, $false, $false)
        $deck.Export($dest, 'PNG', 1600, 900)
        if (-not $Original) {
            $deck.SaveAs((Join-Path $taskRoot ([IO.Path]::ChangeExtension($name,'pdf'))),32)
            foreach ($slide in $deck.Slides) {
                foreach ($shape in $slide.Shapes) {
                    if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                        $range = $shape.TextFrame.TextRange
                        $measurements += @{deck=$name;slide=$slide.SlideIndex;text=$range.Text;left=$shape.Left;top=$shape.Top;width=$shape.Width;height=$shape.Height;boundWidth=$range.BoundWidth;boundHeight=$range.BoundHeight}
                    }
                }
            }
        }
        Write-Output "$name : $($deck.Slides.Count) slides rendered"
        $deck.Close()
    }
    if (-not $Original) {$measurements | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $renderRoot 'text_bounds.json') -Encoding UTF8}
} finally {$pptApp.Quit()}
