import dataclasses

@dataclasses.dataclass
class ChickenNuggetsItem:
    name: str
    quantity: int | None = None
    fries: bool | None = None


@dataclasses.dataclass
class HamburgerItem:
    name: str
    fries: bool | None = None
    pickles: bool | None = None
    lettuce: bool | None = None
    tomatoes: bool | None = None
