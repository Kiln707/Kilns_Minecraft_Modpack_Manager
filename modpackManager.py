
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
import ctypes, datetime, getpass, json, logging, os, re, shutil, subprocess, sys, tempfile, time, traceback

def download(url=None):
    if not url:
        logger.debug('No URL')
        return None
    if not ( url.startswith('http://') or url.startswith('https://') ):
        url='http://'+url
    try:
        logger.debug('Downloading from %s'%url)
        response = request.urlopen(url)
        return response.read()
    except:
        return None

def filename_from_url(url=None):
    if url:
        pos=str(url).rfind('/')+1
        return str(url)[int(pos):]

def filename_from_path(path=None):
    if path:
        pos=str(path).rfind('\\')+1
        return str(path)[int(pos):]

def split_versions(version=''):
    if version:
        pos = str(version).rfind('-')
        return ( str(version)[:int(pos)], str(version)[int(pos+1):])

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

def mod_filename(modname, modversion):
    return "%s-%s.jar"%(modname,modversion)

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

def update_available(latest, current):
    if current:
        return float(latest['version']) > float(current['version'])
    return True

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

def remove_old_mods(modlist, mod_dir):
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

def modpack_isInstalled(modpack, data_dir):
    return os.path.isfile(os.path.join(data_dir, modpack[0], filename_from_url(modpack[1])))

