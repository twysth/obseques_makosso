$Project = "$HOME\Desktop\obseques_makosso"
$Database = Join-Path $Project "data\obseques.db"
$BackupDir = Join-Path $Project "backups"

New-Item -ItemType Directory -Force $BackupDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "obseques_$Timestamp.db"

Copy-Item $Database $BackupFile -Force

Write-Host "Sauvegarde créée :"
Write-Host $BackupFile

# Conservation des 30 sauvegardes les plus récentes
$Backups = Get-ChildItem $BackupDir -Filter "obseques_*.db" |
    Sort-Object LastWriteTime -Descending

if ($Backups.Count -gt 30) {
    $Backups |
        Select-Object -Skip 30 |
        Remove-Item -Force
}

Write-Host "Sauvegarde terminée."