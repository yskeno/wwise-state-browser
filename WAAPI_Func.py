#! python3

from waapi import WaapiClient, CannotConnectToWaapiException
import atexit
from pprint import pprint


class WaapiClient_StateTool(WaapiClient):
    # for Singleton design pattern.
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __call__(cls):
        if cls.__instance is None:
            cls.__instance = super().__call__(cls)
        return cls.__instance

    def __init__(self):
        super().__init__()

        self.set_subscription()

    def is_connected(self) -> bool:
        if super().is_connected() is None:
            return False
        else:
            return super().is_connected()

    def get_wproj_info(self) -> dict:
        """
        Return wproj name and path as str.
        {'name': wproj_name',
        'filePath': 'wproj_path'}
        """

        wproj_object = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["Project"]},
            "options": {
                "return": ["name", "filePath"]}
        })
        return {'name': wproj_object['return'][0]['name'],
                'filePath': wproj_object['return'][0]['filePath']}

    def update_state_info(self) -> dict:
        """Return State information.\n
    Args:

    Returns:
        dict: State information.\n
        {'StateGroup GUID': {'path': 'StateGroup Name',
                                  'state': ['State Name', 'State Name', ...],
                                  'current': 'State name'}
        """
        ret = {}
        stategrouplist = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["StateGroup"]},
            "options": {
                "return": ["id", "path"]}
        }).get('return', [])

        for stategroup in stategrouplist:
            ret[stategroup['id']] = {
                'path': stategroup['path']}

            # Get All State Info from Each StateGroup.
            state_list = self.call("ak.wwise.core.object.get", {
                "from": {
                    "id": [stategroup['id']]},
                "transform": [
                    {"select": ["children"]},
                    {"where": ["type:isIn", ["State"]]}],
                "options": {
                    "return": ["id", "name"]}
            }).get('return', [])

            # Add Each State as List.
            for state in state_list:
                ret[stategroup['id']].setdefault(
                    'state', []).append(state['name'])

            # Add current State info.
            ret[stategroup['id']].setdefault('current', self.call(
                "ak.soundengine.getState", {
                    "stateGroup": stategroup['id'],
                    "options": {
                        "return": ["id", "name"]}  # "parent.id" & "parent.path" is necessary?
                }).get('return', {}).get('name', ""))

        # Sort return dict by path.
        ret_sorted = {}
        for k, v in sorted(ret.items(), key=lambda x: x[1]['path']):
            ret_sorted[k] = v
        return ret_sorted

    def __get_stategroup_info(self) -> dict:
        """Return StateGroup information as dict.\n
    Args:

    Returns:
        dict: StateGroup information.\n
        ex.) {'{StateGroupA GUID}': {'id': '{StateGroupA GUID}'\n
                                                     'path': '\\States\\Default WorkUnit\\StGroup_A'},\n
                '{StateGroupB GUID}': {'id': '{StateGroupB GUID}',\n
                                                     'path': '\\States\\Default WorkUnit\\StGroup_B'}}
        """
        stategrouplist = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["StateGroup"]},
            "options": {
                "return": ["id", "path"]}
        }).get('return', [])
        ret = {}
        for stategroup in stategrouplist:
            ret[stategroup['id']] = {
                'id': stategroup['id'],
                'path': stategroup['path']}
        return ret

    def __get_current_state(self) -> dict:
        """
        Return current State in Wwise as dict.
                ex.) {'id': '{00000000-1111-2222-3333-444444444444}',
                'name': 'StateA',
                'parent.id': 
                'parent.path': '\\States\\Default Work Unit\\StateGroup'}
        """
        ret = {}
        stategroup_dict = self.__get_stategroup_info()
        for stategroup in stategroup_dict.values():
            ret.setdefault(stategroup['id'], self.call("ak.soundengine.getState", {
                "stateGroup": stategroup['id'],
                "options": {
                    "return": ["id", "name", "parent.path"]}
            }).get('return', {}))
        return ret

    def set_state(self, stategroup: str, state: str) -> bool:
        """Return StateGroup information as dict.\n
    Args:
        stategroup (str): Either the ID(GUID), name, or Short ID of the State Group.
        state (str): Either the ID(GUID), name, or Short ID of the State.
    Returns:
        bool: True for success, False otherwise.
        """
        try:

            self.call("ak.soundengine.setState", {
                "stateGroup": stategroup,
                "state": state
            })
            return True
        except:
            return False

    # Callback function with F matching signature.
    # Signature (*args, **kwargs) matches anything, with results being in kwargs.
    def set_subscription(self):
        self.subscribe("ak.wwise.core.object.nameChanged",
                       self.subscribe_statename_changed, {"return": ["type"]})
        self.subscribe("ak.wwise.core.profiler.stateChanged",
                       self.subscribe_state_changed, {"return": ["id", "name"]})

    def subscribe_statename_changed(self, *args, **kwargs):
        if kwargs.get("object", {}).get("type") != "State" and kwargs.get("object", {}).get("type") != "StateGroup":
            return
        print(kwargs.get("oldName")+" to "+kwargs.get("newName"))

    def subscribe_state_changed(self, *args, **kwargs):
        print("!!! State Changed !!!")
        pprint(args)
        pprint(kwargs)


if __name__ == "__main__":
    try:
        # Connecting to Waapi using default URL
        client = WaapiClient_StateTool()
        # NOTE: the client must be manually disconnected when instantiated in the global scope

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi: Check Wwise is running and WAAPI is enabled.")
    else:
        # Get Selected Object.
        print("*** Get Selected Object.")
        pprint(client.call("ak.wwise.ui.getSelectedObjects",
                           options={
                               "return": ["id", "name", "type", "shortId", "classId", "category", "filePath",
                                          "workunit", "parent", "owner", "path", "workunitIsDefault", "workunitType", "workunitIsDirty",
                                          "childrenCount"]}))

        # Get ProjectName and Path.
        print("*** ProjectName and Path: get_wproj_info()")
        print(client.get_wproj_info())

        # Get State List
        print("*** Get State Dict: update_state_info()")
        pprint(client.update_state_info())

        client.set_state("{5ABE43F7-5E44-4F37-AE07-BC265DDCC34E}",
                         "{CD350719-7205-45AC-B57A-2FB2E1E492AD}")

        print("*** Get Current State: __get_current_state()")
        pprint(client.__get_current_state())

        # print("*** Subscribe")
        # handler = client.set_subscription()

        client.disconnect()

        print("*** EOF")
