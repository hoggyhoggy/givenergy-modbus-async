import json
from typing import DefaultDict, Optional

from .register import (
    HR,
    IR,
    Register,
)


class RegisterCache(DefaultDict[Register, int]):
    """Holds a cache of Registers populated after querying a device."""

    def __init__(self, registers: Optional[dict[Register, int]] = None) -> None:
        if registers is None:
            registers = {}
        super().__init__(lambda: None, registers)

    def json(self) -> str:
        """Return JSON representation of the register cache, to mirror `from_json()`."""  # noqa: D402,D202,E501
        return json.dumps(self)

    @classmethod
    def from_json(cls, data: str) -> "RegisterCache":
        """Instantiate a RegisterCache from its JSON form."""

        def register_object_hook(object_dict: dict[str, int]) -> dict[Register, int]:
            """Rewrite the parsed object to have Register instances as keys instead of their (string) repr."""
            lookup = {"HR": HR, "IR": IR}
            ret = {}
            for k, v in object_dict.items():
                if k.find("(") > 0:
                    reg, idx = k.split("(", maxsplit=1)
                    idx = idx[:-1]
                elif k.find(":") > 0:
                    reg, idx = k.split(":", maxsplit=1)
                else:
                    raise ValueError(f"{k} is not a valid Register type")
                try:
                    ret[lookup[reg](int(idx))] = v
                except ValueError:
                    # unknown register, discard silently
                    continue
            return ret

        return cls(registers=(json.loads(data, object_hook=register_object_hook)))
