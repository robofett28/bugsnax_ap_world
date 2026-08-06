"""
Items.py - item table.
"""
from typing import NamedTuple
from BaseClasses import ItemClassification

BASE_ID = 3874000

class ItemData(NamedTuple):
    code: int
    classification: ItemClassification
    count: int

item_table: dict[str, ItemData] = {
    'Sauce Slinger': ItemData(BASE_ID + 0, ItemClassification.progression, 1),
    'Buggy Ball': ItemData(BASE_ID + 2, ItemClassification.progression, 1),
    'Lunchpad': ItemData(BASE_ID + 3, ItemClassification.progression, 1),
    'SnakGrappler': ItemData(BASE_ID + 4, ItemClassification.progression, 1),
    'Trip Shot': ItemData(BASE_ID + 5, ItemClassification.progression, 1),
    'Golden Snax': ItemData(BASE_ID + 8, ItemClassification.progression, 50),
    'Story Complete Token': ItemData(BASE_ID + 9, ItemClassification.progression, 1),
    'BUNGER!': ItemData(BASE_ID + 10, ItemClassification.filler, 16),
    'BOPSICLE!': ItemData(BASE_ID + 11, ItemClassification.filler, 16),
    'STRABBY!': ItemData(BASE_ID + 12, ItemClassification.filler, 15),
    'CRAPPLE!': ItemData(BASE_ID + 13, ItemClassification.filler, 15),
}

FILLER_ITEM_NAMES = ['BUNGER!', 'BOPSICLE!', 'STRABBY!', 'CRAPPLE!']
MAX_GOLDEN_SNAX = 50
