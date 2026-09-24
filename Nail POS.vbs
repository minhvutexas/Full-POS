' Nail POS — Silent Launcher
' Double-click this to start everything with no console flash.
Dim sh : Set sh = CreateObject("WScript.Shell")
Dim dir : dir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
sh.Run "cmd /c """ & dir & "LAUNCH-POS.bat""", 1, False
