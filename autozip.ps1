$suffix=Get-Date -Format "yyyyMMdd"
$full=$("SIT"+$suffix)
Xcopy /E /I /H ".\dist" $full
Compress-Archive $full $(".\release\"+$full)