
from functools import partial
from itertools import product
from io import BytesIO
from multiprocessing import Pool, Process
from nbtlib import Compound, List, nbt, String
from subprocess import run
from sys import exit
from tkinter import *
from zipfile import ZipFile
import urllib.request as request
from urllib.parse import quote, urlparse
import validators
from urllib.error import HTTPError, URLError
import ctypes, datetime, getpass, json, logging, os, re, shutil, subprocess, sys, tempfile, time, traceback

#####################################
# Editable Variables for installer
#####################################
#   Server name for Modpack, Will be used in connections
SERVERNAME='Related by Gaming'
#   URL For the modpack manifest.
MANIFEST_URL = "http://relatedbygaming.ddns.net/files/minecraft/rbg_mc.manifest"

#####
#   helpers and Checkers
#####
def correct_url(url):
    if url.startswith('http://'):
        return 'http://'+quote(url[7:])
    if url.startswith('https://'):
        return 'https://'+quote(url[8:])
    return quote(url)

def is_valid_url(url):
    return validators.url(url)

def split_versions(version=''):
    if version:
        pos = str(version).rfind('-')
        return ( str(version)[:int(pos)], str(version)[int(pos+1):])

def update_available(latest, current):
    if current:
        return float(latest['version']) > float(current['version'])
    return True

def is_java_installed():
    try:
        subprocess.call(["java","-version"])
    except FileNotFoundError as e:
        return False
    return True

def is_admin():
    if os.name=='nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        if getpass.getuser() == 'root':
            return True
        return False

def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def restart_as_admin(action):
    result = 0
    if sys.argv[0].endswith('.py'):
        logger.debug('Python')
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "python", sys.argv[0]+" quiet %s"%action, '', 6)
    else:
        logger.debug('EXE')
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.argv[0], "quiet %s"%action, '', 6)
    if not result>32:
        logger.error("Failed to run as administrator")
        return False
    return True

def set_data_directory_path():
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)
    return data_directory

def get_data_directory():
    if os.name =='nt':
        return os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        return os.path.join(os.path.expanduser(), DATA_DIR_NAME)

#####
#   File MANIPULATIONS
#####
def download(url=None):
    if not url:
        logger.debug('No URL')
        return None
    if not is_valid_url(url):
        url=correct_url(url)
    if not ( url.startswith('http://') or url.startswith('https://') ):
        url='http://'+url
    try:
        logger.debug('Downloading from %s'%url)
        response = request.urlopen(url)
        return response.read()
    except HTTPError as e:
        return None
    except URLError as e:
        return None
    except Exception as e:
        return None
    return None

def filename_from_url(url=None):
    if url:
        pos=str(url).rfind('/')+1
        return str(url)[int(pos):]

def filename_from_path(path=None):
    if path:
        pos=str(path).rfind('\\')+1
        return str(path)[int(pos):]

