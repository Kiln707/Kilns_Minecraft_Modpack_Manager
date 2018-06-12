from io import BytesIO
from itertools import product
from nbtlib import nbt
from subprocess import run
from tkinter import *
from zipfile import ZipFile
from multiprocessing import Process, Pool
import json
import urllib.request as request
import os
import tempfile
import shutil
import subprocess

import time, datetime

def download(url=None):
    if not url:
        return None
    try:
        response = request.urlopen(url)
        return response.read()
    except:
        return None

def filename_from_url(url=None):
    if url:
        pos=str(url).rfind('/')+1
        return str(url)[int(pos):]

def download_json(url=None):
    data = download(url)
    if data:
        return json.loads(data.decode('utf-8'))
    return None

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

def make_modpack_directories(modpack, data_directory=''):
    if not modpack_isInstalled(modpack, data_directory):
        os.mkdir(os.path.join(data_directory, modpack[0]))
    if not os.path.isdir(os.path.join(data_directory, modpack[0], "mods")):
        os.mkdir(os.path.join(data_directory, modpack[0], "mods"))
    if not os.path.isdir(os.path.join(data_directory, modpack[0], 'config')):
        os.mkdir(os.path.join(data_directory, modpack[0], "config"))
    return os.path.join(data_directory, modpack[0])

def install_config_files(config_dir, url=''):
    resp = download(url)
    zipfile = ZipFile(BytesIO(resp))
    zipfile.extractall(config_dir)
    print("Downloaded configs from %s"%url)

def install_mod_files(mod_data):
    with open(os.path.join(mod_data[4], "%s-%s.jar"%(mod_data[0],mod_data[1])), "wb+") as f:
        f.write(download(mod_data[3]))
    print("Downloaded %s, Version: %s, from %s"%(mod_data[0], mod_data[1], mod_data[3]))

def install_minecraft_forge(forge_version):
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    minecraft_version=forge_version[:forge_version.rfind('-')]
    mc_version_dir=os.path.join(minecraft_dir, 'versions', minecraft_version)
    minecraft_manifest_url="https://launchermeta.mojang.com/mc/game/version_manifest.json"
    forge_dl_url="https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar"%(forge_version, forge_version)
    if not os.path.isdir(os.path.join(minecraft_dir, 'versions')):
        os.mkdir(os.path.join(minecraft_dir, 'versions'))
    if not os.path.isdir(mc_version_dir):
        os.mkdir(mc_version_dir)
    print("Downloading Minecraft %s"%minecraft_version)
    for version in download_json(minecraft_manifest_url)['versions']:
        if str(version['id']) == str(minecraft_version):
            save_json(os.path.join(mc_version_dir, filename_from_url(version['url'])), download_json(version['url']))
            break
    version_json = open_json(os.path.join(mc_version_dir, filename_from_url(version['url'])))
    with open(os.path.join(mc_version_dir, "%s.jar"%minecraft_version), 'wb') as f:
        f.write(download(version_json['downloads']['client']['url']))
    print('Minecraft download complete')
    print('Downloading and installing forge')
    dirpath = tempfile.mkdtemp()
    forge_installer=os.path.join(dirpath, "forge-%s-installer.jar"%forge_version)
    with open(forge_installer, 'wb') as f:
        f.write(download(forge_dl_url))
        result = run(["java", "-jar", forge_installer], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("Forge Installer Exit Code:", result.returncode)
        print(result.stdout.decode('UTF-8'))
    shutil.rmtree(dirpath)
    print('Forge installed')

def update_launcher(modpack_info, data_directory):
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    forge_version=modpack_info['forge']
    minecraft_version=forge_version[:forge_version.rfind('-')]
    profile_json=os.path.join(minecraft_dir, "launcher_profiles.json")
    profile = open_json(profile_json)
    timestamp=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    modpack_profile = {'name':modpack_info['modpack_name'],
                        'type':'custom',
                        'created':timestamp,
                        'lastUsed':timestamp,
                        "lastVersionId":"%s-forge%s"%(minecraft_version, forge_version),
                        'gameDir':data_directory}
    profile['profiles'][modpack_info['modpack_name']]=modpack_profile
    save_json(profile_json, profile)
    server_data={'':{'servers':[{'ip':'relatedbygaming.ddns.net:25555', 'name':'modpack'}]}}
    nbtfile = nbt.load(os.path.join(data_directory, "servers.dat"))
    print(nbtfile)

def install_modpack(modpack, data_directory=''):
    modpack_dir=make_modpack_directories(modpack, data_directory)
    mod_dir=os.path.join(modpack_dir, "mods")
    config_dir=os.path.join(modpack_dir, "config")
    modpack_json=get_latest_json(url=modpack[1],file_location=os.path.join(modpack_dir, filename_from_url(modpack[1])))
    forge_install=Process(target=install_minecraft_forge, kwargs={'forge_version': modpack_json['forge']})
    forge_install.start()
    config_dl=None
    if modpack_json['config_link']:
        config_dl=Process(target=install_config_files, kwargs={'config_dir':config_dir, 'url':modpack_json['config_link']})
        config_dl.start()
#    modlist = modpack_json['modlist']
    for modinfo in modpack_json['modlist']:
        modinfo.append(mod_dir)
    with Pool() as pool:
        pool.imap_unordered(install_mod_files, modpack_json['modlist'])
        pool.close()
        update_launcher(modpack_info=modpack_json, data_directory=modpack_dir)
        pool.join()
    if config_dl:
        config_dl.join()
    forge_install.join()

def modpack_isInstalled(modpack, data_directory=''):
    return os.path.isdir(os.path.join(data_directory, modpack[0]))

def update_available(modpack, data_directory=''):
    latest_json = download_json(modpack[1])
    if latest_json:
        jsondata={}
        modpack_json = os.path.join(data_directory, filename_from_url(modpack[1]))
        if os.path.isfile(modpack_json):
            jsondata = open_json(modpack_json)
        if not jsondata or float(latest_json['version']) > float(jsondata['version']):
            return True
        return False
    else:
        return None

if __name__ == "__main__":
    minecraft_dir=os.path.join(os.getenv('APPDATA'), ".minecraft")
    if not os.path.isdir(minecraft_dir):
        print("ERROR! Please run Minecraft launcher before installing.")
        exit(1)
    #Editable Variables for installer
    MANIFEST_URL = "http://relatedbygaming.ddns.net/files/rbgtest.manifest"
    DATA_DIR_NAME=".RelatedByGaming"

    #No more configuration
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)

    manifest_filename=os.path.join(data_directory, str(filename_from_url(MANIFEST_URL)))
    manifest = get_latest_json(url=MANIFEST_URL, file_location=manifest_filename)
    if not manifest:
        exit(1)
    modpack_list=manifest['modlist']

    for modpack in modpack_list:
        #if not modpack_isInstalled(modpack, data_directory):
            install_modpack(modpack, data_directory)
        #elif modpack_update_available(modpack):
        #    update_modpack(modpack, DATA_DIR_NAME)


    #modpack_list_status={}
    #for modpack in modpack_list:
    #    if not modpack_isInstalled(modpack):
    #        modlist_status[modpack[0]]=-1
    #    elif modpack_update_available(modpack):
    #        modlist_status[modpack[0]]=1
    #    else:
    #        modlist_status[modpack[0]]=0
