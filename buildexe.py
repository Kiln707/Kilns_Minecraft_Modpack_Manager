import os, shutil

def files_in_dir(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def delete_spec_files(path):
    for file in files_in_dir(path):
        if file.endswith('.spec'):
            os.remove(file)

def delete_directory(path):
    if os.path.isdir(path):
        os.system("RMDIR /S /Q %s"%path)

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
    delete_directory(build)
    delete_directory(dist)
    delete_spec_files(cwd)

    #Start building
    req=os.path.join(cwd, "requirements.txt")
    os.system("pip install -r %s"%req)

    if debug:
        os.system("pyinstaller --win-private-assemblies --icon=rbg_mc.ico -F modpackInstaller.py")
        os.system("pyinstaller --icon=rbg_mc.ico -F modpackBuilder.py")
    else:
        os.system("pyinstaller --onefile --noconsole --icon=rbg_mc.ico -F modpackInstaller.py")
        os.system("pyinstaller --onefile --noconsole --icon=rbg_mc.ico -F modpackBuilder.py")

    #cleanup
    delete_directory(build)
    delete_spec_files(cwd)

    #Restore previous
    if pwd != cwd:
        os.chdir(pwd)
