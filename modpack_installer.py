from tkinter import *
import json
import urllib.request
import os

def download(url=None):
    if not url:
        return None
    try:
        response = urllib.request.urlopen(url)
        return response.read()
    except:
        return None

def filename_from_url(url=None):
    if url:
        pos=str(url).rfind('/')+1
        return str(url)[int(pos):]

def download_json(url=None):
    data = download_file(url)
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

def install_modpack(modpack, data_directory=''):
    if not modpack_isInstalled(modpack, data_directory):
        os.mkdir(os.path.join(data_directory, modpack[0]))
        os.mkdir(os.path.join(data_directory, modpack[0], "mods"))
        os.mkdir(os.path.join(data_directory, modpack[0], "config"))
    

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
    MANIFEST_URL = ""
    DATA_DIR_NAME=""
    SERVERNAME=""

    #No more configuration
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), DATA_DIR_NAME)
    else:
        data_directory=os.path.join(os.path.expanduser(), DATA_DIR_NAME)

    manifest_filename=os.path.join(data_directory, filename_from_url(MANIFEST_URL))
    manifest = get_latest_manifest(url=MANIFEST_URL, file_location=manifest_filename)
    if not manifest:
        exit(1)
    modpack_list=manifest['modlist']

    for modpack in modpack_list:
        if not modpack_isInstalled(modpack, DATA_DIR_NAME):
            install_modpack(modpack, DATA_DIR_NAME)
        elif modpack_update_available(modpack):
            update_modpack(modpack, DATA_DIR_NAME)


    #modpack_list_status={}
    #for modpack in modpack_list:
    #    if not modpack_isInstalled(modpack):
    #        modlist_status[modpack[0]]=-1
    #    elif modpack_update_available(modpack):
    #        modlist_status[modpack[0]]=1
    #    else:
    #        modlist_status[modpack[0]]=0
