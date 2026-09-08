from collections.abc import Iterable, Iterator, Sequence
from math import sqrt
from typing import Any, Self, SupportsIndex, overload, cast


class Vector(Sequence[float | int]):
    CLASS_LEN: int = 0
    DIM_ORDER: str = "xyzabcdef"

    def __init__(
        self,
        *args: float
        | tuple[int | float, ...]
        | list[int | float]
        | list[int]
        | list[float]
        | None,
    ) -> None:
        if self.__iscompatible(args):
            self._dim_pos = tuple(cast(tuple[int | float, ...], args))
        elif len(args) == 1 and self.__iscompatible(args[0]):
            self._dim_pos = tuple(cast(Iterable[int | float], args[0]))
        else:
            raise ValueError(
                f"cant initialise {self.__class__.__name__} with {args}"
            )

    def __pow__(self, other: float) -> Self:
        """
        give an exponent to each axis of a vector
        """
        if isinstance(other, (float, int)):
            return self.__class__(tuple(a**other for a in self))
        raise TypeError(f"cant pow {self} to {other}")

    def __mod__(self, other: Sequence[int | float]) -> Self:
        """
        Modulo of two vectors or a vector and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] % a_b[1] for a_b in zip(self, other))
            )
        raise TypeError(f"cant mod {self} to {other}")

    def __add__(self, other: Sequence[int | float]) -> Self:
        """
        Add two vectors or a vector and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] + a_b[1] for a_b in zip(self, other))
            )
        raise TypeError(f"cant add {self} to {other}")

    def __sub__(self, other: Sequence[int | float]) -> Self:
        """
        Subtract two vectors or a vector and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] - a_b[1] for a_b in zip(self, other))
            )
        raise TypeError(f"cant sub {self} to {other}")

    def __mul__(self, other: Sequence[int | float] | float) -> Self:
        """
        Multiply two vectors or a vector and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] * a_b[1]
                      for a_b in zip(self, cast(Sequence[int | float], other)))
            )
        elif isinstance(other, (float, int)):
            return self.__class__(tuple(a * other for a in self))

        raise TypeError(f"cant mul {self} to {other}")

    def __truediv__(self, other: Sequence[int | float] | float) -> Self:
        """
        Divide two vectors or a vector and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] / a_b[1]
                      for a_b in zip(self, cast(Sequence[int | float], other)))
            )
        elif isinstance(other, (float, int)):
            return self.__class__(tuple(a / other for a in self))
        raise TypeError(f"cant div {self} to {other}")

    def __floordiv__(self, other: Sequence[int | float] | float) -> Self:
        """
        Perform floor division on two vectors or a vector
        and a compatible iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(a_b[0] // a_b[1]
                      for a_b in zip(self, cast(Sequence[int | float], other)))
            )
        elif isinstance(other, (float, int)):
            return self.__class__(tuple(a // other for a in self))
        raise TypeError(f"cant floordiv {self} to {other}")

    def __iscompatible(self, other: Any) -> bool:
        """
        Check if another object is compatible with this vector for operations.
        """
        return bool(
            hasattr(other, "__iter__")
            and hasattr(other, "__len__")
            and len(other) == self.CLASS_LEN
            and all(isinstance(x, (float, int)) for x in other)
        )

    @property
    def pos(self) -> tuple[int | float, ...]:
        """
        Get the position of the vector as a tuple.
        """
        return tuple(self._dim_pos)

    def __iter__(self) -> Iterator[int | float]:
        """
        Iterate over the dimensions of the vector.
        """
        yield from self._dim_pos

    def __len__(self) -> int:
        """
        Get the number of dimensions in the vector.
        """
        return self.CLASS_LEN

    def __repr__(self) -> str:
        """
        Return a string representation of the vector.
        """
        clsname = self.__class__.__name__
        return f"{clsname}({', '.join([str(dim) for dim in self._dim_pos])})"

    def __str__(self) -> str:
        """
        Return a string representation of the vector.
        """
        clsname = self.__class__.__name__
        return f"{clsname}({', '.join([str(dim) for dim in self._dim_pos])})"

    def __format__(self, format_spec: Any) -> str:
        """
        Format the vector according to the given format specification.
        """
        result: list[int | float] = []
        for i in range(self.CLASS_LEN):
            if self.DIM_ORDER[i] in format_spec:
                result.append(self._dim_pos[i])
        return "(" + " ".join([str(a) for a in result]) + ")"

    def __round__(self, ndigits: SupportsIndex | None = None) -> Self:
        """
        Round the dimensions of the vector to the specified number of digits.
        """
        return self.__class__(tuple(round(s, ndigits) for s in self))

    def __eq__(self, value: object) -> bool:
        """
        Check if this vector is equal to another vector or compatible iterable.
        """
        if self.__iscompatible(value):
            return all(
                a == b
                for a, b in zip(
                    self, cast(Sequence[int | float], value)))
        raise TypeError(f"cant compare {self} to {value}")

    def __bool__(self) -> bool:
        """
        Return True if any dimension of the vector is non-zero.
        """
        return any(self._dim_pos)

    def __hash__(self) -> int:
        """
        Return a hash value for the vector based on its dimensions.
        """
        return hash(tuple(self))

    @overload
    def __getitem__(self, key: int, /) -> float | int:
        ...

    @overload
    def __getitem__(
        self,
            key: slice, /) -> Sequence[float | int]:
        ...

    def __getitem__(
        self,
            key: int | slice) -> int | float | Sequence[float | int]:
        """
        Get the value of a specific dimension by index.
        """
        return self._dim_pos.__getitem__(key)

    def __getattr__(self, name: str) -> int | float:
        """
        Get the value of a specific dimension by name.
        """
        if name in self.DIM_ORDER[0:self.CLASS_LEN]:  # fmt: skip
            value = self._dim_pos[self.DIM_ORDER.find(name)]
            return value
        raise AttributeError(
            f"cannot acces attribute {name} "
            f"for class {self.__class__.__name__}")

    def pythagore(self, other: Sequence[int | float]) -> float:
        if self.__iscompatible(other):
            return sqrt(sum(self.abs_diff(other) ** 2))
        else:
            raise ValueError(
                f"cant use pythagore for {self.__class__.__name__} with{other}"
            )

    def lerp(self, next: Any, delta: float) -> Self:
        """use linear interpolation between
        self and next using delta as proportion
        Args:
            next (Any): next value
            delta (float): proportion from self -> next
        Raises:
            ValueError: if the value is not compatible
        Returns:
            Self: a new vector of same size, with each dimension lerp with next
        """
        if self.__iscompatible(next):
            diff: Self = ((next - self) * delta)
            return self + diff
        else:
            raise ValueError(
                f"cant lerp {self.__class__.__name__} with {next}"
            )

    def abs_diff(self, other: Sequence[int | float]) -> Self:
        """
        calculate the sum of absolute differences between this vector
        and another compatible vector or iterable.
        """
        if self.__iscompatible(other):
            return self.__class__(
                tuple(abs(a_b[0] - a_b[1]) for a_b in zip(self, other))
            )
        raise TypeError(f"cant get abs_diff of  {self} to {other}")


class Pos2D(Vector):
    CLASS_LEN = 2


class ColorRGB(Vector):
    CLASS_LEN = 3
    DIM_ORDER = "RGB"
