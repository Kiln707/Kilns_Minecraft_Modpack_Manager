from tkinter import *
import json
import urllib.request
import os

def download_file(url=None):
    if not url:
        return None
    try:
        response = urllib.request.urlopen(url)
        return response.read()
    except:
        return None

def download_manifest(url=None):
    data = download_file(url)
    if data:
        return json.loads(data.decode('utf-8'))
    return None

def download_modpack_json(url=None):
    return download_manifest(url)

def save_manifest(manifest_file_location=None, manifest=None):
    if manifest_file_location and manifest:
        with open(manifest_file_location,'w+') as manifest_file:
            json.dump(manifest, manifest_file)

def open_manifest(manifest_file_location=None):
    if manifest_file_location:
        with open(manifest_file_location,'r') as manifest_file:
            manifest = json.load(manifest_file)
        return manifest
    return None

def get_updated_manifest(url=None, manifest_file_location=None):
    latest_manifest = download_manifest(url)
    if latest_manifest:
        manifest={}
        if os.path.isfile(manifest_file_location):
            manifest = open_manifest(manifest_file_location)
        if not manifest or float(latest_manifest['version']) > float(manifest['version']):
            save_manifest(manifest_file_location, latest_version)
        return manifest
    else:
        return None

def modpack_json_filename(modpack, data_directory):
    modpack_dir=os.path.join(data_directory, modpack[0])
    return os.path.join(modpack_dir, "%s.json"%modpack[0])

def modpack_isInstalled(modpack, data_directory=''):
    return os.path.isfile(modpack_json_filename(modpack, data_directory))

def save_modpack(modpack, data_directory):
    pass

def open_modpack(modpack, data_directory):
    pass

def modpack_update_available(modpack):
    latest_json = download_modpack_json(modpack[1])
    if latest_json:
        jsondata={}
        modpack_json = modpack_json_filename(modpack, data_directory)
        if os.path.isfile(modpack_json):
            jsondata = open_manifest(modpack_json)
        if not manifest or float(latest_manifest['version']) > float(manifest['version']):
            save_manifest(modpack_json, latest_version)
        return jsondata
    else:
        return None

if __name__ == "__main__":
    #Editable Variables for installer
    MANIFEST_URL = ""
    SERVERNAME=""

    #No more configuration
    data_directory=''
    if os.name =='nt':
        data_directory=os.path.join(os.getenv('APPDATA'), '.RelatedByGaming')
    else:
        data_directory=os.path.join(os.path.expanduser(), '.RelatedByGaming')

    manifest_filename=os.path.join(data_directory, 'relatedbygaming.manifest')
    manifest = get_updated_manifest(url=MANIFEST_URL, manifest_file_location=manifest_filename)
    if not manifest:
        exit 1
    modlist=manifest['modlist']
    modlist_status={}
    for modpack in modlist:
        if not modpack_isInstalled(modpack):
            modlist_status[modpack[0]]=-1
        elif modpack_update_available(modpack):
            modlist_status[modpack[0]]=1
        else:
            modlist_status[modpack[0]]=0