def files_in_dir(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def remove_file(filename):
    if os.path.isfile(filename):
        os.remove(filename)

def downloadExtact_zip(dir, url=''):
    logger.debug("Downloading zipfile from %s"%url)
    resp = download(url)
    zipfile = ZipFile(BytesIO(resp))
    zipfile.extractall(dir)

def download_json(url=None):
    data = download(url)
    if data:
        return json.loads(data.decode('utf-8'))
    return None

def download_file(url, filename):
    data = download(url)
    if data:
        with open(filename, "wb+") as f:
            f.write(data)
            return True
    else:
        logging.error("Did not receive data from url: %s"%url)
    return False

def download_file_size(url):
    try:
        with request.urlopen(url) as r:
            return int(r.info()['Content-Length'])
    except:
        pass
    return 0

def get_file_size(filename):
    if os.path.isfile(filename):
        logger.debug("%s exists"%filename)
        return os.path.getsize(filename)
    return 0

def save_file(file_location, data):
    try:
        with open(file_location, 'w+') as file:
            file.write(data)
    except TypeError as e:
        with open(file_location, 'wb') as file:
            file.write(data)

def save_json(file_location=None, data=None):
    if file_location and data:
        logger.debug("Writing json file at %s"%file_location)
        with open(file_location,'w+') as file:
            json.dump(data, file)

def open_json(file_location=None):
    if file_location:
        logger.debug("Opening json file at %s"%file_location)
        with open(file_location,'r') as file:
            data = json.load(file)
        return data
    return None

def make_directory(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

def delete_directory(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)

#####
#   Mod MANIPULATIONS
#####
def mod_filename(modname, modversion):
    return "%s-%s.jar"%(modname,modversion)

def split_mod_filename(filename):
    name=filename.split('.')
    return (name[0].split('-'))

def validate_mod_file(mod_dir, mod):
    modfile=os.path.join(mod_dir, mod_filename(mod['name'],mod['version']))
    download=False
    logger.debug("Validating %s"%modfile)
    dl_size = download_file_size(mod['download'])
    file_size = get_file_size(modfile)
    if not dl_size:
        download=True
        logger.debug("%s %s"%(dl_size, file_size))
        logger.info("Unable to validate file %s, redownloading"%mod['name'])
    elif not file_size:
        download=True
        logger.debug("%s %s"%(dl_size, file_size))
        logger.info("File for %s does not exist; redownloading"%mod['name'])
    elif  dl_size != file_size:
        download=True
        logger.debug("%s %s"%(dl_size, file_size))
        logger.info("Failed to validate %s, redownloading"%mod['name'])
    if download:
        remove_file(modfile)
        if not download_mod(mod_dir, mod):
            return False
    return True

def download_mod(mod_dir, mod_data):
    filename=os.path.join(mod_dir, mod_filename(mod_data['name'],mod_data['version']))
    if not os.path.isfile(filename):
        if download_file(url=mod_data['download'], filename=filename):
            logger.info("Downloaded %s Version: %s, from %s"%(mod_data['name'],mod_data['version'], mod_data['download']))
        else:
            logger.error("Failed to download %s Version: %s, from %s"%(mod_data['name'],mod_data['version'], mod_data['download']))
            return False
    else:
        logger.debug("%s Version: %s, is already installed"%(mod_data['name'],mod_data['version']))
    return True

###################
#   Minecraft Section
###################
def get_minecraft_dir():
    return os.path.join(os.getenv('APPDATA'), ".minecraft")

def minecraft_is_installed():
    return os.path.isdir(get_minecraft_dir())

def create_mc_directories(minecraft_dir):
    if not os.path.isdir(os.path.join(minecraft_dir, 'versions')):
        os.mkdir(os.path.join(minecraft_dir, 'versions'))
    return os.path.join(minecraft_dir, 'versions')

def install_minecraft(minecraft_version):
    logger.info('Installing Minecraft %s'%minecraft_version)
    mc_version_dir=os.path.join(get_minecraft_dir(), 'versions', minecraft_version)
    minecraft_manifest_url="https://launchermeta.mojang.com/mc/game/version_manifest.json"

    if not os.path.isdir(mc_version_dir):
        os.makedirs(mc_version_dir)
    for version in download_json(minecraft_manifest_url)['versions']:
        if str(version['id']) == str(minecraft_version):
            if not ( os.path.isfile(os.path.join(mc_version_dir, filename_from_url(version['url']))) and os.path.isfile(os.path.join(mc_version_dir, "%s.jar"%minecraft_version)) ):
                logger.debug("Downloading Minecraft %s"%minecraft_version)
                save_json(os.path.join(mc_version_dir, filename_from_url(version['url'])), download_json(version['url']))
                version_json = open_json(os.path.join(mc_version_dir, filename_from_url(version['url'])))
                with open(os.path.join(mc_version_dir, "%s.jar"%minecraft_version), 'wb') as f:
                    f.write(download(version_json['downloads']['client']['url']))
                logger.debug('Minecraft Version: %s Installation Complete'%minecraft_version)
            else:
                logger.debug('Minecraft Version: %s already installed'%minecraft_version)

###################
#   Forge Section
###################
# Returns a tuple, Minecraft version will always be at index 0
def extract_mc_forge_versions(forge_version):
    versions = split_versions(forge_version)
    mc1_ver=r'^\d*[.]\d*[.]\d*'
    mc2_ver=r'^\d*[.]\d*'
    if re.match(r'^\d*[.]\d*[.]\d*[.]\d*', versions[0]):
        if re.match(mc1_ver, versions[1]) or re.match(mc2_ver, versions[1]):
            return versions[1], versions[0]
    elif re.match(r'^\d*[.]\d*[.]\d*[.]\d*', versions[1]):
        if re.match(mc1_ver, versions[0]) or re.match(mc2_ver, versions[0]):
            return versions[0], versions[1]
    return None, None

def is_forge_installed(forge_version):
    mc_dir=get_minecraft_dir()
    minecraft_version=extract_mc_forge_versions(forge_version)[0]
    forge_json = os.path.join(mc_dir, 'versions', minecraft_version+'-forge'+forge_version, minecraft_version+'-forge'+forge_version+'.json')
    forge_jar_paths=[os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(mc_ver)s-%(forge_ver)s"%({'mc_ver':minecraft_version, 'forge_ver':forge_version}), 'forge-%(mc_ver)s-%(forge_ver)s.jar'%({'mc_ver':minecraft_version, 'forge_ver':forge_version})),
                    os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(forge_ver)s"%({'forge_ver':forge_version}), 'forge-%(forge_ver)s.jar'%({'forge_ver':forge_version}))
                    ]
    for forge_jar in forge_jar_paths:
        if (os.path.isfile(forge_json) and os.path.isfile(forge_jar) ):
            return True
    return False

def download_forge(forge_version):
    forge_dl_urls=["https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar"%(forge_version, forge_version),
                    "https://files.minecraftforge.net/maven/net/minecraftforge/forge/%(mc_ver)s-%(forge_ver)s/forge-%(mc_ver)s-%(forge_ver)s-installer.jar"%({'mc_ver':extract_mc_forge_versions(forge_version)[0], 'forge_ver':forge_version})
                    ]
    forge_install_data=None
    for forge_dl_url in forge_dl_urls:
        try:
            logger.debug("Attempting to download forge %s Installer at %s"%(forge_version, forge_dl_urls))
            forge_install_data=download(forge_dl_url)
            if forge_install_data:
                logger.debug('Obtained Forge Installer!')
                return forge_install_data
        except Exception as e:
            continue
    logger.error("Failed to download Forge Installer!")
    return None

def get_forge_installer(forge_version, dir):
    logger.info('Downloading Forge %s Installer.'%forge_version)
    forge_installer=os.path.join(dir, "forge-%s-installer.jar"%forge_version)
    forge_installer_data = download_forge(forge_version)
    if forge_installer_data:
        save_file(forge_installer, forge_installer_data)
        return forge_installer
    return None

def get_forge_jar(forge_version):
    forge_ver_dir=os.path.join(get_minecraft_dir(), 'versions', extract_mc_forge_versions(forge_version)[0]+'-forge'+forge_version)
    for f in os.listdir(forge_ver_dir):
        if os.path.isfile(os.path.join(forge_ver_dir, f)):
            return os.path.splitext(f)[0]

def install_forge(forge_version):
    if is_forge_installed(forge_version):
        logger.debug("Minecraft Forge Version: %s is already installed"%forge_version)
        return  True
    logger.debug("Installing Minecraft Forge version: %s"%forge_version)
    dirpath = tempfile.mkdtemp()
    installer = get_forge_installer(forge_version, dirpath)
    success=False
    if installer:
        logger.info("Running Forge %s Installer"%forge_version)
        result = run(["java", "-jar", installer], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.debug("Forge Installer Exit Code:", result.returncode)
        logger.debug(result.stdout.decode('UTF-8'))
        success=True
    delete_directory(dirpath)
    if success:
        logger.debug('Forge %s installed'%forge_version)
        return True
    logger.error('Failed to install Forge %s'%forge_version)
    return False

###########
#   Launcher Profiles
###########
def get_profile_json():
    return open_json(os.path.join(get_minecraft_dir(), "launcher_profiles.json"))

def save_profile_json(profiledata):
    save_json(os.path.join(get_minecraft_dir(), "launcher_profiles.json"), profiledata)

def profile_is_installed(profile_name):
    if profile_name in get_profile_json():
        return True
    return False

def generate_profile_data(modpack, modpack_dir):
    timestamp=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return {'name':modpack['modpack_name'],
            'type':'custom',
            'created':timestamp,
            'lastUsed':timestamp,
            "lastVersionId":"%s"%str(get_forge_jar(modpack['forge'])),
            'javaArgs': "-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=16M",
            'gameDir':modpack_dir}

def insert_profile(profilename, profiledata):
    logger.info("Inserting %s into launcher profiles"%profilename)
    launcher=get_profile_json()
    if not profile_is_installed(profilename):
        launcher['profiles'][profilename]=profiledata
        save_profile_json(launcher)
        logger.debug("Inserted %s into launcher profiles."%profilename)
        return True
    return False

def remove_profile(profilename):
    logger.info("Removing %s from launcher profiles"%profilename)
    launcher=get_profile_json()
    if profile_is_installed(profilename):
        launcher['profiles'].pop(profilename, None)
        save_profile_json(launcher)
        logger.debug("Removed %s from launcher profiles."%profilename)
        return True
    return False

def update_profile(profile_data):
    launcher = get_profile_json()
    update=False
    for key, value in launcher['profiles'][profile_data['name']]:
        if (key == 'name' or key == 'lastVersionId') and profile_data[key] != launcher[key]:
            launcher[key] = profile_data[key]
            update=True
    if update:
        logger.info("Saving updated launcher profiles")
        save_profile_json(launcher)

def create_server_connection(modpack_info):
    logger.info('Creating Server connection file')
    server_dat_file=os.path.join(modpack_directory(modpack_info['modpack_name']), "servers.dat")
    logger.debug("Writing server connection file to %s"%server_dat_file)
    if os.path.isfile(server_dat_file):
        os.remove(server_dat_file)
    nbtfile = nbt.File({'':nbt.Compound({'servers':List[nbt.Compound]([nbt.Compound({'ip':String(modpack_info['server_address']), 'name': String(SERVERNAME)})])})})
    nbtfile.save(server_dat_file, gzipped=False)

###################
#   Modpack Sections
###################
def modpack_directory(modpack_name):
    return os.path.join(get_data_directory(), modpack_name)

def modpack_isInstalled(modpack):
    return os.path.isfile(os.path.join(modpack_directory(modpack[0]), modpack[0]))

def download_modpack_manifest(url):
    return download_json(url)

def install_configs(modpack_json):
    downloadExtact_zip(dir=os.path.join(modpack_directory(modpack_json['modpack_name']), 'config'), url=modpack_json['config_link'])

def create_modpack_directories(dir):
    make_directory(dir)
    make_directory(os.path.join(dir, 'mods'))
    make_directory(os.path.join(dir, 'config'))

def get_current_modpack_manifest(modpack):
    manifest_filename = os.path.join(modpack_directory(modpack[0]), str(filename_from_url(modpack[1])) )
    current_manifest=None
    if os.path.isfile(manifest_filename):
        current_manifest=open_json(manifest_filename)
    return current_manifest

def remove_old_mods(latest_modlist):
    logger.info('Removing old mods for modpack %s'%latest_json['modpack_name'])
    mod_dir =os.path.join(modpack_directory(latest_json['modpack_name']), "mods")
    for file in files_in_dir(mod_dir):
        splitname=split_mod_filename(file)
        remove=True
        for mod in latest_modlist:
            if mod['name'] == splitname[0] and mod['version'] == splitname[1]:
                remove=False
                break
        if remove:
            logger.info("Removing old mod file %s"%file)
            remove_file(os.path.join(mod_dir, file))

def install_mods(latest_json):
    logger.info('Installing mods for modpack %s'%latest_json['modpack_name'])
    mod_dir = os.path.join(modpack_directory(latest_json['modpack_name']), "mods")
    for mod in latest_json['modlist']:
        if not download_mod(mod_dir, mod):
            logging.error("Failed to download mod %s"%mod)

def install_modpack(latest_json):
    logger.info("Installing Modpack %s"%latest_json['modpack_name'])
    mod_dir=modpack_directory(latest_json['modpack_name'])
    create_modpack_directories(mod_dir)
    install_minecraft(extract_mc_forge_versions(latest_json['forge'])[0])
    install_forge(latest_json['forge'])
    install_configs(latest_json)
    install_mods(latest_json)
    insert_profile(latest_json['modpack_name'], generate_profile_data(latest_json, mod_dir))
    create_server_connection(latest_json)
    save_json(os.path.join(mod_dir, modpack[0]+'.json'), latest_json)

def uninstall_modpack(modpack):
    remove_profile(modpack[0])
    delete_directory(modpack_directory(modpack[0]))

def update_modpack(latest_json):
    mod_dir=modpack_directory(latest_json['modpack_name'])
    remove_old_mods(latest_json['modlist'])
    install_minecraft(extract_mc_forge_versions(latest_json['forge'])[0])
    install_forge(latest_json['forge'])
    install_configs(latest_json)
    install_mods(mod_dir, latest_json['modlist'])
    update_profile(generate_profile_data(latest_modlist['name'], mod_dir))

def validate_modpack(latest_json):
    mod_dir=os.path.join(modpack_directory(latest_json['modpack_name']), "mods")
    for mod in latest_json['modlist']:
        validate_mod_file(mod_dir, mod)

##########
#   Program tools
##########
def copy_program(data_dir):
    logger.debug("Copying program from %s to %s"%( sys.executable, os.path.join(data_dir, filename_from_path(sys.argv[0]).strip('.\/')) ))
    with open(os.path.join(data_dir, filename_from_path(sys.executable).strip('.\/')), "wb+") as f:
        logger.debug("Opened %s for writing"%os.path.join(data_dir, filename_from_path(sys.executable).strip('.\/')))
        with open(sys.argv[0],"rb") as o:
            logger.debug("Opened %s for reading"% sys.argv[0])
            f.write(o.read())
    logger.debug("Finished copying program")

def schedule(data_dir):
    logger.info('Scheduling Auto-Update!')
    if os.name == 'nt':
        logger.debug('Scheduling for windows')
        result = run(['schtasks.exe', '/QUERY', '/TN', '%s_Modpack_Manager'%SERVERNAME], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            logger.debug("Auto update was not scheduled, installing")
            with open(os.path.join(data_dir, 'autoupdate.cmd'), 'w+') as f:
                f.write('%s quiet update'%os.path.join(data_dir, filename_from_path(sys.executable).strip('.\/')))
            run("schtasks.exe /CREATE /SC ONLOGON /RU %(user)s /TN %(servername)s_Modpack_Manager /TR %(executable)s"%({'user':getpass.getuser(), 'servername':SERVERNAME, 'executable': os.path.join(data_dir, 'autoupdate.cmd')}), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            logger.debug("Auto update is already scheduled")
    #else:
        # result = run('crontab -l', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # if os.path.join(data_dir, __file__.strip('.\/')) in result.stdout:
        #     with open('tmpfile', 'w+') as f:
        #         f.write(result.stdout)
        #     run('crontab tmpfile', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #     os.remove('tmpfile')

def unschedule():
    logger.debug("Unscheduling AutoUpdate")
    if os.name == 'nt':
        result = run(['schtasks.exe', '/QUERY', '/TN', '%s_Modpack_Manager'%SERVERNAME], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if not result.returncode:
            logger.debug("Removing scheduled task")
            result = run("schtasks.exe /DELETE /F /TN %s_Modpack_Manager"%SERVERNAME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logger.debug("Delete Task Exit Code: %s, %s"%(result.returncode, result.stdout))
    #else:
        # result = run('crontab -l', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # if os.path.join(data_dir, __file__.strip('.\/')) in result.stdout:
        #     with open('tmpfile', 'w+') as f:
        #         f.write(result.stdout)
        #     run('crontab tmpfile', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #     os.remove('tmpfile')

class Installer(Frame):
    def __init__(self, data_dir, server):
        root=Tk()
        super().__init__(root)
        self.master = root
        #self.master.iconbitmap(os.path.join(os.getcwd(), 'rbg_mc.ico'))
        self.master.title("%s Modpack Manager"%server)
        self.master.protocol("WM_DELETE_WINDOW", self.onexit)
        self.data_dir=data_dir
        self.server=server
        self.value=None
        if self.isInstalled():
            self.uninstall=Button(self.master, text="Uninstall %s Modpack Manager"%self.server, command=partial(self.onButtonClick, value='uninstall')).grid(row=0, column=0, padx=10, pady=10)
            self.update=Button(self.master, text="Check for Updates", command=partial(self.onButtonClick, value='update')).grid(row=0, column=1, padx=10, pady=10)
        else:
            self.install=Button(self.master, text="Install %s Modpack Manager"%self.server, command=partial(self.onButtonClick, value='install')).grid(row=0, column=0, padx=10, pady=10)
        self.cancel=Button(self.master, text="Cancel", command=partial(self.onButtonClick, value='cancel')).grid(row=1, column=0, padx=10, pady=10)

    def run(self):
        self.master.mainloop()

    def return_value(self):
        return self.value

    def isInstalled(self):
        return os.path.isfile(os.path.join(self.data_dir, filename_from_path(sys.executable).strip('.\/')))

    def onButtonClick(self, value):
        self.value=value
        self.master.destroy()

    def onexit(self):
        self.onButtonClick('cancel')

def installer_gui():
    if not quiet:
        installer=Installer(data_directory, SERVERNAME)
        installer.run()
        return installer.return_value()
    logger.debug("Quiet installation")
    return action

def initilize_logger(directory, level = logging.INFO):
    logger = logging.getLogger('Modpack_Manager')
    logger.setLevel(level)
    fh = logging.FileHandler(os.path.join(directory, 'modpack-manager.log'))
    fh.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.debug("Logger Initialized")
    return logger

def manifest_filename():
    return os.path.join(set_data_directory_path(), str(filename_from_url(MANIFEST_URL)))

def get_current_manifest():
    if os.path.isfile(manifest_filename()):
        return open_json(manifest_filename())
    return None

############################################################
#   Entry Point
############################################################
# Do not edit, Modified when changes are made
VERSION="1.0.1"
DEBUG=False

if __name__ == "__main__":
    quiet=False
    action=''
    #Valid formats are installer.exe action or installer.exe quiet action
    #Check if quiet, grab action
    #TODO: Replace with argparse
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quiet':
            quiet=True
            action=sys.argv[2]
        else:
            action = sys.argv[1]

    # If we are just checking the version, catch and close quickly.
    if action == 'version':
        print("Kiln's Modpack Installer Version: %s"%VERSION)
        sys.exit(0)

    #DO NOT EDIT THESE VARIABLES
    DATA_DIR_NAME=".%s"%SERVERNAME
    data_directory = set_data_directory_path()
    make_directory(data_directory)
    #Initializeing Logger
    if DEBUG:
        logger = initilize_logger(data_directory, level=logging.DEBUG)
    else:
        logger = initilize_logger(data_directory)

    if not minecraft_is_installed():
        logger.error("ERROR!\nMinecraft has not been installed or the launcher has not been opened at least one time.\nPlease install Minecraft and open the launcher at least once.")
        Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nMinecraft has not been installed or the launcher has not been opened at least one time.\nPlease install Minecraft and open the launcher at least once.", 1)
        sys.exit(1)
    if not is_java_installed():
        logger.error("ERROR! Install Java from https://www.java.com/en/download/")
        Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nInstall Java from https://www.java.com/en/download/", 1)
        sys.exit(1)

    #No more configuration
    logger.debug("Arguments %s"%sys.argv)

    #This will only show the GUI to install, update, or uninstall
    logger.info("Running GUI Installer")
    action = installer_gui()
    logger.debug("Running as Administrator: %s"%is_admin())
    logger.debug("action: "+action)
    if action == 'install' and  data_directory != os.path.dirname(os.path.realpath(__file__)) :
        logger.info("Running Modpack Manager Installation.")
        if os.name == 'nt':
            if not quiet:
                copy_program(data_directory)
                logger.debug("Restarting as Administrator to schedule auto-update")
                if not restart_as_admin('install'):
                    logger.error("Failed to schedule")
                    Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nFailed to schedule auto-update", 1)
                    sys.exit(1)
            else:
                try:
                    schedule(data_directory)
                except:
                    logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
                    sys.exit(1)
                logger.info("Finished schedule")
                sys.exit(0)
        logger.debug("Finished installing initial setup")
    elif action == 'uninstall':
        if os.name == 'nt':
            if not quiet:
                logger.debug("Restarting as Administrator")
                if not restart_as_admin('uninstall'):
                    logger.error('Failed to uninstall')
                    Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nFailed to remove schedule", 1)
                    sys.exit(1)
                manifest = get_current_manifest()
                if manifest:
                    for modpack in manifest['modlist']:
                        uninstall_modpack(modpack)
                logging.shutdown()
                delete_directory(data_directory)
                Mbox('Related By Gaming Modpack Uninstaller', "Uninstallation is complete", 1)
                sys.exit(0)
            else:
                logger.info("Running Modpack Manager uninstall")
                try:
                    unschedule()
                    logging.shutdown()
                    delete_directory(data_directory)
                except:
                    logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
                    sys.exit(1)
        sys.exit(0)
    elif action == 'cancel':
        logger.info("User cancelled operation")
        sys.exit(0)

    #TODO, RUN MODPACK MANIPULATIONS HERE FOR MULTI_THREAD



    logger.info("Updating/Installing Modpacks")
    current_manifest = None
    try:
        # Download Latest manifest. Install/update modpacks
        latest_manifest = download_json(MANIFEST_URL)
        if not latest_manifest:
            logger.error("Failed to download manifest from %s"%MANIFEST_URL)
            sys.exit(1)
        else:
            modpacks=latest_manifest['modlist']
            logger.info('Checking %s modpacks'%len(modpacks))
            for modpack in modpacks:
                logger.debug('Installing modpack %s: %s'%(modpack[0], (not modpack_isInstalled(modpack[0]))) )
                #
                #Install Modpack Section
                #
                latest_modpack_manifest = download_modpack_manifest(modpack[1])
                current_modpack_manifest=get_current_modpack_manifest(modpack[0]) #get_current_modpack_manifest(os.path.join(modpack_dir, str(filename_from_url(modpack[1]))))

                if not modpack_isInstalled(modpack[0]):
                    install_modpack(latest_modpack_manifest)
                elif current_modpack_manifest and update_available(latest_modpack_manifest, current_modpack_manifest):
                    logger.debug('Updating modpack %s'%modpack[0])
                    update_modpack(latest_modpack_manifest)
                validate_modpack(latest_modpack_manifest)
                if current_modpack_manifest and update_available(latest_modpack_manifest, current_modpack_manifest):
                    save_json(os.path.join(modpack_dir, str(filename_from_url(modpack[1]))), latest_modpack_manifest)
            #
            # Save Manifest for uninstallation purposes
            #
            current_manifest = get_current_manifest()
            if current_manifest:
                if update_available(latest_manifest, current_manifest):
                    save_json(manifest_filename(), latest_manifest)
            else:
                save_json(manifest_filename(), latest_manifest)
                current_manifest = get_current_manifest()
    except :
        logger.error("%s %s"%(sys.exc_info()[0:1],traceback.extract_tb(sys.exc_info()[2])))
        input("Please contact an Administrator for help. Press Enter to continue.")
        sys.exit(1)
