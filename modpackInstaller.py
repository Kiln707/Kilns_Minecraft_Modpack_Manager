
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
        print(e.code)
        print(e.read())
    except URLError as e:
        print(e.read().decode("utf8", 'ignore'))
    except Exception as e:
        print(type(e))
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
    with open(filename, "wb+") as f:
        f.write(download(url))

def download_file_size(url):
    site = urllib.urlopen(link)
    meta = site.info()
    return int(meta.getheaders("Content-Length")[0])

def get_file_size(filename):
    if os.path.isfile(filename):
        return os.path.getsize(filename)
    return 0

def save_file(file_location, data):
    with open(file_location, 'w+') as file:
        file.write(forge_install_data)

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

#
#   DEPRECIATED
#
def get_latest_json(url=None, file_location=None):
    latest_json = download_json(url)
    if latest_json:
        current_json={}
        if os.path.isfile(file_location):
            current_json = open_json(file_location)
        if not current_json or float(latest_json['version']) > float(current_json['version']):
            save_json(file_location, latest_json)
            return latest_json
        return current_json
    else:
        return None

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
    if download_file_size(mod['download']) != get_file_size(modfile):
        remove_file(modfile)
        download_mod(mod_dir, mod)

def download_mod(mod_dir, mod_data):
    filename=os.path.join(mod_dir, mod_filename(mod_data['name'],mod_data['version']))
    if not os.path.isfile(filename):
        download_file(url=mod_data['download'], filename=filename)
        logger.debug("Downloaded %s Version: %s, from %s"%(mod_data['name'],mod_data['version'], mod_data['download']))
    else:
        logger.debug("%s Version: %s, is already installed"%(mod_data['name'],mod_data['version']))

###################
#   Minecraft Section
###################
def install_minecraft(minecraft_version, mc_dir):
    mc_version_dir=os.path.join(mc_dir, 'versions', minecraft_version)
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
def extract_mc_forge_versions(forge_version):
    versions = split_versions(forge_version)
    mc1_ver=r'^\d*[.]\d*[.]\d*'
    mc2_ver=r'^\d*[.]\d*'
    if re.match(r'^\d*[.]\d*[.]\d*[.]\d*', versions[0]):
        print(re.match(r'^\d*[.]\d*[.]\d*[.]\d*', versions[0]), versions[0])
        if re.match(mc1_ver, versions[1]) or re.match(mc2_ver, versions[1]):
            return versions[1], versions[0]
    elif re.match(r'^\d*[.]\d*[.]\d*[.]\d*', versions[1]):
        if re.match(mc1_ver, versions[0]) or re.match(mc2_ver, versions[0]):
            return versions[0], versions[1]
    return None, None

def is_forge_installed(forge_ver, minecraft_ver, mc_dir):
    forge_jar_paths=[os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(mc_ver)s-%(forge_ver)s"%({'mc_ver':minecraft_version, 'forge_ver':forge_version}), 'forge-%(mc_ver)s-%(forge_ver)s.jar'%({'mc_ver':minecraft_version, 'forge_ver':forge_version})),
                    os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(forge_ver)s"%({'forge_ver':forge_version}), 'forge-%(forge_ver)s.jar'%({'forge_ver':forge_version}))
                    ]
    for forge_jar in forge_jar_paths:
        if (os.path.isfile(forge_json) and os.path.isfile(forge_jar) ):
            return True
    return False

def download_forge(forge_version, minecraft_version):
    forge_dl_urls=["https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar"%(forge_version, forge_version),
                    "https://files.minecraftforge.net/maven/net/minecraftforge/forge/%(mc_ver)s-%(forge_ver)s/forge-%(mc_ver)s-%(forge_ver)s-installer.jar"%({'mc_ver':minecraft_version, 'forge_ver':forge_version})
                    ]
    forge_install_data=None
    for forge_dl_url in forge_dl_urls:
        try:
            logger.debug("Attempting to download forge %s Installer at %s"%(forge_version, forge_dl_urls))
            forge_install_data=download(forge_dl_url)
            if forge_install_data:
                return forge_install_data
        except Exception as e:
            print(e)
            continue
    logger.error("Failed to download Forge Installer!")
    return None

def get_forge_installer(forge_version, minecraft_version, dir):
    forge_installer=os.path.join(dir, "forge-%s-installer.jar"%forge_version)
    forge_installer_data = download_forge(forge_version, minecraft_version)
    if forge_installer_data:
        save_file(forge_installer, forge_installer_data)
        return forge_installer
    return None

