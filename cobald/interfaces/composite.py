import abc
from typing import List


from .pool import Pool


class CompositePool(Pool):
    """
    Multiple providers for a number of indistinguishable resources
    """
    @property
    @abc.abstractmethod
    def supply(self):
        """The volume of resources that is provided by this pool"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def demand(self):
        """The volume of resources to be provided by this pool"""
        raise NotImplementedError

    @demand.setter
    @abc.abstractmethod
    def demand(self, value):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def utilisation(self) -> float:
        """Fraction of the provided resources which are actively used"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def allocation(self) -> float:
        """Fraction of the provided resources which are assigned for usage"""
        raise NotImplementedError

    @abc.abstractmethod
    @property
    def children(self) -> List[Pool]:
        """The individual resource providers making up this pool"""
        raise NotImplementedError

    @abc.abstractmethod
    @children.setter
    def children(self, value: List[Pool]):
        raise NotImplementedError