RMDIR /S /Q %CD%\build
RMDIR /S /Q %CD%\dist
pyinstaller --onefile --icon=rbg_mc.ico -F modpackManager.py
pyinstaller --onefile --icon=rbg_mc.ico -F modpackBuilder.py
pause