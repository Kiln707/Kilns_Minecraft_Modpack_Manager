from io import BytesIO
from itertools import product
from nbtlib import nbt, List, Compound, String
from subprocess import run
from tkinter import *
from zipfile import ZipFile
from multiprocessing import Process, Pool
import urllib.request as request
import json, os, tempfile, shutil, subprocess, subprocess, time, datetime, getpass, ctypes, sys
from functools import partial

def download(url=None):
    if not url:
        return None
    if not ( url.startswith('http://') or url.startswith('https://') ):
        url='http://'+url
    try:
        response = request.urlopen(url)
        return response.read()
    except:
        return None

def filename_from_url(url=None):
    if url:
        pos=str(url).rfind('/')+1
        return str(url)[int(pos):]

def downloadExtact_zip(dir, url=''):
    resp = download(url)
    zipfile = ZipFile(BytesIO(resp))
    zipfile.extractall(dir)
    print("Downloaded configs from %s"%url)

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
        with open(file_location,'w+') as file:
            json.dump(data, file)

def open_json(file_location=None):
    if file_location:
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
                available=True
                break
        if not available:
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
                if file == mod_filename(mod[0], mod[1]):
                    keep=True
                    break
            if not keep:
                os.remove(modfile)

def modpack_isInstalled(modpack, data_dir):
    return os.path.isfile(os.path.join(data_dir, modpack[0], filename_from_url(modpack[1])))

