import os, shutil, argparse, re, sys

SERVERNAME="Related by Gaming"

def files_in_dir(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def delete_build_files(path):
    for file in files_in_dir(path):
        if file.endswith('.spec') or file.endswith("_version.txt"):
            os.remove(file)

def delete_directory(path):
    if os.path.isdir(path):
        os.system("RMDIR /S /Q %s"%path)

#####################################
#   Version File
#####################################
def get_version_file(cwd):
    data = ''
    with open(os.path.join(cwd, "version_template.txt")) as f:
        data=f.read()
    return data

def generate_version_file(cwd, filename, version):
    version_file_data = get_version_file(cwd)
    version_file_data = version_file_data.replace("SERVERNAME", SERVERNAME)
    version_file_data = version_file_data.replace("FILEDESC", filename+'.exe')
    version_file_data = version_file_data.replace("VERSION", version)
    version_file_data = version_file_data.replace("PRODNAME", "Kiln's Modpack Suite")
    with open(os.path.join(cwd,filename+"_version.txt"), 'w+') as f:
        f.write(version_file_data)
    return filename+"_version.txt"

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

def get_server_name(file):
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
    installer_release_file=os.path.join(cwd, "dist", INSTALLER_FILENAME+".exe")
    builder_file=os.path.join(cwd, BUILDER_FILENAME+".py")
    builder_release_file=os.path.join(cwd, "dist", BUILDER_FILENAME+".exe")

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
    delete_build_files(cwd)
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
        debug_args="--win-private-assemblies --icon=rbg_mc.ico"
        if args.installer:
            installer_version_file = generate_version_file(cwd, INSTALLER_FILENAME, get_version(installer_file))
            os.system("pyinstaller %s --version-file %s -F %s"%(debug_args, installer_version_file, installer_file))
        elif args.builder:
            os.system("pyinstaller %s -F %s"%(debug_args, installer_file))
        else:
            installer_version_file = generate_version_file(cwd, INSTALLER_FILENAME, get_version(installer_file))
            os.system("pyinstaller %s --version-file %s -F %s"%(debug_args, installer_version_file, installer_file))
            os.system("pyinstaller %s -F %s"%(debug_args, builder_file))
    else:
        installer_release_args="--onedir --noconsole --win-private-assemblies --icon=rbg_mc.ico"
        builder_release_args="--onefile --noconsole --win-private-assemblies --icon=rbg_mc.ico"
        if args.installer:
            installer_version_file = generate_version_file(cwd, INSTALLER_FILENAME, get_version(installer_file))
            os.system("pyinstaller %s --version-file %s -F %s"%(installer_release_args, installer_version_file, installer_file))
        elif args.builder:
            os.system("pyinstaller %s -F %s"%(builder_release_args, installer_file))
        else:
            installer_version_file = generate_version_file(cwd, INSTALLER_FILENAME, get_version(installer_file))
            os.system("pyinstaller %s --version-file %s -F %s"%(installer_release_args, installer_version_file, installer_file))
            os.system("pyinstaller %s -F %s"%(builder_release_args, builder_file))

    ################
    #   Clean up
    ################
    delete_directory(build)
    delete_build_files(cwd)
    #Restore previous
    if pwd != cwd:
        os.chdir(pwd)
