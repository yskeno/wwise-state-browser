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

        self.statedict = {}

    def is_connected(self) -> bool:
        if super().is_connected() is None:
            return False
        else:
            return super().is_connected()

    def get_wproj_info(self) -> str:
        """
        Return wproj name and path as str.
        '(wproj_name)<(wproj_path)>'
        """

        wproj_object = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["Project"]},
            "options": {
                "return": ["name", "filePath",]}
        })
        return wproj_object['return'][0]['name'] + " <" + wproj_object['return'][0]['filePath'] + ">"

    def __get_stategroup_list(self) -> list:
        stategroup_list = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["StateGroup"]},
            "options": {
                "return": ["id", "name", "path"]}
        })
        return stategroup_list["return"]

    def __get_stateinfo_list(self, stategroup_id: str) -> list:
        state_info = self.call("ak.wwise.core.object.get", {
            "from": {
                "id": [stategroup_id]},
            "transform": [
                {"select": ["children"]},
                {"where": ["type:isIn", ["State"]]}],
            "options": {
                "return": ["id", "name"]}
        })
        return state_info["return"]

    def get_state_dict(self) -> dict:
        """
        Return state dict.\n
        ex.) {"\\State\\WorkUnit\\StGroup_A": [{'id': '{00000000-1111-2222-3333-444444444444}'\n
                                                                  'name': "StGroup_A_ON"},\n
                                                                  {'id': '{AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE}',\n
                                                                  'name': "StGroup_A_OFF"]}
        """
        ret = {}

        stategroup_list = self.__get_stategroup_list()
        for each_stategroup in stategroup_list:
            # Make Key as StateGroup path.
            ret.setdefault(each_stategroup['path'], [])

            # Get All State Info from Each StateGroup.
            all_state_info = self.__get_stateinfo_list(each_stategroup['id'])

            # Add Each State as List.
            for each_state_info in all_state_info:
                ret[each_stategroup['path']].append(
                    {'id': each_state_info['id'], 'name': each_state_info['name']})
        return ret

    def get_currentstate_dict(self) -> dict:
        currentstate_dict = {}
        statedict = self.get_state_dict()
        for stategrouppath in statedict.keys():
            currentstate_dict.setdefault(
                stategrouppath, self.__get_current_state(stategrouppath)['name'])
            self.__get_current_state(stategrouppath)
        return currentstate_dict

    def __get_current_state(self, stategroup_path: str) -> dict:
        """
        Return current state.\n
        ex.) {'id': '{00000000-1111-2222-3333-444444444444}',
                'name': 'StateA',
                'parent.path': '\\States\\Default Work Unit\\StateGroup'}
        """
        ret = self.call("ak.soundengine.getState", {
            "stateGroup": stategroup_path,
            "options": {
                "return": ["id", "name", "parent.path"]}
        })
        return ret["return"]

    def set_state(self, stategroup_name: str, state: str):
        self.call("ak.soundengine.setState", {
            "stateGroup": stategroup_name,
            "state": state
        })

    # Callback function with a matching signature.
    # Signature (*args, **kwargs) matches anything, with results being in kwargs.
    def set_subscription(self):
        self.subscribe("ak.wwise.core.object.nameChanged",
                       self.__func_statename_changed, {"return": ["type"]})
        self.subscribe("ak.wwise.core.profiler.stateChanged",
                       self.__func_state_changed, {"return": ["id", "name"]})

    def __func_statename_changed(self, *args, **kwargs):
        if kwargs.get("object", {}).get("type") != "State" and kwargs.get("object", {}).get("type") != "StateGroup":
            return
        print(kwargs.get("oldName")+" to "+kwargs.get("newName"))

    def __func_state_changed(self, *args, **kwargs):
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
        print("*** Get State List: get_state_dict()")
        pprint(client.get_state_dict())

        client.set_state("PlayerInWater", "No")

        print("*** Get Current State: get_currentstate_dict()")
        pprint(client.get_currentstate_dict())

        print("*** Subscribe")
        handler = client.set_subscription()

        print("*** EOF")
