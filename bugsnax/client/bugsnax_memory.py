"""
bugsnax_memory.py

Shared pointer-chain resolver for Bugsnax memory addresses.

Add new items to ITEM_CHAINS format:

    "ItemName": {
        "base_offset": 0x760E00,     # from "Bugsnax.exe"+XXXXXX
        "offsets": [0x2D8],          # rows top-to-bottom from the pointer
                                      # popup; last one is NOT dereferenced
    }
"""

import pymem
import pymem.process

PROCESS_NAME = "Bugsnax.exe"

# The build hash and ID of the version the AP is made for
# before touching any funny memory stuff, recorded here for reference.
KNOWN_BUILD_SHA256 = "C63B2DE643E7376499DF42DD2E3A25AF453E7EE92AA703CBD31A2EDC218A219F"
KNOWN_BUILD_ID = "24392074"

# The 6 progression tools - Hookshot NO LONGER WIP :)
CORE_TOOLS = [
    "StrabbyBall",
    "SnapTrap",
    "Hookshot",
    "Slingshot",
    "Launchpad",
    "Tripwire",
]

ITEM_CHAINS = {
    "Ketchup": {
        "base_offset": 0x760E00,
        "offsets": [0xC0, 0x20, 0x10, 0xB8, 0x28],
    },
    # NOTE: this is NOT per-item. It's a shared gate that controls whether
    # the toolwheel menu is willing to open at all ("do you own ANY tool").
    # Write it once as it's not part of granting a specific item.
    "AnyToolOwnedGate": {
        "base_offset": 0x760E00,
        "offsets": [0x2D8],
    },
    # Full toolwheel Selectable array
    "StrabbyBall_Selectable": {  # n=0
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0x78, 0x28],
    },
    "SnapTrap_Selectable": {  # n=1
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0x80, 0x28],
    },
    "SnaxScope_Selectable": {  # n=2
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0x88, 0x28],
    },
    "Hookshot_Selectable": {  # n=3
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0x90, 0x28],
    },
    "Slingshot_Selectable": {  # n=4
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0x98, 0x28],
    },
    "Launchpad_Selectable": {  # n=5
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0xA0, 0x28],
    },
    "Tripwire_Selectable": {  # n=6
        "base_offset": 0x760E00,
        "offsets": [0x138, 0x20, 0x10, 0xA8, 0x28],
    },
    "BugsnaxFile_Selectable": {  # n=7
        "base_offset": 0x760E00,      # Im deadass not even sure what this item is, but its in the array *shrug emoji* its probably the journal - Rob
        "offsets": [0x138, 0x20, 0x10, 0xB0, 0x28],  # The array ends here
    },
}

def get_pymem() -> pymem.Pymem:
    return pymem.Pymem(PROCESS_NAME)


def resolve_chain(pm: pymem.Pymem, base_offset: int, offsets: list[int]) -> int:
    module = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME)
    addr = pm.read_longlong(module.lpBaseOfDll + base_offset)
    for offset in offsets[:-1]:
        addr = pm.read_longlong(addr + offset)
    return addr + offsets[-1]


def resolve_item(pm: pymem.Pymem, item_name: str) -> int:
    if item_name not in ITEM_CHAINS:
        raise KeyError(f"No known chain for {item_name!r}. Known items: {list(ITEM_CHAINS)}")
    chain = ITEM_CHAINS[item_name]
    return resolve_chain(pm, chain["base_offset"], chain["offsets"])


def read_item(pm: pymem.Pymem, item_name: str) -> int:
    return pm.read_int(resolve_item(pm, item_name))


def write_item(pm: pymem.Pymem, item_name: str, value: int) -> None:
    pm.write_int(resolve_item(pm, item_name), value)