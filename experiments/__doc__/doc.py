def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper


@my_decorator
def say_whee():
    print("Whee!")


class PP(object):
    """ Class PP bla bla """
    def __init__(self):
        """ __init__ ble ble ble """
        self.m1 = True
        """ Not for m1 """


print(PP.__doc__)
a = PP()
print(a.__init__.__doc__)
print(a.m1.__doc__)
