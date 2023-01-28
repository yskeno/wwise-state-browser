#! python3
from waapi import WaapiClient, CannotConnectToWaapiException
from waapi.client.executor import SequentialThreadExecutor
from pprint import pprint

from StateObserver import Subject


class StateUtility(WaapiClient, Subject):
    # {'StateGroup GUID': {'path': 'StateGroup Name',
    #                       'state': ['State Name', 'State Name', ...],
    #                       'current': 'State name'}
    __wproj_info = {}

    @property
    def wproj_info(self):
        return StateUtility.__wproj_info

    __state_in_wwise = {}

    @property
    def state_in_wwise(self):
        return StateUtility.__state_in_wwise

    def __init__(self,
                 url=None,
                 allow_exception=False,
                 callback_executor=SequentialThreadExecutor,
                 observer=None):
        super().__init__(url, allow_exception, callback_executor)
        if observer is not None:
            self.add_observer(observer)

        # { 'StateGroup GUID' : {'StateGroup':{'newName':NewStateGroup Path},
        #                        'State': {'id':State GUID,
        #                                  'oldName':OldState Name,
        #                                  'newName':NewState Name}}
        self.changed_statename = {}
        self.changed_currentstate = {}   # { StateGroup GUID : NewState Name}

        self.update_wproj_info()
        self.update_state_info()
        self.set_subscription()

    def is_connected(self) -> bool:
        if super().is_connected() is None:
            return False
        else:
            return super().is_connected()

    def disconnect(self) -> bool:
        ret = super().disconnect()
        self.notify_observer_of_waapi_disconnected()
        return ret

    # Callback function with a matching signature.
    # Signature (*args, **kwargs) matches anything, with results being in kwargs.
    def set_subscription(self):
        self.subscribe("ak.wwise.core.project.preClosed",
                       self.disconnect)
        self.subscribe("ak.wwise.core.object.nameChanged",
                       self.on_statename_changed, {"return": ["type", "id", "name", "path", "parent"]})
        self.subscribe("ak.wwise.core.profiler.stateChanged",
                       self.on_currentstate_changed, {"return": ["id", "name", "path"]})

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

        StateUtility.__wproj_info = {'name': wproj_object['return'][0]['name'],
                                     'filePath': wproj_object['return'][0]['filePath']}

        return StateUtility.__wproj_info

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
            StateUtility.__state_in_wwise[k] = v

        return StateUtility.__state_in_wwise

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

    def on_statename_changed(self, **kwargs):
        # Process for StateGroup.
        if kwargs.get("object", {}).get("type", "") == "StateGroup":
            stategroupguid = kwargs.get("object", {}).get("id", "")
            self.changed_statename[stategroupguid] = {"StateGroup":
                                                      {'oldName': StateUtility.__state_in_wwise[stategroupguid]['path'],
                                                       'newName': kwargs.get("object", {}).get("path", "")}}
            StateUtility.__state_in_wwise[stategroupguid]['path'] = kwargs.get(
                "object", {}).get("path", "")
            self.notify_observer_of_statename_changed()

        # Process for State.
        elif kwargs.get("object", {}).get("type", "") == "State":
            stategroupguid = kwargs.get("object", {}).get(
                "parent", {}).get("id", "")
            # Make new Changed State List.
            if not self.changed_statename.get(stategroupguid, {}).get("State", []):
                self.changed_statename[stategroupguid] = {"State": []}

            # Is Changed State already exist in changed_statename?
            if kwargs.get("object", {}).get("id", "") in [k['id'] for k in self.changed_statename[stategroupguid]['State']]:
                existed_id = [k['id']
                              for k in self.changed_statename[stategroupguid]['State']].index(kwargs.get("object", {}).get("id", ""))
                self.changed_statename[stategroupguid]["State"][existed_id] = {'id': kwargs.get("object", {}).get("id", ""),
                                                                               'oldName': kwargs.get("oldName", ""),
                                                                               'newName': kwargs.get("newName", "")}
            else:
                self.changed_statename[stategroupguid]["State"].append({'id': kwargs.get("object", {}).get("id", ""),
                                                                        'oldName': kwargs.get("oldName", ""),
                                                                        'newName': kwargs.get("newName", "")})
            StateUtility.__state_in_wwise[stategroupguid]['state'][StateUtility.__state_in_wwise[stategroupguid]['state'].index(
                kwargs.get("oldName"))] = kwargs.get("newName")
            self.notify_observer_of_statename_changed()

        # Except for State/StateGroup.
        else:
            return

    def on_currentstate_changed(self, *args, **kwargs):
        StateUtility.__state_in_wwise[kwargs.get(
            "stateGroup", {}).get("id", "")]['current'] = kwargs.get("state", {}).get("name", "")
        self.changed_currentstate[kwargs.get(
            "stateGroup", {}).get("id", "")] = kwargs.get("state", {}).get("name", "")
        self.notify_observer_of_currentstate_changed()

    def on_statename_sync_completed(self):
        self.changed_statename = {}

    def on_currentstate_sync_completed(self):
        self.changed_currentstate = {}


if __name__ == "__main__":
    try:
        # Connecting to Waapi using default URL
        client = StateUtility()
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
