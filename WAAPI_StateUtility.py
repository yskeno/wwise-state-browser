#! python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint


class WaapiClient_StateUtility(WaapiClient):
    # {'StateGroup GUID': {'path': 'StateGroup Name',
    #                       'state': ['State Name', 'State Name', ...],
    #                       'current': 'State name'}
    wproj_info = {}
    state_in_wwise = {}

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
        self.update_wproj_info()
        self.update_state_info()
        self.set_subscription()

    def is_connected(self) -> bool:
        if super().is_connected() is None:
            return False
        else:
            return super().is_connected()

    def update_wproj_info(self) -> dict:
        """
        Return wproj name and path as str.
        {'name': wproj_name',
        'filePath': 'wproj_path'}
        """

        wproj_object = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["Project"]},
            "options": {
                "return": ["name", "filePath"]}})

        WaapiClient_StateUtility.wproj_info = {'name': wproj_object['return'][0]['name'],
                                               'filePath': wproj_object['return'][0]['filePath']}

        return WaapiClient_StateUtility.wproj_info

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
        # Get All StateGroup Info.
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
        for k, v in sorted(ret.items(), key=lambda x: x[1]['path']):
            WaapiClient_StateUtility.state_in_wwise[k] = v

        return WaapiClient_StateUtility.state_in_wwise

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
                "state": state})
            return True
        except:
            return False

    # Callback function with a matching signature.
    # Signature (*args, **kwargs) matches anything, with results being in kwargs.
    def set_subscription(self):
        self.subscribe("ak.wwise.core.object.nameChanged",
                       self.on_statename_changed, {"return": ["type", "id", "name", "path", "parent"]})
        self.subscribe("ak.wwise.core.profiler.stateChanged",
                       self.on_state_changed, {"return": ["id", "name", "path"]})

    def on_statename_changed(self, **kwargs):
        # Process for StateGroup
        if kwargs.get("object", {}).get("type", "") == "StateGroup":
            WaapiClient_StateUtility.state_in_wwise[kwargs.get("object", {}).get(
                "id", "")]['path'] = kwargs.get("object", {}).get("path", "")
        # Process for State
        elif kwargs.get("object", {}).get("type", "") == "State":
            WaapiClient_StateUtility.state_in_wwise[kwargs.get(
                "object", {}).get("parent", {}).get("id", "")]['state'][WaapiClient_StateUtility.state_in_wwise[kwargs.get(
                    "object", {}).get("parent", {}).get("id", "")]['state'].index(kwargs.get("oldName"))] = kwargs.get("newName")
        # Except for State/StateGroup
        else:
            return

    def on_state_changed(self, *args, **kwargs):
        WaapiClient_StateUtility.state_in_wwise[kwargs.get(
            "stateGroup", {}).get("id", "")]['current'] = kwargs.get("state", {}).get("name", "")


if __name__ == "__main__":
    try:
        # Connecting to Waapi using default URL
        client = WaapiClient_StateUtility()
        # NOTE: the client must be manually disconnected when instantiated in the global scope

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi: Check Wwise is running and WAAPI is enabled.")
    else:
        # Get Selected Object.
        # print("*** Get Selected Object.")
        # pprint(client.call("ak.wwise.ui.getSelectedObjects",
        #                    options={
        #                        "return": ["id", "name", "type", "shortId", "classId", "category", "filePath",
        #                                   "workunit", "parent", "owner", "path", "workunitIsDefault", "workunitType", "workunitIsDirty",
        #                                   "childrenCount"]}))

        # Get ProjectName and Path.
        # print("*** ProjectName and Path: get_wproj_info()")
        # print(client.update_wproj_info())

        # Get State List
        # print("*** Get State Dict: update_state_info()")
        # pprint(client.update_state_info())

        # client.set_state("{5ABE43F7-5E44-4F37-AE07-BC265DDCC34E}",
        #                  "{CD350719-7205-45AC-B57A-2FB2E1E492AD}")

        # print("*** Subscribe")
        # handler = client.set_subscription()

        # client.disconnect()

        print("*** EOF")
