from io import BytesIO
from itertools import product
from tkinter import *
from zipfile import ZipFile
from multiprocessing import Process, Pool
import json
import urllib.request as request
import os

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
    print(modpack_isInstalled(modpack, data_directory))
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

def install_mod_files(mod_data):
    data = download(mod_data[3])
    with open(os.path.join(mod_data[4], "%s-%s.jar"%(mod_data[0],mod_data[1])), "wb+") as f:
        f.write(data)
    print("Downloaded %s, Version: %s"%(mod_data[0], mod_data[1]))

def install_modpack(modpack, data_directory=''):
    modpack_dir=make_modpack_directories(modpack, data_directory)
    mod_dir=os.path.join(modpack_dir, "mods")
    config_dir=os.path.join(modpack_dir, "config")
    modpack_json=get_latest_json(url=modpack[1],file_location=os.path.join(modpack_dir, filename_from_url(modpack[1])))
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
        pool.join()
    if config_dl:
        config_dl.join()

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
    print(manifest)
    modpack_list=manifest['modlist']

    for modpack in modpack_list:
        if not modpack_isInstalled(modpack, data_directory):
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
