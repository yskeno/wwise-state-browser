#! python3
import tkinter
import tkinter.ttk as ttk

from StateObserver import Observer
from WwiseStateBrowserInterface import StateUtility


class MainWindow(tkinter.Tk, Observer):
    def __init__(self, enableautosync=True, visible_stategroup_path=False):
        super().__init__()

        self.title("Wwise State Browser")
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.minsize(750, 220)

        # Variables.
        self.client: StateUtility = None

        self.enable_autosync = tkinter.BooleanVar(value=enableautosync)
        self.visible_stategroup_path = tkinter.BooleanVar(
            value=visible_stategroup_path)

        self.dict_state_in_wwise = {}
        # { 'StateGroup' : {'Label' : LabelObject<StateGroupName>,
        #                   'ComboBox' : ComboBoxObject<StateName> }
        self.dict_statebrowser_object = {}
        # { 'StateGroup GUID' : 'State Name' }
        self.dict_changedstate = {}

        # Create Settings Section.
        self.frame_settings = ttk.Labelframe(self,
                                             name="frame_settings",
                                             text="Settings",
                                             padding=3, border=1, relief="solid")
        self.frame_settings.grid(column=0, row=0, sticky="nw",
                                 padx=10, pady=3, ipadx=2, ipady=0)

        self.btn_forceupdate = ttk.Button(self.frame_settings,
                                          name="btn_forceupdate",
                                          text="Force Update",
                                          command=self.update_statebrowser,
                                          state='disabled',
                                          padding=3,)
        self.btn_forceupdate.grid(column=0, row=0, padx=3, pady=0)

        self.btn_setstate = ttk.Button(self.frame_settings,
                                       name="btn_setstate",
                                       text="Set State", padding=3,
                                       command=self.set_changed_state,
                                       state='disabled')
        self.btn_setstate.grid(column=1, row=0, padx=3, pady=0)

        self.chk_autosync = ttk.Checkbutton(self.frame_settings,
                                            name="chk_autosync",
                                            text="Auto Sync with Wwise",
                                            padding=3,
                                            variable=self.enable_autosync,
                                            )
        self.chk_autosync.grid(column=2, row=0, padx=3, pady=0)

        self.chk_visiblegrouppath = ttk.Checkbutton(self.frame_settings,
                                                    name="chk_visiblegrouppath",
                                                    text="Show StateGroup Path",
                                                    padding=3,
                                                    variable=self.visible_stategroup_path,
                                                    command=self.__on_toggle_stategrouplabel_text)
        self.chk_visiblegrouppath.grid(column=3, row=0, padx=3, pady=0)

        # Create Status Section.
        self.frame_status = ttk.Labelframe(self,
                                           name="frame_status",
                                           text="Connection Status",
                                           padding=3, border=1, relief="solid")
        self.frame_status.grid(column=0, row=2, sticky="sw",
                               padx=5, pady=3, ipadx=2, ipady=0,)

        self.btn_connectwaapi = ttk.Button(self.frame_status,
                                           name="btn_connectwaapi",
                                           text="Connect",
                                           state='active',
                                           padding=3, width=10)
        self.btn_connectwaapi.pack(side="left")

        self.lbl_wproj_info = ttk.Label(self.frame_status,
                                        name="lbl_wproj_info",
                                        text="",
                                        padding=3)
        self.lbl_wproj_info.pack(side="left")

        # Create Log Section.
        # self.frame_log = ttk.Labelframe(self,
        #                                 name="frame_log",
        #                                 text="Log",
        #                                 padding=3, border=1, relief="solid")
        # self.frame_log.grid(column=0, row=3, sticky="sw",
        #                     padx=5, pady=3, ipadx=2, ipady=0,)
        # self.lbl_log = ttk.Label(self.frame_log,
        #                          name="lbl_log",
        #                          text="Welcome to WaapiStateBrowser!",
        #                          padding=3)
        # self.lbl_log.pack(side="left")

        # Create StateBrowser Section.
        self.frame_statebrowser = ttk.Labelframe(self, name="frame_statebrowser",
                                                 text="State List",
                                                 padding=3, border=1, relief="solid")
        self.frame_statebrowser.grid(column=0, row=1, sticky="nsew",
                                     padx=10, pady=3, ipadx=2, ipady=0)

        self.lbl_title_stategroup = ttk.Label(self.frame_statebrowser, name="lbl_title_stategroup",
                                              text="StateGroup", width=25, anchor="center")
        self.lbl_title_stategroup.grid(column=0, row=0, sticky="EW")
        self.lbl_title_statename = ttk.Label(self.frame_statebrowser, name="lbl_title_statename",
                                             text="State", width=25, anchor="center")
        self.lbl_title_statename.grid(column=1, row=0, sticky="EW")

    def show_status_message(self, message=''):
        self.lbl_wproj_info.config(text=message)
        self.lbl_wproj_info.update()

    def clear_statebrowser(self):
        for stategroup in self.dict_statebrowser_object.keys():
            self.dict_statebrowser_object[stategroup]['Label'].destroy()
            self.dict_statebrowser_object[stategroup]['ComboBox'].destroy()
        self.dict_statebrowser_object.clear()
        self.dict_changedstate.clear()

    def update_statebrowser(self):
        self.clear_statebrowser()
        # Create StateGroupName Label & DirtyFlag Label.
        for stategroup_id, stategroup_info in self.dict_state_in_wwise.items():
            self.dict_statebrowser_object.setdefault(
                stategroup_id, {}).setdefault(
                    'Label', ttk.Label(self.frame_statebrowser,
                                       name="lbl_"+stategroup_id,
                                       #    text=stategroup_info.get('path', ""),
                                       width=50, border=1, relief="solid"))
            self.dict_statebrowser_object[stategroup_id].setdefault(
                'DirtyMark', ttk.Label(self.frame_statebrowser,
                                       name="dirty_"+stategroup_id,
                                       foreground="red",
                                       width=5, border=1, relief="flat"))

            # Create State ComboBox.
            combobox_values = []
            for i in stategroup_info.get('state', []):
                combobox_values.append(i)

            self.dict_statebrowser_object[stategroup_id].setdefault(
                'ComboBox', ttk.Combobox(self.frame_statebrowser,
                                         name='cmb_'+stategroup_id,
                                         state='readonly',
                                         width=25,
                                         values=combobox_values))
            self.dict_statebrowser_object[stategroup_id]['ComboBox'].current(0)
            self.dict_statebrowser_object[stategroup_id]['ComboBox'].bind(
                '<<ComboboxSelected>>', self.__on_state_combobox_changed)

            for i in range(len(self.dict_statebrowser_object)):
                # Browser column title is placed row=0, so start row=1.
                self.dict_statebrowser_object[stategroup_id]['Label'].grid(
                    column=0, row=i+1, sticky="EW")
                self.dict_statebrowser_object[stategroup_id]['ComboBox'].grid(
                    column=1, row=i+1, sticky="EW")
                self.dict_statebrowser_object[stategroup_id]['DirtyMark'].grid(
                    column=2, row=i+1)

            # Set ComboBox value to current State.
            self.dict_statebrowser_object[stategroup_id]['ComboBox'].set(
                stategroup_info.get('current'))

        # Set Label text.
        self.__on_toggle_stategrouplabel_text()

        self.client.on_statename_sync_completed()
        self.client.on_currentstate_sync_completed()

    def set_changed_state(self):
        if self.client is not None:
            for stategroup_id, state_name in self.dict_changedstate.items():
                self.client.set_state(stategroup_id, state_name)
            self.dict_changedstate = {}

    def __on_toggle_stategrouplabel_text(self):
        if self.visible_stategroup_path.get() == True:
            for stategroup in self.dict_statebrowser_object.keys():
                self.dict_statebrowser_object[stategroup]['Label'].config(
                    text=self.dict_state_in_wwise.get(stategroup, {}).get('path', ""))
        else:
            for stategroup in self.dict_statebrowser_object.keys():
                self.dict_statebrowser_object[stategroup]['Label'].config(
                    text=self.dict_state_in_wwise.get(stategroup, {}).get('path', "").split('\\')[-1])

    def __on_state_combobox_changed(self, event):
        # Already listed in dict_changedstate?
        if event.widget._name in self.dict_changedstate.keys():
            # Same State in Wwise?
            if self.dict_state_in_wwise[event.widget._name].get('current') == event.widget.get():
                # Delete existed key because you changed to same state in Wwise.
                del self.dict_changedstate[event.widget._name]
                return
        # Add new State in dict_changedstate.
        self.dict_changedstate[event.widget._name] = event.widget.get()

    def on_waapi_connected(self, client: StateUtility):
        self.client = client
        self.lbl_wproj_info.config(
            text="Connected: " + client.wproj_info.get('name', "") + "<"+client.wproj_info.get('filePath', "") + ">")
        self.btn_forceupdate['state'] = 'normal'
        self.btn_setstate['state'] = 'normal'
        self.dict_state_in_wwise = client.state_in_wwise
        self.update_statebrowser()

    def on_waapi_disconnected(self, client: StateUtility):
        self.client = None
        self.lbl_wproj_info.config(
            text="NotConnected: Check Wwise is running and WAAPI is enabled.")
        self.btn_forceupdate['state'] = 'disabled'
        self.btn_setstate['state'] = 'disabled'

    def on_statename_changed(self, client: StateUtility):
        if self.enable_autosync.get() == False:
            return
        for stategroupid, statenameinfo in client.changed_statename.items():
            for statetype, names in statenameinfo.items():
                if statetype == "StateGroup":
                    self.dict_statebrowser_object[stategroupid]['Label'].config(
                        text=names['newName'])
                elif statetype == "State":
                    # Can't change combobox values...
                    pass
        client.on_statename_sync_completed()

    def on_currentstate_changed(self, client: StateUtility):
        if self.enable_autosync.get() == False:
            return
        for stategroupid, newstate in client.changed_currentstate.items():
            self.dict_statebrowser_object[stategroupid]['ComboBox'].set(
                newstate)
        client.on_currentstate_sync_completed()


if __name__ == "__main__":
    root = MainWindow()
    root.mainloop()
