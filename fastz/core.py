"""
Impedance models, data-structures, and calculations.

.. moduleauthor:: whileman133

"""

from abc import ABC, abstractmethod
from typing import Union, cast
import math
import numpy as np


class Z(ABC):
    """Abstract representation of an impedance element."""

    @property
    @abstractmethod
    def prefix(self) -> str:
        """Impedance prefix or reference designator (e.g. 'R', 'L', 'C', 'Z')."""
        pass

    @property
    def subscript(self) -> Union[str, int]:
        """Subscript for the impedance prefix, string or integer."""
        return self._subscript

    @subscript.setter
    def subscript(self, subs: Union[str, int]):
        self._subscript = subs

    @property
    def label(self):
        """
        Tag or label for this impedance formed by concatenating the prefix and subscript.
        """
        return f"{self.prefix}{self.subscript}"

    def __init__(self, subs: Union[str, int] = ''):
        self.subscript = subs

    def __add__(self, other: "Z") -> "SeriesZ":
        """
        Connect this impedance in series with another.

        :param Z other: The impedance to connect in series with this impedance.
        :return SeriesZ: Impedance object representing the series-connected impedance.
        """

        if type(self) is SeriesZ:
            # we're connecting another impedance in series with this composite series impedance;
            # merge the other impedance with this one to keep the operation flat
            s = cast(SeriesZ, self)
            s.merge(other)
            return s
        else:
            return SeriesZ(self, other)

    def __floordiv__(self, other: "Z") -> "ParallelZ":
        """
        Connect this impedance in parallel with another.

        :param Z other: The impedance to connect in parallel with this impedance.
        :return ParallelZ: Impedance object representing the parallel-connected impedance.
        """

        if type(self) is ParallelZ:
            # we're connecting another impedance in parallel with this composite parallel impedance;
            # merge the other impedance with this one to keep the operation flat
            s = cast(ParallelZ, self)
            s.merge(other)
            return s
        else:
            return ParallelZ(self, other)

    def __getitem__(self, subscript: Union[str, int]) -> "Z":
        """
        Assign a subscript to this impedance.

        .. note::

            Contrary to its normal use as an accessor on other objects such as lists, the subscript operator
            `[]` assigns a subscript to an impedance in place.

        :param subscript: The subscript to assign to the impedance
        :return Z: This impedance object.
        """

        self.subscript = subscript
        return self

    def breakfreq(self, labels: str) -> float:
        """
        Compute the frequency at which the impedance of two lumped elements contained in this impedance are equal.

        :param str labels: The whitespace-separated labels of two lumped elements making up this impedance object.
        :return float: The break frequency (in Hz), i.e. the frequency at which of the two elements'
            impedances intersect.
        :raises KeyError: when one or both of the elements cannot be found by the specified labels.
        :raises ValueError: when the elements' impedance curves do not intersect or the specified elements are not
            instances of R, L, or C.
        """

        elements = [self.subz(label) for label in labels.split()]
        elements_dict = {type(e).__name__: e for e in elements}
        element_set = set(elements_dict)

        if len(elements) != 2 or len(elements_dict) != 2:
            raise ValueError(f"Expected two lumped elements of different type for the break frequency calculation, "
                             f"got {len(elements_dict)} unique types out of {len(elements)} total supplied "
                             f"from argument '{labels}'.")

        if not element_set.issubset({'R', 'L', 'C'}):
            raise ValueError(f"Expected lumped elements of type R, L, and C, "
                             f"got types '{' '.join(elements_dict.keys())}' from argument '{labels}'.")

        # RC break frequency (Hz) = 1/(2*pi*R*C)
        if element_set == {'R', 'C'}:
            return 1.0 / 2.0 / math.pi / elements_dict['R'].value / elements_dict['C'].value

        # RL break frequency (Hz) = R/(2*pi*L)
        if element_set == {'R', 'L'}:
            return elements_dict['R'].value / 2.0 / math.pi / elements_dict['L'].value

        # LC break frequency (Hz) = 1/(2*pi*√LC)
        if element_set == {'L', 'C'}:
            return 1.0 / 2.0 / math.pi / math.sqrt(elements_dict['L'].value * elements_dict['C'].value)

    @abstractmethod
    def __call__(self, ff: Union[np.ndarray, float], **lumpedparam):
        """
        Return the complex representation of this impedance at a frequency or set of frequencies.

        :param ff: The cyclic frequency or frequencies (in Hz) at which to evaluate the impedance, float or 1D numpy array.
        :param lumpedparam: Dictionary of parameter values to associate with lumped elements.
            Keys identify the element by label (concatenation of prefix and subscript - e.g. 'R1', 'Lt', 'Cp', 'Zxy')
            Values temporarily replace existing element values loaded on construction of the element.
        :return: The complex impedance (in Ohms) at the specified frequency/frequencies, scalar or 1D numpy array.
        :raises ValueError: when any parameter cannot be matched to a lumped element using the provided label.
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        Construct a string representation of this impedance.
        """
        pass

    @abstractmethod
    def subz(self, label: str) -> "Z":
        """
        Fetch a labeled sub-impedance of this impedance from the internal impedance tree.

        .. note::

            If two or more sub-impedance's have the same label, the impedance returned is not well defined.
            It varies with the tree structure and traversal algorithm.

        :param str label: The label for which to search the impedance tree.
        :return Z: The first impedance found that matches the provided label.
        :raises KeyError: if an impedance with the given label is not found within the tree.
        """
        pass


