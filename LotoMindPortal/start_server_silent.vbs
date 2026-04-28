' LotoMind Portal — Inicializador silencioso
' Este script inicia o servidor Flask sem abrir uma janela de console.

Dim shell
Set shell = CreateObject("WScript.Shell")

' Executa o servidor em segundo plano (0 = janela oculta)
shell.Run "cmd /c cd /d ""C:\Users\widso\OneDrive\Documentos\Projetos\LotoMega\LotoMindPortal"" && python app.py", 0, False

Set shell = Nothing
