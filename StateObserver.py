#! python3

class Subject:
    def __init__(self):
        self.__observers = []

    def __del__(self):
        self.__observers = []

    def add_observer(self, observer):
        self.__observers.append(observer)

    def remove_observer(self, observer):
        self.__observers.remove(observer)

    def notify_observer_of_wproj_postclosed(self):
        for observer in self.__observers:
            observer.on_wproj_postclosed(self)

    def notify_observer_of_waapi_disconnected(self):
        for observer in self.__observers:
            observer.on_waapi_disconnected(self)

    def notify_observer_of_statename_changed(self):
        for observer in self.__observers:
            observer.on_statename_changed(self)

    def notify_observer_of_currentstate_changed(self):
        for observer in self.__observers:
            observer.on_currentstate_changed(self)

    __iadd__ = add_observer
    __isub__ = remove_observer


class Observer:
    def __init__(self):
        pass

    def on_waapi_disconnected():
        pass

    def on_statename_changed():
        pass

    def on_currentstate_changed():
        pass