def make_server_directory(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

def extract_mc_forge_versions(forge_version):
    versions = split_versions(forge_version)
    mc1_ver='\d*.\d*.\d*'
    mc2_ver='\d*.\d*'
    if re.match('\d*.\d*.\d*.\d*', versions[0]):
        if re.match(mc1_ver, versions[1]) or re.match(mc2_ver, versions[1]):
            return versions[1], versions[0]
    elif re.match('\d*.\d*.\d*.\d*', versions[1]):
        if re.match(mc1_ver, versions[0]) or re.match(mc2_ver, versions[0]):
            return versions[0], versions[1]
    return None, None


def make_modpack_directories(modpack, data_directory=''):
    if not os.path.isdir(os.path.join(data_directory, modpack)):
        os.mkdir(os.path.join(data_directory, modpack))
    if not os.path.isdir(os.path.join(data_directory, modpack, "mods")):
        os.mkdir(os.path.join(data_directory, modpack, "mods"))
    if not os.path.isdir(os.path.join(data_directory, modpack, 'config')):
        os.mkdir(os.path.join(data_directory, modpack, "config"))
    return os.path.join(data_directory, modpack)

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

def install_forge(forge_version, minecraft_version, mc_dir):
    forge_json=os.path.join(mc_dir, 'versions', minecraft_version+'-forge'+forge_version, minecraft_version+'-forge'+forge_version+'.json')
    forge_jar_paths=[os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(mc_ver)s-%(forge_ver)s"%({'mc_ver':minecraft_version, 'forge_ver':forge_version}), 'forge-%(mc_ver)s-%(forge_ver)s.jar'%({'mc_ver':minecraft_version, 'forge_ver':forge_version})),
                os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', "%(forge_ver)s"%({'forge_ver':forge_version}), 'forge-%(forge_ver)s.jar'%({'forge_ver':forge_version}))
                ]
    forge_dl_urls=["https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar"%(forge_version, forge_version),
                    "https://files.minecraftforge.net/maven/net/minecraftforge/forge/%(mc_ver)s-%(forge_ver)s/forge-%(mc_ver)s-%(forge_ver)s-installer.jar"%({'mc_ver':minecraft_version, 'forge_ver':forge_version})
                    ]
    for forge_jar in forge_jar_paths:
        if (os.path.isfile(forge_json) and os.path.isfile(forge_jar) ):
            logger.debug("Minecraft Forge Version: %s is already installed"%forge_version)
            return

    logger.debug("Installing Minecraft Forge version: %s"%forge_version)
    dirpath = tempfile.mkdtemp()
    forge_installer=os.path.join(dirpath, "forge-%s-installer.jar"%forge_version)
    forge_install_data=None
    for forge_dl_url in forge_dl_urls:
        try:
            forge_install_data=download(forge_dl_url)
        except:
            continue
    if not forge_install_data:
        logger.error("Failed to download Forge Installer!")
        exit(1)
    with open(forge_installer, 'wb') as f:
        f.write(forge_install_data)
        result = run(["java", "-jar", forge_installer], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logger.debug("Forge Installer Exit Code:", result.returncode)
        logger.debug(result.stdout.decode('UTF-8'))
    shutil.rmtree(dirpath)
    logger.debug('Forge %s installed'%forge_version)

def insert_launcher_info(modpack_info, data_dir, minecraft_dir, servername):
    forge_version=modpack_info['forge']
    minecraft_version, bleh=extract_mc_forge_versions(forge_version)
    profile_json=os.path.join(minecraft_dir, "launcher_profiles.json")
    profile = open_json(profile_json)
    timestamp=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    modpack_name=modpack_info['modpack_name']
    modpack_dir=os.path.join(data_directory, modpack_name)
    forge_ver_dir=os.path.join(minecraft_dir, 'versions', minecraft_version+'-forge'+forge_version)
    forge=''
    if not os.path.isdir(forge_ver_dir):
        logger.error("Forge was not installed!")
        exit(1)
    else:
        for f in os.listdir(forge_ver_dir):
            if os.path.isfile(os.path.join(forge_ver_dir, f)):
                forge, ext = os.path.splitext(f)

    modpack_profile = {'name':modpack_info['modpack_name'],
                        'type':'custom',
                        'created':timestamp,
                        'lastUsed':timestamp,
                        "lastVersionId":"%s"%str(forge),
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

def update_modpack(modpack, data_directory, servername):
    logger.info('Updating modpack %s'%modpack[0])
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    modpack_dir=make_modpack_directories(modpack[0], data_directory)
    mod_dir=os.path.join(modpack_dir, "mods")
    config_dir=os.path.join(modpack_dir, "config")
    latest_json=download_json(modpack[1])
    remove_old_mods(latest_json['modlist'], mod_dir)
    if os.path.isdir(config_dir):
        shutil.rmtree(config_dir)
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

def update_manifest(manifest_url, data_dir, manifest_filename):
    latest_manifest=download_json(manifest_url)
    current_manifest=None
    if os.path.isfile(manifest_filename):
        current_manifest=open_json(manifest_filename)
    if current_manifest:
        if update_available(latest_manifest, current_manifest):
            logger.info("Update is available, Updating modpacks!")
            save_json(manifest_filename, latest_manifest)
            remove_old_modpacks(manifest, data_dir)
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

if __name__ == "__main__":
    quiet=False
    action='install'
    if len(sys.argv) > 1 and sys.argv[1] == 'quiet':
        quiet=True
    if len(sys.argv) > 2:
        action=sys.argv[2]

    #os.path.join(os.path.dirname(os.path.realpath(__file__)), __file__.strip('.\/'))
    SERVERNAME='RelatedbyGaming'
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    if not os.path.isdir(minecraft_dir):
        logger.debug("ERROR! Please run Minecraft launcher before installing.")
        input("Press Enter to continue...")
        exit(1)
    #Editable Variables for installer
    MANIFEST_URL = "http://relatedbygaming.ddns.net/files/minecraft/rbg_mc.manifest"
    DATA_DIR_NAME=".%s"%SERVERNAME

    #No more configuration
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)

    if not os.path.isdir(data_directory):
        os.mkdir(data_directory)

    #Initializeing Logger
    logger = logging.getLogger('Modpack_Manager')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(data_directory, 'modpack-manager.log'))
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.debug("Logger Initialized")

    logger.debug("Arguments %s"%sys.argv)

    if ( not quiet and not is_admin()):
        logger.info("Running GUI Installer")
        action = run_installer()

    if action == 'install' and  data_directory != os.path.dirname(os.path.realpath(__file__)) :
        logger.info("Running Modpack Manager Installation.")
        if os.name == 'nt':
            if not is_admin():
                logger.debug("Restarting as Administrator")
                result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.argv[0], "quiet", '', 6)
                if not result>32:
                    logger.error("Failed to install modpack Manager")
                    exit(1)
            else:
                try:
                    make_server_directory(data_directory)
                    copy_program(data_directory)
                    schedule(data_directory)
                except:
                    logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
                exit(0)
        logging.debug("Finished installing")
    elif action == 'uninstall':
        if os.name == 'nt':
            if not is_admin():
                logger.debug("Restarting as Administrator")
                result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.argv[0], 'quiet uninstall', '', 6)
            else:
                logger.info("Running Modpack Manager uninstall")
                unschedule()
                uninstall_manifest(os.path.join(data_directory, str(filename_from_url(MANIFEST_URL))), data_directory)
                logging.shutdown()
                shutil.rmtree(data_directory)
        exit(0)
    elif action == 'cancel':
        logger.info("User cancelled operation")
        exit(0)
    logger.info("Updating/Installing Modpacks")
    manifest_filename=os.path.join(data_directory, str(filename_from_url(MANIFEST_URL)))
    manifest = None
    try:
        manifest = update_manifest(manifest_url=MANIFEST_URL, data_dir=data_directory, manifest_filename=manifest_filename)
    except :
        logger.error(sys.exc_info()[0:1], traceback.extract_tb(sys.exc_info()[2]))
        input("Please contact an Administrator for help. Press Enter to continue.")
    if not manifest:
        logger.debug("Failed to download manifest from %s"%MANIFEST_URL)
        exit(1)
