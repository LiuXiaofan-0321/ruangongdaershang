Option Explicit
On Error Resume Next

' The GUI script host starts PowerShell hidden from creation and waits for its exit code.
Dim shell, files, scriptPath, powershellPath, command, result
If WScript.Arguments.Count <> 1 Then WScript.Quit 2
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
If Err.Number <> 0 Then WScript.Quit 1
scriptPath = WScript.Arguments(0)
If Not files.FileExists(scriptPath) Then WScript.Quit 2
powershellPath = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
command = Chr(34) & powershellPath & Chr(34) & " -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & scriptPath & Chr(34)
result = shell.Run(command, 0, True)
If Err.Number <> 0 Then WScript.Quit 1
WScript.Quit result