# Series/parallel composites -------------------------------------------------------------------------------------------

class CompositeZ(Z, ABC):
    """Abstract tree node representing the connection of two or more impedance elements."""

    @property
    @abstractmethod
    def _operator(self):
        pass

    @property
    def prefix(self):
        return "Z"

    def __init__(self, *children: "Z", subscript=''):
        """
        Initialize a composite impedance object.

        :param children: Two or more impedance objects to include in this composite.
        :param subscript: The subscript to assign to this impedance object.
        :raises ValueError: when less than two impedance objects are supplied.
        """

        if len(children) < 2:
            raise ValueError(f"Two or more child impedances are required to construct "
                             f"a {type(self)}, {len(children)} given.")

        super().__init__(subscript)
        self._children = list(children)

    def __str__(self):
        text = f" {self._operator} ".join(str(z) for z in self._children)

        if self.subscript:
            return f"{self.label}:({text})"
        else:
            return f"({text})"

    def subz(self, label: str):
        if label == self.label:
            return self

        for z in self._children:
            try:
                return z.subz(label)
            except KeyError:
                pass

        raise KeyError(f"Could not locate impedance with the label '{label}' within '{self}'.")

    def merge(self, other: "Z"):
        """
        Merge another impedance with this composite impedance.

        .. note::

            If the impedance to be merged is a composite impedance of the same type as this impedance,
            then the merge is performed by adding each of the other impedance's children to this impedance's
            children list. The result is a flatter representation of series and parallel impedance combinations.

        :param Z other: The impedance to merge with this composite impedance.
        :return: None
        """

        if type(other) is type(self):
            # merge all of the children of the other impedance if it is a composite of the same type
            self._children.extend(cast(CompositeZ, other)._children)
        else:
            self._children.append(other)


class SeriesZ(CompositeZ):
    """Tree node representing series connection of two or more impedance elements."""

    @property
    def _operator(self):
        return '+'

    def __call__(self, ff, **lumpedparam):
        # recurse the tree and add the resulting impedance vectors
        return sum(z(ff, **lumpedparam) for z in self._children)


class ParallelZ(CompositeZ):
    """Tree node representing parallel connection of two or more impedance elements."""

    @property
    def _operator(self):
        return '||'

    def __call__(self, ff, **lumpedparam):
        # recurse the tree and parallel the resulting impedance vectors
        return 1 / sum(1 / z(ff, **lumpedparam) for z in self._children)


# Lumped elements ------------------------------------------------------------------------------------------------------

class LumpedElement(Z, ABC):
    """Abstract tree leaf representing a lumped-parameter element."""

    @property
    @abstractmethod
    def _unit(self):
        pass

    @property
    def value(self) -> float:
        return self._value

    def __init__(self, subscript='', v: float = None):
        super().__init__(subscript)
        self._value = v

    def __str__(self):
        if self._value is None:
            return f"{self.prefix}{self.subscript}"
        else:
            return f"{self.prefix}{self.subscript}[{self._value}{self._unit}]"

    def subz(self, label: str):
        if label == self.label:
            return self
        else:
            raise KeyError(f"Label '{label}' does not match '{self}'.")

    def _lookup_value(self, **lumpedparam):
        """
        Fetch the value of this lumped element from either (a) the provided dictionary or (b) the initial value.

        :raises ValueError: on failure to find a value.
        """

        name = f"{self.prefix}{self._subscript}"
        if name in lumpedparam:
            value = lumpedparam[name]
        else:
            value = self._value

        if value is None:
            raise ValueError(f"Value not found for element '{name}'.")

        return value


class R(LumpedElement):
    """Tree leaf modeling a resistor."""

    @property
    def prefix(self):
        return 'R'

    @property
    def _unit(self):
        return 'Ω'

    def __call__(self, ff, **lumpedparam):
        return np.ones_like(ff) * self._lookup_value(**lumpedparam)


class C(LumpedElement):
    """Tree leaf modeling a capacitor."""

    @property
    def prefix(self):
        return 'C'

    @property
    def _unit(self):
        return 'F'

    def __call__(self, ff, **lumpedparam):
        return 1/(1j * 2 * np.pi * ff * self._lookup_value(**lumpedparam))


class L(LumpedElement):
    """"Tree leaf modeling an inductor."""

    @property
    def prefix(self):
        return 'L'

    @property
    def _unit(self):
        return 'H'

    def __call__(self, ff, **lumpedparam):
        return 1j * 2 * np.pi *ff * self._lookup_value(**lumpedparam)