def install_forge(forge_version, minecraft_version, mc_dir):
    if is_forge_installed(forge_version, minecraft_version, mcdir):
        logger.debug("Minecraft Forge Version: %s is already installed"%forge_version)
        return  True
    logger.debug("Installing Minecraft Forge version: %s"%forge_version)
    dirpath = tempfile.mkdtemp()
    installer = get_forge_installer(forge_version, minecraft_version, dirpath)
    success=False
    if installer:
        result = run(["java", "-jar", forge_installer], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.debug("Forge Installer Exit Code:", result.returncode)
        logger.debug(result.stdout.decode('UTF-8'))
        success=True
    shutil.rmtree(dirpath)
    if success
        logger.debug('Forge %s installed'%forge_version)
        return True
    logger.error('Failed to install Forge %s'%forge_version)

###################
#   Modpack Sections
###################
def modpack_isInstalled(modpack, data_dir):
    return os.path.isfile(os.path.join(data_dir, modpack[0], filename_from_url(modpack[1])))

def download_modpack_manifest(url):
    return download_json(url)

def get_current_modpack_manifest(manifest_filename):
    current_manifest=None
    if os.path.isfile(manifest_filename):
        current_manifest=open_json(manifest_filename)
    return current_manifest

def remove_old_mods(latest_modlist, mod_dir):
    for file in files_in_dir(mod_dir):
        splitname=split_mod_filename(file)
        remove=True
        for mod in latest_modlist:
            if mod['name'] == splitname[0] and mod['version'] == splitname[1]:
                remove=False
                break
        remove_file(os.path.join(mod_dir, file))

def install_mods(mod_dir, mod_list):
    for mod in modlist:
        download_mod(mod_dir, mod)

def update_modpack(latest_json, current_json, data_directory):
    mod_dir=os.path.join(data_directory,'mods')
    remove_old_mods(latest_json['modlist'], mod_dir)
    install_mods(mod_dir, latest_json['modlist'])

def validate_modpack(latest_json, data_directory):
    mod_dir=os.path.join(data_directory,'mods')
    for mod in latest_json['modlist']:
        validate_mod_file(mod_dir, mod)




#
#   DEPRECIATED
def remove_old_modpacks(manifest, data_dir):
    installed_modpacks=[ item for item in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, item)) ]
    for Imodpack in installed_modpacks:
        available=False
        for modpack in manifest['modlist']:
            if Imodpack == modpack[0]:
                logger.info("Keeping modpack %s"%Imodpack)
                available=True
                break
        if not available:
            logger.info("deleting modpack %s"%Imodpack)
            shutil.rmtree(os.path.join(data_dir, Imodpack))

#
#   DEPRECIATED
#
def depreciated_remove_old_mods(modlist, mod_dir):
    moddirlist=os.listdir(mod_dir)
    for dir in moddirlist:
        if os.path.isdir(os.path.join(mod_dir, dir)):
            shutil.rmtree(os.path.join(mod_dir, dir))
    for file in moddirlist:
        modfile=os.path.join(mod_dir, file)
        if os.path.isfile(modfile):
            keep=False
            for mod in modlist:
                if file == mod_filename(mod['name'], mod['version']):
                    logger.info("Match found! %s still in modpack."%file)
                    keep=True
                    break
            if not keep:
                logger.info("Removing %s, no longer in modpack"%file)
                os.remove(modfile)







def make_modpack_directories(modpack, data_directory=''):
    if not os.path.isdir(os.path.join(data_directory, modpack)):
        os.mkdir(os.path.join(data_directory, modpack))
    if not os.path.isdir(os.path.join(data_directory, modpack, "mods")):
        os.mkdir(os.path.join(data_directory, modpack, "mods"))
    if not os.path.isdir(os.path.join(data_directory, modpack, 'config')):
        os.mkdir(os.path.join(data_directory, modpack, "config"))
    return os.path.join(data_directory, modpack)

#
#   DEPRECIATED
#
def install_mod_files(mod_data):
    filename=os.path.join(mod_data['dir'], mod_filename(mod_data['name'],mod_data['version']))
    if not os.path.isfile(filename):
        download_file(url=mod_data['download'], filename=filename)
        logger.debug("Downloaded %s Version: %s, from %s"%(mod_data['name'],mod_data['version'], mod_data['download']))
    else:
        logger.debug("%s Version: %s, is already installed"%(mod_data['name'],mod_data['version']))

def create_mc_directories(minecraft_dir):
    if not os.path.isdir(os.path.join(minecraft_dir, 'versions')):
        os.mkdir(os.path.join(minecraft_dir, 'versions'))
    return os.path.join(minecraft_dir, 'versions')

