def main():
    m = ConcreteModel()
    m.add_observer(NumView())
    m.add_observer(ExcelView())
    for i in [5, 10, 15]:
        m.num = i


# Subject
class Model:
    def __init__(self):
        self.__observers = []
        self.__num = None

    def add_observer(self, observer):
        self.__observers.append(observer)

    def notify_observer(self):
        for observer in self.__observers:
            observer.update(self)


class Observer:
    def __init__(self):
        pass

    def update():
        pass


# ConcreteSubject
class ConcreteModel(Model):
    def __init__(self):
        super().__init__()

    @property
    def num(self):
        return self.__num

    @num.setter
    def num(self, num):
        self.__num = num
        self.notify_observer()  # important point


# ConcreteObserver1
class NumView(Observer):
    def __init__(self):
        pass

    # ここも大事
    def update(self, model):
        s = "NView: {}".format(model.num)
        print(s)


# ConcreteObserver2
class ExcelView(Observer):
    def __init__(self):
        pass

    # ここも大事
    def update(self, model):
        s = "EView: {}".format("*" * model.num)
        print(s)


if __name__ == "__main__":
    main()
