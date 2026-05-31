Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Users\Admin\AurumCRM"
sh.Run "python app.py", 0, False
WScript.Sleep 2500
sh.Run "http://localhost:5000", 1, False