###########
#   Launcher Profiles
###########
def get_profile_json():

def profile_is_installed(modpack):
    if




def insert_launcher_info(modpack_info, data_dir, minecraft_dir, servername):
    forge_version=modpack_info['forge']
    minecraft_version=extract_mc_forge_versions(forge_version)[0]
    profile_json=os.path.join(minecraft_dir, "launcher_profiles.json")
    profile = open_json(profile_json)
    timestamp=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    modpack_name=modpack_info['modpack_name']
    modpack_dir=os.path.join(data_directory, modpack_name)
    forge_ver_dir=os.path.join(minecraft_dir, 'versions', minecraft_version+'-forge'+forge_version)
    forge=''
    # if not os.path.isdir(forge_ver_dir):
    #     logger.error("Forge was not installed!")
    #     exit(1)
    # else:
    for f in os.listdir(forge_ver_dir):
        if os.path.isfile(os.path.join(forge_ver_dir, f)):
            forge, ext = os.path.splitext(f)

    modpack_profile = {'name':modpack_info['modpack_name'],
                        'type':'custom',
                        'created':timestamp,
                        'lastUsed':timestamp,
                        "lastVersionId":"%s"%str(forge),
                        'javaArgs': "-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=16M",
                        'gameDir':modpack_dir}
    profile['profiles'].pop(modpack_name, None)
    profile['profiles'][modpack_name]=modpack_profile
    logger.info("Installed profile for %s"%modpack_name)
    logger.debug("Installed %s"%str(modpack_profile))
    save_json(profile_json, profile)
    #Servers.dat file section
    server_dat_file=os.path.join(data_directory, modpack_name, "servers.dat")
    logger.debug("Writing server connection file to %s"%server_dat_file)
    if os.path.isfile(server_dat_file):
        os.remove(server_dat_file)
    nbtfile = nbt.File({'':nbt.Compound({'servers':List[nbt.Compound]([nbt.Compound({'ip':String(modpack_info['server_address']), 'name': String(servername)})])})})
    nbtfile.save(server_dat_file, gzipped=False)
    logger.info("Created server connection")

def append_modDir(modpack_json, mod_dir):
    for modinfo in modpack_json['modlist']:
        modinfo['dir']=mod_dir
    return modpack_json

def install_modpack(modpack, data_directory='', servername=''):
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    modpack_dir=make_modpack_directories(modpack[0], data_directory)
    mod_dir=os.path.join(modpack_dir, "mods")
    config_dir=os.path.join(modpack_dir, "config")
    modpack_json=append_modDir(get_latest_json(url=modpack[1],file_location=os.path.join(modpack_dir, filename_from_url(modpack[1]))), mod_dir)
    processes=[]
    minecraft_version, blah=extract_mc_forge_versions(modpack_json['forge'])
    forge_version=modpack_json['forge']

    install_minecraft(minecraft_version, minecraft_dir)
    install_forge(forge_version, minecraft_version, minecraft_dir)
    downloadExtact_zip(dir=config_dir, url=modpack_json['config_link'])

    # processes.append(Process(target=install_minecraft, kwargs={'minecraft_version': minecraft_version, 'mc_dir': minecraft_dir}))
    # processes.append(Process(target=install_forge, kwargs={'forge_version': forge_version, 'minecraft_version':minecraft_version,'mc_dir': minecraft_dir}))
    # config_dl=None
    # if modpack_json['config_link']:
    #     processes.append(Process(target=downloadExtact_zip, kwargs={'dir':config_dir, 'url':modpack_json['config_link']}))
    # for process in processes:
    #    process.start()
    for mod in modpack_json['modlist']:
        install_mod_files(mod)
    insert_launcher_info(modpack_info=modpack_json, data_dir=modpack_dir, minecraft_dir=minecraft_dir, servername=servername)

    # with Pool() as pool:
    #     pool.imap_unordered(install_mod_files, modpack_json['modlist'])
    #     pool.close()
    #     insert_launcher_info(modpack_info=modpack_json, data_dir=modpack_dir, minecraft_dir=minecraft_dir, servername=servername)
    #     pool.join()
    # for process in processes:
    #     process.join()

