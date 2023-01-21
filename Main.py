#! python3
import sys

import WAAPI_Func
import TK_Func


def connect_to_wwise(rootwd: TK_Func.MainWindow):
    rootwd.show_connecting_message()
    try:
        # Connecting to Waapi using default URL
        # NOTE: the client must be manually disconnected when instantiated in the global scope
        client = WAAPI_Func.WaapiClient_StateTool()
        global handler
        handler = client.subscribe(
            "ak.wwise.core.project.preClosed", lambda: disconnect_from_wwise(rootwd, client))
        rootwd.protocol("WM_DELETE_WINDOW",
                        lambda: close_main_window(rootwd, client))
        rootwd.update_wproj_info(True, client.get_wproj_info())
        rootwd.update_statebrowser(
            client.update_state_info())
        bind_tkinter_to_waapi(rootwd, client)
        return client
    except WAAPI_Func.CannotConnectToWaapiException:
        rootwd.update_wproj_info(False)
        return


def disconnect_from_wwise(rootwd: TK_Func.MainWindow, client: WAAPI_Func.WaapiClient_StateTool):
    client.unsubscribe(handler)
    client.disconnect()
    rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)
    rootwd.btn_updatestate['command'] = None
    rootwd.btn_setstate['command'] = None
    rootwd.update_wproj_info()
    rootwd.clear_statebrowseer()


def bind_tkinter_to_waapi(rootwd: TK_Func.MainWindow, client: WAAPI_Func.WaapiClient_StateTool):
    rootwd.btn_connectwaapi['command'] = lambda: disconnect_from_wwise(
        rootwd, client)
    rootwd.btn_updatestate['command'] = lambda: update_state_browsertool(
        rootwd, client)
    rootwd.btn_setstate['command'] = lambda: set_changed_state(
        rootwd, client)


def update_state_browsertool(rootwd: TK_Func.MainWindow, client: WAAPI_Func.WaapiClient_StateTool):
    rootwd.update_statebrowser(client.update_state_info())
    return


def set_changed_state(rootwd: TK_Func.MainWindow, client: WAAPI_Func.WaapiClient_StateTool):
    for changedstategroup_name, changedstate_name in rootwd.dict_statebrowser_changed.items():
        client.set_state(changedstategroup_name.split('\\')[-1],
                         changedstate_name)


def close_main_window(rootwd, client):
    if isinstance(client, WAAPI_Func.WaapiClient_StateTool):
        client.disconnect()
        client = None
    rootwd.destroy()


rootwd = TK_Func.MainWindow()
rootwd.btn_connectwaapi['command'] = lambda: connect_to_wwise(rootwd)

client = connect_to_wwise(rootwd)

rootwd.mainloop()
