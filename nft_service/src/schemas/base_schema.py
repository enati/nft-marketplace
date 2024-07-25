from abc import ABC, abstractmethod

class BaseRequest:

    @classmethod
    def get_class_name(cls):
        return cls.__name__
