#! python3
import os
import configparser

import WaapiInterface
import TK_Window


def connect_to_wwise(rootwd: TK_Window.MainWindow):
    rootwd.show_connecting_message()
    try:
        # Connecting to Waapi using default URL
        # NOTE: the client must be manually disconnected when instantiated in the global scope
        client = WaapiInterface.StateUtility()
        client.add_observer(rootwd)
        rootwd.client = client

        rootwd.dict_state_in_wwise = client.state_in_wwise

        global handler
        handler = client.subscribe(
            "ak.wwise.core.project.preClosed", lambda: disconnect_from_wwise(rootwd, client))
        rootwd.protocol("WM_DELETE_WINDOW",
                        lambda: close_main_window(rootwd, client))
        rootwd.update_wproj_info(client.wproj_info)
        rootwd.update_statebrowser()
        bind_tkinter_to_waapi(rootwd, client)

        return client

    except WaapiInterface.CannotConnectToWaapiException:
        rootwd.update_wproj_info()
        return


def disconnect_from_wwise(rootwd: TK_Window.MainWindow, client: WaapiInterface.StateUtility):
    rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)
    rootwd.btn_setstate['command'] = None
    rootwd.update_wproj_info()


def bind_tkinter_to_waapi(rootwd: TK_Window.MainWindow, client: WaapiInterface.StateUtility):
    rootwd.btn_connectwaapi['command'] = lambda: disconnect_from_wwise(
        rootwd, client)


def close_main_window(rootwd: TK_Window.MainWindow, client: WaapiInterface.StateUtility = None):
    if isinstance(client, WaapiInterface.StateUtility):
        client.disconnect()
    with open('WwiseStateBrowser.ini', 'w') as ini:
        config['SETTINGS'] = {'enable_autosync': rootwd.enable_autosync.get(),
                              'visible_stategroup_path': rootwd.visible_stategroup_path.get()}
        config.write(ini)
    rootwd.destroy()


config = configparser.ConfigParser()
if not os.path.exists(os.getcwd()+"\\WwiseStateBrowser.ini"):
    with open('WwiseStateBrowser.ini', 'w') as ini:
        config['DEFAULT'] = {'enable_autosync': True,
                             'visible_stategroup_path': False}
        config['SETTINGS'] = {'enableautosync': True,
                              'visible_stategroup_path': False}
        config.write(ini)
config.read('WwiseStateBrowser.ini')


rootwd = TK_Window.MainWindow(
    config['SETTINGS']['enable_autosync'], config['SETTINGS']['visible_stategroup_path'])
rootwd.protocol("WM_DELETE_WINDOW",
                lambda: close_main_window(rootwd))

rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)

client = connect_to_wwise(rootwd)

rootwd.mainloop()
