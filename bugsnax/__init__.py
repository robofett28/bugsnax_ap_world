"""
Bugsnax
"""
from BaseClasses import Region, Entrance, Location, Item, ItemClassification, Tutorial
from worlds.AutoWorld import World, WebWorld
from worlds.generic.Rules import set_rule
from worlds.LauncherComponents import Component, components, Type, launch_subprocess

from .Items import item_table, ItemData, FILLER_ITEM_NAMES, MAX_GOLDEN_SNAX
from .Locations import location_table
from .Options import BugsnaxOptions
from .Rules import location_rules


def _launch_client():
    try:
        from .client.launcher import launch
    except Exception:
        import os
        import tempfile
        import traceback
        tb = traceback.format_exc()
        log_path = os.path.join(tempfile.gettempdir(), "bugsnax_client_error.log")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(tb)
        except OSError:
            pass
        print(f"Bugsnax client failed to load. See {log_path}\n{tb}")
        return
    launch_subprocess(launch, name="BugsnaxClient")


components.append(Component("Bugsnax Client", func=_launch_client, component_type=Type.CLIENT))


class BugsnaxItem(Item):
    game = "Bugsnax"


class BugsnaxLocation(Location):
    game = "Bugsnax"


class BugsnaxWeb(WebWorld):
    theme = "partyTime"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up the Bugsnax randomizer for Archipelago multiworld games.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Balenar"],
        )
    ]


class BugsnaxWorld(World):
    """Bugsnax is a game about where players explore a mysterious island
    and attempt to find and capture the eponymous insectoid food creatures"""
    game = "Bugsnax"
    web = BugsnaxWeb()

    options_dataclass = BugsnaxOptions
    options: BugsnaxOptions

    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_name_to_id = location_table

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        snaxburg = Region("Snaxburg", self.player, self.multiworld)

        menu_exit = Entrance(self.player, "MenuToSnaxburg", menu)
        menu.exits.append(menu_exit)

        self.multiworld.regions += [menu, snaxburg]
        menu_exit.connect(snaxburg)

        for loc_name, loc_id in location_table.items():
            location = BugsnaxLocation(self.player, loc_name, loc_id, snaxburg)
            snaxburg.locations.append(location)
            if loc_name == "Complete the Final Mission":
                token_data = item_table["Story Complete Token"]
                location.place_locked_item(
                    BugsnaxItem("Story Complete Token", token_data.classification,
                                token_data.code, self.player))

        goal_event = BugsnaxLocation(self.player, "Bugsnax Goal", None, snaxburg)
        goal_event.place_locked_item(
            BugsnaxItem("Victory", ItemClassification.progression, None, self.player))
        snaxburg.locations.append(goal_event)

    def set_rules(self):
        for loc_name, rule in location_rules.items():
            location = self.multiworld.get_location(loc_name, self.player)
            set_rule(location, lambda state, rule=rule: rule(state, self.player))

        goal_tools = ["Sauce Slinger", "Buggy Ball", "Trip Shot", "SnakGrappler", "Lunchpad"]
        golden_snax_required = self.options.golden_snax_required.value

        def goal_rule(state, tools=goal_tools, required=golden_snax_required, player=self.player):
            return state.has_all(set(tools), player) and state.has("Golden Snax", player, required)

        goal_location = self.multiworld.get_location("Bugsnax Goal", self.player)
        set_rule(goal_location, goal_rule)

        self.multiworld.completion_condition[self.player] = \
            lambda state: state.has("Victory", self.player)

    def create_items(self):
        required = self.options.golden_snax_required.value
        extra = self.options.golden_snax_extra.value
        total_golden_snax = min(required + extra, MAX_GOLDEN_SNAX)
        unused = MAX_GOLDEN_SNAX - total_golden_snax

        filler_extra = {name: 0 for name in FILLER_ITEM_NAMES}
        if unused > 0:
            base_add = unused // len(FILLER_ITEM_NAMES)
            remainder = unused % len(FILLER_ITEM_NAMES)
            for i, name in enumerate(FILLER_ITEM_NAMES):
                filler_extra[name] = base_add + (1 if i < remainder else 0)

        pool: list[Item] = []
        for name, data in item_table.items():
            if name == "Story Complete Token":
                continue
            if name == "Golden Snax":
                count = total_golden_snax
            elif name in filler_extra:
                count = data.count + filler_extra[name]
            else:
                count = data.count

            for _ in range(count):
                pool.append(BugsnaxItem(name, data.classification, data.code, self.player))

        self.multiworld.itempool += pool

    def fill_slot_data(self):
        return {
            "golden_snax_required": self.options.golden_snax_required.value,
        }

    def get_filler_item_name(self) -> str:
        return "BUNGER!"
