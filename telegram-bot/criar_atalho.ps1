$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("C:\Users\diogo\Desktop\HubVision Bot.lnk")
$shortcut.TargetPath = "P:\LandingPage-PromptHub\telegram-bot\iniciar_bot.bat"
$shortcut.WorkingDirectory = "P:\LandingPage-PromptHub\telegram-bot"
$shortcut.WindowStyle = 7
$shortcut.Save()
Write-Host "Atalho criado na area de trabalho!"
