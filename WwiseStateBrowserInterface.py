#! python3
from waapi import WaapiClient, CannotConnectToWaapiException
from waapi.client.executor import SequentialThreadExecutor

from StateObserver import Subject


class StateUtility(WaapiClient, Subject):

    def __init__(self, url=None, allow_exception=False, callback_executor=SequentialThreadExecutor, observer=None):
        super().__init__(url, allow_exception, callback_executor)
        if observer is not None:
            self.add_observer(observer)

        # If under v2022, set RestrictMode.
        self.is_restrictedmode = False
        version = self.call('ak.wwise.core.getInfo')['version']
        if version['year'] < 2022:
            self.is_restrictedmode = True

        wproj = self.call("ak.wwise.core.object.get",
                          {"from": {"ofType": ["Project"]},
                           "options": {"return": ["name", "filePath"]}})['return'][0]
        self.__wproj_info = {'name': wproj['name'],
                             'filePath': wproj['filePath']}

        # {'StateGroup GUID': {'path': 'StateGroup Name',
        #                      'state': ['State Name', 'State Name', ...],
        #                      'current': 'State name'}
        self.__state_in_wwise = {}
        # { 'StateGroup GUID' : {'StateGroup':{'newName':NewStateGroup Path},
        #                        'State'     :{'id':State GUID,
        #                                      'oldName':OldState Name,
        #                                      'newName':NewState Name}}
        self.changed_statename = {}
        # { StateGroup GUID : NewState Name}
        self.changed_currentstate = {}

        self.update_state_info()
        self.set_subscription()

        self.notify_observer_of_waapi_connected()

    @property
    def wproj_info(self):
        return self.__wproj_info

    @property
    def state_in_wwise(self):
        return self.__state_in_wwise

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
        self.subscribe("ak.wwise.core.object.nameChanged",
                       self.on_statename_changed, {"return": ["type", "id", "name", "path", "parent"]})

        if not self.is_restrictedmode:
            self.subscribe("ak.wwise.core.profiler.stateChanged",
                           self.on_currentstate_changed, {"return": ["id", "name", "path"]})

    def update_state_info(self) -> dict:
        """Return State information.\n
        Returns:
            dict: State information.\n
            {'StateGroup GUID': {'path': 'StateGroup Path',
                                'state': ['State Name', 'State Name', ...],
                                'current': 'State name'}
        """
        ret = {}
        # Get All StateGroup Info.
        stategroup_list = self.call("ak.wwise.core.object.get", {
            "from": {
                "ofType": ["StateGroup"]},
            "options": {
                "return": ["id", "path"]}
        })['return']

        for stategroup in stategroup_list:
            ret[stategroup['id']] = {'path': stategroup['path']}

            # Get All State Info from Each StateGroup.
            state_list = self.call("ak.wwise.core.object.get", {
                "from": {
                    "id": [stategroup['id']]},
                "transform": [
                    {"select": ["children"]},
                    {"where": ["type:isIn", ["State"]]}],
                "options": {
                    "return": ["id", "name"]}
            })['return']

            # Add Each State as List.
            for state in state_list:
                ret[stategroup['id']].setdefault(
                    'state', []).append(state['name'])

            # Add current State info.
            if self.is_restrictedmode:
                ret[stategroup['id']].setdefault('current', 'None')
            else:
                test = self.call("ak.soundengine.getState", {
                    "stateGroup": stategroup['id'],
                    "options": {"return": ["id", "name", 'parent.id']}
                })
                ret[stategroup['id']].setdefault('current', self.call("ak.soundengine.getState", {
                    "stateGroup": stategroup['id'],
                    "options": {"return": ["id", "name", 'parent.id']}
                })['return'].get('name', 'None'))

        # Sort return dict by path.
        for k, v in sorted(ret.items(), key=lambda x: x[1]['path']):
            self.__state_in_wwise[k] = v

        return self.__state_in_wwise

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
        changedobj = kwargs["object"]
        # Process for StateGroup.
        if changedobj["type"] == "StateGroup":
            stategroupguid = changedobj["id"]
            self.changed_statename[stategroupguid] = {"StateGroup":
                                                      {'oldName': self.__state_in_wwise[stategroupguid]['path'],
                                                       'newName': changedobj["path"]}}
            self.__state_in_wwise[stategroupguid]['path'] = changedobj["path"]
            self.notify_observer_of_statename_changed()

        # Process for State.
        elif changedobj["type"] == "State":
            stategroupguid = changedobj["parent"]["id"]
            # Make new Changed State List.
            if not self.changed_statename.get(stategroupguid, {}).get("State", []):
                self.changed_statename[stategroupguid] = {"State": []}

            # Is Changed State already exist in changed_statename?
            if changedobj["id"] in [k['id'] for k in self.changed_statename[stategroupguid]['State']]:
                existed_id = [k['id']
                              for k in self.changed_statename[stategroupguid]['State']].index(changedobj["id"])
                self.changed_statename[stategroupguid]["State"][existed_id] = {'id': changedobj["id"],
                                                                               'oldName': kwargs.get("oldName", ""),
                                                                               'newName': kwargs.get("newName", "")}
            else:
                self.changed_statename[stategroupguid]["State"].append({'id': changedobj["id"],
                                                                        'oldName': kwargs.get("oldName", ""),
                                                                        'newName': kwargs.get("newName", "")})
            self.__state_in_wwise[stategroupguid]['state'][self.__state_in_wwise[stategroupguid]['state'].index(
                kwargs.get("oldName"))] = kwargs.get("newName")
            self.notify_observer_of_statename_changed()

        # Except for State/StateGroup.
        else:
            return

    def on_currentstate_changed(self, *args, **kwargs):
        self.__state_in_wwise[kwargs.get(
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
        print("*** Get Selected Object.")
        # print(client.call("ak.wwise.ui.getSelectedObjects"))
        #    options={
        #        "return": ["id", "name", "type", "shortId", "classId", "category", "filePath",
        #                   "workunit", "parent", "owner", "path", "workunitIsDefault", "workunitType", "workunitIsDirty",
        #                   "childrenCount"]}))

        # Get ProjectName and Path.
        # print("*** ProjectName and Path: get_wproj_info()")
        # print(client.update_wproj_info())

        # Get State List
        # print("*** Get State Dict: update_state_info()")
        # print(client.update_state_info())

        # client.set_state("{5ABE43F7-5E44-4F37-AE07-BC265DDCC34E}",
        #                  "{CD350719-7205-45AC-B57A-2FB2E1E492AD}")

        # print("*** Subscribe")
        # handler = client.set_subscription()

        client.disconnect()

        print("*** EOF")
