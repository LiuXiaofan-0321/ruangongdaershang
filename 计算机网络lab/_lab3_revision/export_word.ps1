param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference='Stop'
$wordInstance=New-Object -ComObject Word.Application
$wordInstance.Visible=$false
$wordInstance.DisplayAlerts=0
$reportDocument=$null
try {
    $reportDocument=$wordInstance.Documents.Open($InputFile,$false,$true)
    $reportDocument.Fields.Update() | Out-Null
    $reportDocument.Repaginate()
    $reportDocument.ExportAsFixedFormat($OutputPdf,17)
    Write-Output ('PDF_SAVED '+$OutputPdf)
    Write-Output ('PAGES '+$reportDocument.ComputeStatistics(2))
} finally {
    if ($null -ne $reportDocument) { $reportDocument.Close(0) }
    $wordInstance.Quit()
}