def make_server_directory(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

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
        print("Downloaded %s Version: %s, from %s"%(mod_data['name'],mod_data['version'], mod_data['download']))
    else:
        print("%s Version: %s, is already installed"%(mod_data['name'],mod_data['version']))

def create_mc_directories(minecraft_dir):
    if not os.path.isdir(os.path.join(minecraft_dir, 'versions')):
        os.mkdir(os.path.join(minecraft_dir, 'versions'))
    return os.path.join(minecraft_dir, 'versions')

def install_minecraft(minecraft_version, mc_dir):
    mc_version_dir=os.path.join(mc_dir, 'versions', minecraft_version)
    minecraft_manifest_url="https://launchermeta.mojang.com/mc/game/version_manifest.json"

    if not os.path.isdir(mc_version_dir):
        os.mkdir(mc_version_dir)
    for version in download_json(minecraft_manifest_url)['versions']:
        if str(version['id']) == str(minecraft_version):
            if not ( os.path.isfile(os.path.join(mc_version_dir, filename_from_url(version['url']))) and os.path.isfile(os.path.join(mc_version_dir, "%s.jar"%minecraft_version)) ):
                print("Downloading Minecraft %s"%minecraft_version)
                save_json(os.path.join(mc_version_dir, filename_from_url(version['url'])), download_json(version['url']))
                version_json = open_json(os.path.join(mc_version_dir, filename_from_url(version['url'])))
                with open(os.path.join(mc_version_dir, "%s.jar"%minecraft_version), 'wb') as f:
                    f.write(download(version_json['downloads']['client']['url']))
                print('Minecraft Version: %s Installation Complete'%minecraft_version)
            else:
                print('Minecraft Version: %s already installed'%minecraft_version)

def install_forge(forge_version, minecraft_version, mc_dir):
    forge_json=os.path.join(mc_dir, 'versions', minecraft_version+'-forge'+forge_version, minecraft_version+'-forge'+forge_version+'.json')
    forge_jar=os.path.join(mc_dir, 'libraries', 'net','minecraftforge','forge', forge_version, 'forge-'+forge_version+'.jar')
    forge_dl_url="https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar"%(forge_version, forge_version)

    if not (os.path.isfile(forge_json) and os.path.isfile(forge_jar) ):
        print("Installing Minecraft Forge version: %s"%forge_version)
        dirpath = tempfile.mkdtemp()
        forge_installer=os.path.join(dirpath, "forge-%s-installer.jar"%forge_version)
        with open(forge_installer, 'wb') as f:
            f.write(download(forge_dl_url))
            result = run(["java", "-jar", forge_installer], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print("Forge Installer Exit Code:", result.returncode)
            print(result.stdout.decode('UTF-8'))
        shutil.rmtree(dirpath)
        print('Forge installed')
    else:
        print("Minecraft Forge Version: %s is already installed"%forge_version)

def insert_launcher_info(modpack_info, data_dir, minecraft_dir, servername):
    forge_version=modpack_info['forge']
    minecraft_version=forge_version[:forge_version.rfind('-')]
    profile_json=os.path.join(minecraft_dir, "launcher_profiles.json")
    profile = open_json(profile_json)
    timestamp=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    modpack_name=modpack_info['modpack_name']
    modpack_profile = {'name':modpack_info['modpack_name'],
                        'type':'custom',
                        'created':timestamp,
                        'lastUsed':timestamp,
                        "lastVersionId":"%s-forge%s"%(minecraft_version, forge_version),
                        'gameDir':data_directory}

    profile['profiles'].pop(modpack_name, None)
    profile['profiles'][modpack_name]=modpack_profile
    save_json(profile_json, profile)
    #Servers.dat file section
    server_dat_file=os.path.join(data_directory, "servers.dat")
    if os.path.isfile(server_dat_file):
        os.remove(server_dat_file)
    nbtfile = nbt.File({'':nbt.Compound({'servers':List[nbt.Compound]([nbt.Compound({'ip':String(modpack_info['server_address']), 'name': String(servername)})])})})
    nbtfile.save(server_dat_file, gzipped=False)

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
    forge_version=modpack_json['forge']
    minecraft_version=forge_version[:forge_version.rfind('-')]

    processes.append(Process(target=install_minecraft, kwargs={'minecraft_version': minecraft_version, 'mc_dir': minecraft_dir}))
    processes.append(Process(target=install_forge, kwargs={'forge_version': forge_version, 'minecraft_version':minecraft_version,'mc_dir': minecraft_dir}))
    config_dl=None
    if modpack_json['config_link']:
        processes.append(Process(target=downloadExtact_zip, kwargs={'dir':config_dir, 'url':modpack_json['config_link']}))
    for process in processes:
        process.start()

    with Pool() as pool:
        pool.imap_unordered(install_mod_files, modpack_json['modlist'])
        pool.close()
        insert_launcher_info(modpack_info=modpack_json, data_dir=modpack_dir, minecraft_dir=minecraft_dir, servername=servername)
        pool.join()
    for process in processes:
        process.join()

def update_modpack(modpack, data_directory, servername):
        minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
        modpack_dir=make_modpack_directories(modpack[0], data_directory)
        mod_dir=os.path.join(modpack_dir, "mods")
        config_dir=os.path.join(modpack_dir, "config")
        latest_json=download_json(modpack[1])

        remove_old_mods(latest_json, mod_dir)
        if os.path.isdir(config_dir):
            shutil.rmtree(config_dir)
        install_modpack(modpack, data_directory, servername)

def uninstall_modpack(modpack_info, data_dir):
    print("Uninstalling modpack")
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
    print("Uninstalling manifest")
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
        result = run(['schtasks.exe', '/QUERY', '/TN', 'RBG_Modpack_Manager'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            with open(os.path.join(data_dir, 'autoupdate.cmd'), 'w+') as f:
                f.write('%s quiet update'%os.path.join(data_dir, __file__.strip('.\/')))
            run('schtasks.exe /CREATE /SC ONLOGON /RU '+getpass.getuser()+" /TN 'RBG_Modpack_Manager' /TR '%s'"%os.path.join(data_dir, 'autoupdate.cmd'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #else:
        # result = run('crontab -l', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # if os.path.join(data_dir, __file__.strip('.\/')) in result.stdout:
        #     with open('tmpfile', 'w+') as f:
        #         f.write(result.stdout)
        #     run('crontab tmpfile', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #     os.remove('tmpfile')

def unschedule():
    if os.name == 'nt':
        result = run(['schtasks.exe', '/QUERY', '/TN', '%s_Modpack_Manager'%SERVERNAME], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            run('schtasks.exe /DELETE /TN "%s_Modpack_Manager"'%SERVERNAME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #else:
        # result = run('crontab -l', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # if os.path.join(data_dir, __file__.strip('.\/')) in result.stdout:
        #     with open('tmpfile', 'w+') as f:
        #         f.write(result.stdout)
        #     run('crontab tmpfile', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #     os.remove('tmpfile')

def copy_program(data_dir):
    with open(os.path.join(data_dir, __file__.strip('.\/')), "wb+") as f:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), __file__.strip('.\/')), "rb") as o:
            f.write(o.read())

class Installer(Frame):
    def __init__(self, data_dir, server):
        root=Tk()
        super().__init__(root)
        self.master = root
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
        return os.path.isfile(os.path.join(self.data_dir, __file__.strip('.\/')))

    def onButtonClick(self, value):
        self.value=value
        self.master.destroy()

def run_installer():
    if not quiet:
        installer=Installer(data_directory, SERVERNAME)
        installer.run()
        return installer.return_value()
    return ''

if __name__ == "__main__":
    print(sys.argv)
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
        print("ERROR! Please run Minecraft launcher before installing.")
        exit(1)
    #Editable Variables for installer
    MANIFEST_URL = "http://relatedbygaming.ddns.net/files/rbgtest.manifest"
    DATA_DIR_NAME=".%s"%SERVERNAME

    #No more configuration
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)

    if ( not quiet and not is_admin()):
        action = run_installer()

    if action == 'install' and  data_directory != os.path.dirname(os.path.realpath(__file__)) :
        if os.name == 'nt' and not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, 'quiet', 1)
            exit(0)
        make_server_directory(data_directory)
        copy_program(data_directory)
        schedule(data_directory)
    elif action == 'uninstall':
        unschedule()
        uninstall_manifest(os.path.join(data_directory, str(filename_from_url(MANIFEST_URL))), data_directory)
        shutil.rmtree(data_directory)
        exit(0)
    elif action == 'cancel':
        exit(0)

    manifest_filename=os.path.join(data_directory, str(filename_from_url(MANIFEST_URL)))
    manifest = update_manifest(manifest_url=MANIFEST_URL, data_dir=data_directory, manifest_filename=manifest_filename)
    if not manifest:
        exit(1)