#
#   DEPRECIATED
#
def depreciated_update_modpack(modpack, data_directory, servername):
    logger.info('Updating modpack %s'%modpack[0])
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    modpack_dir=make_modpack_directories(modpack[0], data_directory)
    mod_dir=os.path.join(modpack_dir, "mods")
    config_dir=os.path.join(modpack_dir, "config")
    json_filename=os.path.join(modpack_dir, str(filename_from_url(modpack[1])))
    latest_json=download_json(modpack[1])
    current_json=None
    if os.path.isfile(json_filename):
        current_json = open_json(json_filename)
    if current_json:
        if update_available(latest_json, current_json):
            logger.info("Update is available for %s"%modpack[0])
            remove_old_mods(latest_json['modlist'], mod_dir)
            if os.path.isdir(config_dir):
                shutil.rmtree(config_dir)
        else:
            logger.info("No update available for %s"%modpack[0])
            return
    else:
        logger.info("%s not installed. Installing."%modpack[0])
        save_json(json_filename, latest_json)
    install_modpack(modpack, data_directory, servername)

def uninstall_modpack(modpack_info, data_dir):
    logger.info("Uninstalling modpack %s"%modpack_info[0])
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    modpack_dir=os.path.join(data_dir, modpack_info[0])
    json_filename=os.path.join(modpack_dir, filename_from_url(modpack_info[1]))
    profile_json=os.path.join(minecraft_dir, "launcher_profiles.json")
    json = open_json(json_filename)
    if json:
        modpack_name=json['modpack_name']
        profile = open_json(profile_json)
        profile['profiles'].pop(modpack_name, None)
        save_json(profile_json, profile)

def uninstall_manifest(manifest_filename, data_dir):
    manifest = open_json(manifest_filename)
    logger.debug("Uninstalling manifest")
    if manifest:
        for modpack in manifest['modlist']:
            uninstall_modpack(modpack, data_dir)

def get_latest_manifest(manifest_url):
    return download_json(manifest_url)



##
#   DEPRECIATED !
##
def update_manifest(manifest_url, data_dir, manifest_filename):
    latest_manifest=download_json(manifest_url)
    current_manifest=None
    if os.path.isfile(manifest_filename):
        current_manifest=open_json(manifest_filename)
    if current_manifest:
        if update_available(latest_manifest, current_manifest):
            logger.info("Update is available, Updating modpacks!")
            save_json(manifest_filename, latest_manifest)
            remove_old_modpacks(latest_manifest, data_dir)
    else:
        save_json(manifest_filename, latest_manifest)
    for modpack in latest_manifest['modlist']:
        if modpack_isInstalled(modpack, data_dir):
            update_modpack(modpack, data_dir, latest_manifest['server'])
        else:
            make_modpack_directories(modpack[0], data_directory=data_dir)
            install_modpack(modpack, data_dir, latest_manifest['server'])
    return latest_manifest

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

def schedule(data_dir):
    if os.name == 'nt':
        result = run(['schtasks.exe', '/QUERY', '/TN', '%s_Modpack_Manager'%SERVERNAME], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            logger.debug("Auto update was not scheduled, installing")
            with open(os.path.join(data_dir, 'autoupdate.cmd'), 'w+') as f:
                f.write('%s quiet update'%os.path.join(data_dir, filename_from_path(sys.argv[0]).strip('.\/')))
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

def copy_program(data_dir):
    logger.debug("Copying program from %s to %s"%( sys.argv[0], os.path.join(data_dir, filename_from_path(sys.argv[0]).strip('.\/')) ))
    with open(os.path.join(data_dir, filename_from_path(sys.argv[0]).strip('.\/')), "wb+") as f:
        logger.debug("Opened %s for writing"%os.path.join(data_dir, filename_from_path(sys.argv[0]).strip('.\/')))
        with open(sys.argv[0],"rb") as o:
            logger.debug("Opened %s for reading"% sys.argv[0])
            f.write(o.read())
    logger.debug("Finished copying program")

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
        return os.path.isfile(os.path.join(self.data_dir, filename_from_path(sys.argv[0]).strip('.\/')))

    def onButtonClick(self, value):
        self.value=value
        self.master.destroy()

    def onexit(self):
        self.onButtonClick('cancel')

def run_installer():
    if not quiet:
        installer=Installer(data_directory, SERVERNAME)
        installer.run()
        return installer.return_value()
    logger.debug("Quiet installation")
    return ''

def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def initilize_logger(directory):
    logger = logging.getLogger('Modpack_Manager')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(directory, 'modpack-manager.log'))
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.debug("Logger Initialized")
    return logger

def minecraft_req_met():
    return os.path.isdir(minecraft_dir)

def set_data_directory_path(directory_name):
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)
    return data_directory



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

