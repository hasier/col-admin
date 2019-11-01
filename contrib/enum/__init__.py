from typing import Tuple, Any, Generator, Iterable


class ChoiceEnumMixin(object):
    @classmethod
    def choices(cls: Iterable) -> Generator[Tuple[str, Any], None, None]:
        return ((choice.name, choice.value) for choice in cls)
