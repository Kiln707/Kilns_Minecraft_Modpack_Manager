from tkinter import *
from tkinter import filedialog
from editabletreeview import EditableTreeview
from operator import itemgetter

import urllib.request as request

import json

class ModpackBuilder(Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.num_items=0
        self.modpack_name = 'New Modpack'
        self.version = 0.0
        self.master.title("Modpack Builder")
        self.master.geometry("800x400")
        self.pack(fill=BOTH, expand=1)
        self.manifest_builder_window=None

        #modpack name Informational section
        label_name = Label(self, text='Modpack Name:')
        label_name.place(x=20, y=20)
        self.text_name = Text(self, height=1, width=30)
        self.text_name.insert('end', self.modpack_name)
        self.text_name.place(y=20, x=120)
        label_version = Label(self, text='Modpack Version:')
        label_version.place(y=20, x=400)
        self.text_version = Text(self, height=1, width=10)
        self.text_version.insert('end', self.version)
        self.text_version.place(y=20, x=500)

        #Table of mod information
        modpack_list = EditableTreeview(self)
        modpack_list['columns'] = ('ModName', 'Version', 'ModLink', 'DownloadLink')
        modpack_list['show'] = 'headings'
        modpack_list.heading('ModName', text='Mod Name')
        modpack_list.column('ModName', anchor='center', width='150')
        modpack_list.heading('Version', text='Version')
        modpack_list.column('Version', anchor='center', width='100')
        modpack_list.heading('ModLink', text='Mod Info URL')
        modpack_list.column('ModLink', anchor='center', width='250')
        modpack_list.heading('DownloadLink', text='Mod Download URL')
        modpack_list.column('DownloadLink', anchor='center', width='250')
        modpack_list.pack(pady=50)
        self.modpack_list = modpack_list
        self.modpack_list.bind('<<TreeviewInplaceEdit>>', self.update_row)
        self.create_row()

        scroll = Scrollbar(self, command=self.modpack_list.yview)
        scroll.pack( side=RIGHT, fill=Y )
        self.modpack_list['yscrollcommand']=scroll.set

        #modify table buttons:
        new_row = Button(self, text="Add Mod", command=self.create_row)
        new_row.place(x=25, y=280)

        del_row = Button(self, text="Delete Mod", command=self.delete_row)
        del_row.place(x=95, y=280)

        label_config = Label(self, text='Config Download link(Zip of all configs):')
        label_config.place(x=240, y=280)
        self.text_config = Text(self, height=1, width=30)
        self.text_config.place(y=280, x=460)

        label_server = Label(self, text='Server Address:')
        label_server.place(x=25, y=320)
        self.text_server = Text(self, height=1, width=30)
        self.text_server.place(y=320, x=115)

        label_forge = Label(self, text='Forge Version:')
        label_forge.place(x=380, y=305)
        self.text_forge = Text(self, height=1, width=30)
        self.text_forge.place(y=305, x=460)
        label_forge_warn = Label(self, text='WARNING: Forge Version must match Server\'s Forge version')
        label_forge_warn.place(x=380, y=330)

        load_list = Button(self, text='Load', command=self.load_list)
        load_list.place(x=220, y=350)

        save_list = Button(self, text="Save", command=self.save_list)
        save_list.place(x=270, y=350)

        export_list = Button(self, text="Export as text file", command=self.export)
        export_list.place(x=350, y=350)

        cancel = Button(self, text="Exit", command=self.master.destroy)
        cancel.place(x=50, y=350)

        manifest = Button(self, text="Manifest Builder", command=self.open_manifest_builder)
        manifest.place(x=550, y=350)

    def onclick(self, event):
        print(event.widget)

    def update_row(self, event):
        row = self.modpack_list.get_event_info()
        self.modpack_list.inplace_entry(row[0], row[1])

    def create_row(self, data=None):
        if not data:
            row = self.modpack_list.insert('', 'end', "mod_%s" % self.num_items, value=("Mod name", "Version", "Mod Info Link", "Mod Download Link"))
            self.num_items += 1
        else:
            self.modpack_list.insert('', 'end', "mod_%s"%self.num_items, value=tuple(data))
            self.num_items += 1

    def delete_row(self):
        row = self.modpack_list.get_event_info()
        self.modpack_list.delete(row[1])

    def generate_modlist(self):
        modlist=[]
        for row in self.modpack_list.get_children():
            values = self.modpack_list.item(row)['values']
            modlist.append(values)
        return modlist

    def generate_modlist_dict(self):
        modlist=[]
        for mod in self.sort_list(self.generate_modlist()):
            modlist.append({'name':mod[0], 'version':mod[1], 'info':mod[2], 'download':mod[3]})
        return modlist

    def sort_list(self, list, sort_index=0):
        return sorted(list, key=lambda mod: mod[0].lower())

    def save_list(self):
        file_data={}
        filename = filedialog.asksaveasfilename(title="Save Modpack List", filetypes=(('json files',"*.json"),))
        if not filename.endswith('.json'):
            filename="%s.json"%filename
        file_data['modpack_name']=self.text_name.get('1.0', END).strip()
        file_data['version']=self.text_version.get('1.0', END).strip()
        file_data['forge']=self.text_forge.get('1.0', END).strip()
        configlink=self.text_config.get('1.0', END).strip()
        if not configlink.startswith('http://'):
            configlink='http://%s'%configlink
        file_data['config_link']=configlink
        file_data['server_address']=self.text_server.get('1.0', END).strip()
        file_data['modlist']=self.generate_modlist_dict()
        with open(filename, 'w+') as file:
            json.dump(file_data, file)

    def load_list(self):
        filename = filedialog.askopenfilename(title="Open Modpack List", filetypes=(('json files',"*.json"),))
        if not filename.endswith('.json'):
            filename="%s.json"%filename
        file_data={}
        with open(filename, 'r') as file:
            file_data = json.load(file)
        self.text_name.delete('1.0', END)
        self.text_name.insert('end', file_data['modpack_name'])

        self.text_version.delete('1.0', END)
        self.text_version.insert('end', file_data['version'])

        self.text_config.delete('1.0', END)
        self.text_config.insert('end', file_data['config_link'])

        self.text_server.delete('1.0', END)
        self.text_server.insert('end', file_data['server_address'])

        self.text_forge.delete('1.0', END)
        self.text_forge.insert('end', file_data['forge'])

        self.num_items=0
        self.modpack_list.clear()
        for row in self.modpack_list.get_children():
            self.modpack_list.delete(row)
        for row in file_data['modlist']:
            mod=[]
            for key, value in row.items():
                mod.append(value)
            self.create_row(mod)

    def export(self):
        filename = filedialog.asksaveasfilename(title="Export Modpack List", filetypes=(('text files',"*.txt"),("all files","*.*")))
        if filename == '':
            return
        elif "." not in filename:
            filename+=".txt"
        modpack_list=self.sort_list(self.generate_modlist())
        modlist = ""
        for mod in modpack_list:
            modlist+=", ".join(str(e) for e in mod)+'\n'
        with open(filename, 'w+') as file:
            file.write("%(modpack_name)s  Version:%(version)s\nForge Version:%(forge)s\nConfiguration File Download Location:%(config)s\nMods:\n%(modlist)s" % {'modpack_name':self.text_name.get('1.0', END).strip(), 'version':self.text_version.get('1.0', END).strip(), 'modlist':modlist, 'config':self.text_name.get('1.0', END).strip(), 'forge':self.text_forge.get('1.0',END).strip()})

    def open_manifest_builder(self):
        if self.manifest_builder_window:
            return
        top = Toplevel(self)
        self.manifest_builder_window = ManifestBuilder(top)
        self.manifest_builder_window.bind("<<CLOSE_BUILDER>>",self.close_manifest_builder)


    def close_manifest_builder(self, *arg):
        if self.manifest_builder_window:
            #self.manifest_builder_window.withdraw()
            #self.manifest_builder_window.destroy()
            self.manifest_builder_window=None

class ManifestBuilder(Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.num_items=0
        self.group_name = 'Server Name'
        self.version = 0.0
        self.master.title("Manifest Builder")
        self.master.geometry("600x400")
        self.pack(fill=BOTH, expand=1)

        #modpack name Informational section
        label_name = Label(self, text='Modpack Name:')
        label_name.place(x=20, y=20)
        self.text_name = Text(self, height=1, width=30)
        self.text_name.insert('end', self.group_name)
        self.text_name.place(y=20, x=120)
        label_version = Label(self, text='Modpack Version:')
        label_version.place(y=20, x=400)
        self.text_version = Text(self, height=1, width=10)
        self.text_version.insert('end', self.version)
        self.text_version.place(y=20, x=500)

        #Table of mod information
        modpack_list = EditableTreeview(self)
        modpack_list['columns'] = ('ModpackName', 'JSONLocation')
        modpack_list['show'] = 'headings'
        modpack_list.heading('ModpackName', text='Modpack Name')
        modpack_list.column('ModpackName', anchor='center', width='150')
        modpack_list.heading('JSONLocation', text='JSON URL')
        modpack_list.column('JSONLocation', anchor='center', width='150')
        modpack_list.pack(pady=50)
        self.modpack_list = modpack_list
        self.modpack_list.bind('<<TreeviewInplaceEdit>>', self.update_row)
        self.create_row()

        #modify table buttons:
        new_row = Button(self, text="Add Modpack", command=self.create_row)
        new_row.place(x=25, y=280)

        del_row = Button(self, text="Delete Modpack", command=self.delete_row)
        del_row.place(x=110, y=280)

        load_list = Button(self, text='Load', command=self.load_list)
        load_list.place(x=220, y=350)

        save_list = Button(self, text="Save", command=self.save_list)
        save_list.place(x=270, y=350)

        cancel = Button(self, text="Cancel", command=self.close)
        cancel.place(x=50, y=350)

    def close(self):
        self.event_generate("<<CLOSE_BUILDER>>")
        self.master.withdraw()
        self.destroy()


    def update_row(self, event):
        row = self.modpack_list.get_event_info()
        self.modpack_list.inplace_entry(row[0], row[1])

    def create_row(self, data=None):
        if not data:
            row = self.modpack_list.insert('', 'end', "mod_%s" % self.num_items, value=("Modpack Name", "JSON URL"))
            self.num_items += 1
        else:
            self.modpack_list.insert('', 'end', "mod_%s"%self.num_items, value=tuple(data))
            self.num_items += 1


    def delete_row(self):
        row = self.modpack_list.get_event_info()
        self.modpack_list.delete(row[1])

    def save_list(self):
        file_data={}
        filename = filedialog.asksaveasfilename(title="Save Manifest", filetypes=(('manifest files',"*.manifest"),))
        if not filename.endswith('.manifest'):
            filename="%s.manifest"%filename
        file_data['server']=self.text_name.get('1.0', END).strip()
        file_data['version']=self.text_version.get('1.0', END).strip()
        modlist=[]
        for row in self.modpack_list.get_children():
            modlist.append(self.modpack_list.item(row)['values'])
        file_data['modlist']=modlist
        with open(filename, 'w+') as file:
            json.dump(file_data, file)

    def load_list(self):
        filename = filedialog.askopenfilename(title="Open manifest", filetypes=(('manifest files',"*.manifest"),))
        if not filename.endswith('.manifest'):
            filename="%s.manifest"%filename
        file_data={}
        with open(filename, 'r') as file:
            file_data = json.load(file)
        self.text_name.delete('1.0', END)
        self.text_name.insert('end', file_data['server'])

        self.text_version.delete('1.0', END)
        self.text_version.insert('end', file_data['version'])

        self.num_items=0
        self.modpack_list.clear()
        for row in self.modpack_list.get_children():
            self.modpack_list.delete(row)
        for row in file_data['modlist']:
            self.create_row(row)

VERSION="1.0.1"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'version':
            print("Kiln's Modpack Builder Version: %s"%VERSION)
            sys.exit(0)
        else:
            print("Invalid Usage!")
            sys.exit(1)
    root=Tk()

    app=ModpackBuilder(root)

    root.mainloop()