if __name__ == "__main__":
    quiet=False
    action=''
    if len(sys.argv) > 1 and sys.argv[1] == 'quiet':
        quiet=True
    if len(sys.argv) > 2:
        action=sys.argv[2]


    #Editable Variables for installer
    SERVERNAME='RelatedbyGaming'
    MANIFEST_URL = "http://relatedbygaming.ddns.net/files/minecraft/rbg_mc.manifest"

    #DO NOT EDIT THESE VARIABLES
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    DATA_DIR_NAME=".%s"%SERVERNAME
    data_directory = set_data_directory_path(DATA_DIR_NAME)
    make_server_directory(data_directory)
    #Initializeing Logger
    logger = initilize_logger(data_directory)

    if not minecraft_req_met():
        logger.error("ERROR!\nMinecraft has not been installed or the launcher has not been opened at least one time.\nPlease install Minecraft and open the launcher at least once.")
        Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nMinecraft has not been installed or the launcher has not been opened at least one time.\nPlease install Minecraft and open the launcher at least once.", 1)
        exit(1)
    if not is_java_installed():
        logger.error("ERROR! Install Java from https://www.java.com/en/download/")
        Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nInstall Java from https://www.java.com/en/download/", 1)
        exit(1)

    #No more configuration
    logger.debug("Arguments %s"%sys.argv)

    #This will only show the GUI to install, update, or uninstall
    logger.info("Running GUI Installer")
    action = run_installer()

    if action == 'install' and  data_directory != os.path.dirname(os.path.realpath(__file__)) :
        logger.info("Running Modpack Manager Installation.")
        if os.name == 'nt':
            logger.debug(is_admin())
            if not is_admin():
                copy_program(data_directory)
                logger.debug("Restarting as Administrator to schedule auto-update")
                if not restart_as_admin('install'):
                    logger.error("Failed to schedule")
                    Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nFailed to schedule auto-update", 1)
                    exit(1)
            else:
                try:
                    schedule(data_directory)
                except:
                    logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
                    exit(1)
                exit(0)
        logging.debug("Finished installing initial setup")
    elif action == 'uninstall':
        if os.name == 'nt':
            if not is_admin():
                logger.debug("Restarting as Administrator")
                if not restart_as_admin('uninstall'):
                    logging.error('Failed to uninstall')
                    Mbox('Related By Gaming Modpack Installer | ERROR', "ERROR!\nFailed to remove schedule", 1)
                    exit(1)
                uninstall_manifest(os.path.join(data_directory, str(filename_from_url(MANIFEST_URL))), data_directory)
                logging.shutdown()
                shutil.rmtree(data_directory)
            else:
                logger.info("Running Modpack Manager uninstall")
                try:
                    unschedule()
                except:
                    logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
                    exit(1)
        exit(0)
    elif action == 'cancel':
        logger.info("User cancelled operation")
        exit(0)

    #TODO, RUN MODPACK MANIPULATIONS HERE FOR MULTI_THREAD



    logger.info("Updating/Installing Modpacks")
    manifest_filename=os.path.join(data_directory, str(filename_from_url(MANIFEST_URL)))
    manifest = None
    try:
        # Download Latest manifest. Install/update modpacks
        latest_manifest = get_latest_manifest(MANIFEST_URL)
        for modpack in latest_manifest['modlist']:
            #
            #Install Modpack Section
            #
            modpack_dir = make_modpack_directories(modpack[0], data_directory=data_directory)
            latest_modpack_manifest = download_modpack_manifest(modpack[1])
            current_modpack_manifest= get_current_modpack_manifest(os.path.join(modpack_dir, str(filename_from_url(modpack[1]))))
            if current_modpack_manifest and update_available(latest_modpack_manifest, current_modpack_manifest):
                update_modpack(latest_modpack_manifest, current_modpack_manifest, modpack_dir)
            validate_modpack(latest_modpack_manifest, modpack_dir)
            if current_modpack_manifest and update_available(latest_modpack_manifest, current_modpack_manifest):
                save_json(os.path.join(modpack_dir, str(filename_from_url(modpack[1]))), latest_modpack_manifest)
        #
        # Save Manifest for uninstallation purposes
        #
        current_manifest=None
        if os.path.isfile(manifest_filename):
            current_manifest=open_json(manifest_filename)
        if current_manifest:
            if update_available(latest_manifest, current_manifest):
                save_json(manifest_filename, latest_manifest)
        else:
            save_json(manifest_filename, latest_manifest)
    except :
        logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
        input("Please contact an Administrator for help. Press Enter to continue.")
        exit(1)
    if not manifest:
        logger.debug("Failed to download manifest from %s"%MANIFEST_URL)
        exit(1)
