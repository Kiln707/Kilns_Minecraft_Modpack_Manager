import os, shutil


if __name__ == "__main__":
    debug=True

    pwd = os.getcwd()
    if pwd != os.path.dirname(os.path.realpath(__file__)):
        cwd=os.path.dirname(os.path.realpath(__file__))
        os.chdir(cwd)
    else:
        cwd=pwd
    build=os.path.join(cwd, "build")
    dist=os.path.join(cwd, "dist")

    #Delete working directories to start clean
    if os.path.isdir(build):
        os.system("RMDIR /S /Q %s"%build)
    if os.path.isdir(dist):
        os.system("RMDIR /S /Q %s"%dist)

    #Create working directories
    if os.path.isdir(build):
        os.path.mkdir(build)
    if os.path.isdir(dist):
        os.path.mkdir(dist)

    req=os.path.join(cwd, "requirements.txt")
    os.system("pip install -r %s"%req)

    if debug:
        os.system("pyinstaller --onefile --icon=rbg_mc.ico -F modpackInstaller.py")
        os.system("pyinstaller --onefile --icon=rbg_mc.ico -F modpackBuilder.py")
    else:
        os.system("pyinstaller --onefile --noconsole --icon=rbg_mc.ico -F modpackInstaller.py")
        os.system("pyinstaller --onefile --noconsole --icon=rbg_mc.ico -F modpackBuilder.py")

    #Restore previous
    if pwd != cwd:
        os.chdir(pwd)
