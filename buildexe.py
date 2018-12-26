import os, shutil, argparse, re

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

#####################################
#   Get/set Debug
#####################################
def set_debug(file, debug=False):
    file_data=''
    with open(file) as f:
        file_data=f.read()
    with open(file, "w") as f:
        for line in file_data.splitlines():
            if "DEBUG=" in line:
                f.write("DEBUG=%s\n"%debug)
            else:
                f.write(line+"\n")

def get_debug(file):
    file_data=''
    with open(file) as f:
        file_data=f.read()
    for line in file_data.splitlines():
        if "DEBUG=" in line:
            return ( line.split('=')[1] == True )

#####################################
#   Version Handling
####################################
def set_version(file, version):
    if not valid_version_format(version):
        return
    file_data=''
    with open(file) as f:
        file_data=f.read()
    with open(file, "w") as f:
        for line in file_data.splitlines():
            if "VERSION=" in line:
                f.write("VERSION=\"%s\"\n"%version)
            else:
                f.write(line+"\n")

def get_version(file):
    file_data=''
    with open(file) as f:
        file_data=f.read()
    for line in file_data.splitlines():
        if "VERSION=" in line:
            return line.split('=')[1].replace("\"",'')

def valid_version_format(version):
    pattern=re.compile('[0-9]*\.[0-9]*\.[0-9]*$')
    if pattern.match(version):
        return True
    return False

def join_version(version):
    s='.'
    return s.join(version)

def increment_version(file, index):
    version=get_version(file).split('.')
    version[index]=str(int(version[index])+1)
    return version

def reset_version(version, index):
    for i in range(index, len(version)):
        version[i]=str(0)
    return version

def increment_version_bugfix(file):
    version=increment_version(file, 2)
    set_version(file, join_version(version))

def increment_version_minor(file):
    version=increment_version(file, 1)
    version=reset_version(version,2)
    set_version(file, join_version(version))

def increment_version_major(file):
    version=increment_version(file, 0)
    version=reset_version(version,1)
    set_version(file, join_version(version))

INSTALLER_FILENAME="modpackInstaller"
BUILDER_FILENAME="modpackBuilder"

if __name__ == "__main__":
    # Handle and parse arguments
    argparse=argparse.ArgumentParser(description="Build handler for Kiln's Modpack Suite")
    inc = argparse.add_mutually_exclusive_group()
    inc.add_argument('-M', '--major', action='store_true', help='Increment Major version of Suite')
    inc.add_argument('-m', '--minor', action='store_true', help='Increment Minor version of Suite')
    inc.add_argument('-n', '--no-increment', action='store_true', help='Do not increment Version of Suite')
    inc.add_argument('-f', '--force-version',type=str, help='Set version to given version')
    group = argparse.add_mutually_exclusive_group()
    group.add_argument('-i', '--installer', action='store_true', help='Compile Installer Only')
    group.add_argument('-b', '--builder', action='store_true', help='Compile Builder Only')
    argparse.add_argument('-d', '--debug', action='store_true', help='Compile with Debugging mode on')
    args = argparse.parse_args()

    # Set and save directory information
    pwd = os.getcwd()
    if pwd != os.path.dirname(os.path.realpath(__file__)):
        cwd=os.path.dirname(os.path.realpath(__file__))
        os.chdir(cwd)
    else:
        cwd=pwd

    #initialize directory and file variables
    build=os.path.join(cwd, "build")
    dist=os.path.join(cwd, "dist")
    installer_file=os.path.join(cwd, INSTALLER_FILENAME+".py")
    installer_release_file=dist=os.path.join(cwd, "dist", INSTALLER_FILENAME+".exe")
    builder_file=os.path.join(cwd, BUILDER_FILENAME+".py")
    builder_release_file=dist=os.path.join(cwd, "dist", BUILDER_FILENAME+".exe")

    #Increment VERSION depending on values passed
    if args.major:
        if args.installer:
            increment_version_major(installer_file)
        elif args.builder:
            increment_version_major(builder_file)
        else:
            increment_version_major(installer_file)
            increment_version_major(builder_file)
    elif args.minor:
        if args.installer:
            increment_version_minor(installer_file)
        elif args.builder:
            increment_version_minor(builder_file)
        else:
            increment_version_minor(installer_file)
            increment_version_minor(builder_file)
    elif args.no_increment:
        pass
    elif args.force_version:
        if not valid_version_format(args.force_version):
            print("Invalid Version Format. FORMAT: #.#.#")
            exit(1)
        if args.installer:
            set_version(installer_file, args.force_version)
        elif args.builder:
            set_version(builder_file, args.force_version)
        else:
            set_version(installer_file, args.force_version)
            set_version(builder_file, args.force_version)
    else:
        if args.installer:
            increment_version_bugfix(installer_file)
        elif args.builder:
            increment_version_bugfix(builder_file)
        else:
            increment_version_bugfix(installer_file)
            increment_version_bugfix(builder_file)

    ####################
    #   Preparation
    ####################
    #Delete working directories to start clean
    delete_directory(build)
    delete_spec_files(cwd)
    if args.installer:
        os.remove(installer_release_file)
    elif args.builder:
        os.remove(builder_release_file)
    else:
        delete_directory(dist)

    #Start building
    req=os.path.join(cwd, "requirements.txt")
    os.system("pip install -r %s"%req)

    ##############
    #   Compile
    ##############
    if get_debug(installer_file) != str(args.debug):
        print("Setting debug to %s"%args.debug)
        set_debug(installer_file, debug=args.debug)
    if args.debug:
        if args.installer:
            os.system("pyinstaller --icon=rbg_mc.ico -F modpackInstaller.py")
        elif args.builder:
            os.system("pyinstaller --icon=rbg_mc.ico -F modpackBuilder.py")
        else:
            os.system("pyinstaller --icon=rbg_mc.ico -F modpackInstaller.py")
            os.system("pyinstaller --icon=rbg_mc.ico -F modpackBuilder.py")
    else:
        if args.installer:
            os.system("pyinstaller --win-private-assemblies --icon=rbg_mc.ico -F modpackInstaller.py")
        elif args.builder:
            os.system("pyinstaller --noconsole --icon=rbg_mc.ico -F modpackBuilder.py")
        else:
            os.system("pyinstaller --win-private-assemblies --icon=rbg_mc.ico -F modpackInstaller.py")
            os.system("pyinstaller --noconsole --icon=rbg_mc.ico -F modpackBuilder.py")

    ################
    #   Clean up
    ################
    delete_directory(build)
    delete_spec_files(cwd)
    #Restore previous
    if pwd != cwd:
        os.chdir(pwd)
