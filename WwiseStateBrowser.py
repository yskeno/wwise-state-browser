#! python3
import os
import configparser

import WwiseStateBrowserInterface
import WwiseStateBrowserGUI


# def main():
#     # Load config file.
#     config = configparser.ConfigParser()
#     if not os.path.exists(os.getcwd()+"\\WwiseStateBrowser.ini"):
#         with open('WwiseStateBrowser.ini', 'w') as ini:
#             config['DEFAULT'] = {'enable_autosync': True,
#                                  'visible_stategroup_path': False}
#             config['SETTINGS'] = {'enableautosync': True,
#                                   'visible_stategroup_path': False}
#             config.write(ini)
#     config.read('WwiseStateBrowser.ini')

#     rootwd = WwiseStateBrowserGUI.MainWindow(
#         config['SETTINGS']['enable_autosync'], config['SETTINGS']['visible_stategroup_path'])
#     rootwd.protocol("WM_DELETE_WINDOW",
#                     lambda: close_main_window(rootwd))

#     rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)

#     client = connect_to_wwise(rootwd)

#     rootwd.mainloop()


def connect_to_wwise(rootwd: WwiseStateBrowserGUI.MainWindow):
    rootwd.show_status_message('Connecting to Wwise...')
    try:
        client = WwiseStateBrowserInterface.StateUtility(observer=rootwd)

        global handler
        handler = client.subscribe(
            "ak.wwise.core.project.preClosed", lambda: disconnect_from_wwise(rootwd, client))
        rootwd.protocol("WM_DELETE_WINDOW",
                        lambda: close_main_window(rootwd, client))
        rootwd.btn_connectwaapi['command'] = lambda: disconnect_from_wwise(
            rootwd, client)
        rootwd.btn_connectwaapi.config(text="Disconnect")

        return client

    except WwiseStateBrowserInterface.CannotConnectToWaapiException as e:
        rootwd.show_status_message(e)
        return


def disconnect_from_wwise(rootwd: WwiseStateBrowserGUI.MainWindow, client: WwiseStateBrowserInterface.StateUtility):
    client.disconnect()
    rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)
    rootwd.btn_connectwaapi.config(text="Connect")


def close_main_window(rootwd: WwiseStateBrowserGUI.MainWindow, client: WwiseStateBrowserInterface.StateUtility = None):
    if isinstance(client, WwiseStateBrowserInterface.StateUtility):
        del client

    with open('WwiseStateBrowser.ini', 'w') as ini:
        config['SETTINGS'] = {'enable_autosync': rootwd.enable_autosync.get(),
                              'visible_stategroup_path': rootwd.visible_stategroup_path.get()}
        config.write(ini)
    rootwd.quit()


# Config File.
config = configparser.ConfigParser()
if not os.path.exists(os.getcwd()+"\\WwiseStateBrowser.ini"):
    with open('WwiseStateBrowser.ini', 'w') as ini:
        config['DEFAULT'] = {'enable_autosync': True,
                             'visible_stategroup_path': False}
        config['SETTINGS'] = {'enableautosync': True,
                              'visible_stategroup_path': False}
        config.write(ini)
config.read('WwiseStateBrowser.ini')


rootwd = WwiseStateBrowserGUI.MainWindow(
    config['SETTINGS']['enable_autosync'], config['SETTINGS']['visible_stategroup_path'])
rootwd.protocol("WM_DELETE_WINDOW",
                lambda: close_main_window(rootwd))

rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)

client = connect_to_wwise(rootwd)

rootwd.mainloop()

# if __name__ == "__main__":
#     main()
