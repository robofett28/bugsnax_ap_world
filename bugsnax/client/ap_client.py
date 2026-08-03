"""
ap_client.py

Bugsnax Archipelago client, built on AP's own CommonClient/kvui stack --
"""
import asyncio
import re
import xml.etree.ElementTree as ET

from CommonClient import CommonContext, get_base_parser, gui_enabled, server_loop, logger

from .bugsnax_memory import get_pymem, read_item, write_item
from .bugsnax_paths import find_save_path
from .bug_capture_checks import BUG_CAPTURE_CHECKS, SPECIAL_LOCATIONS
from .item_name_translation import GRANTABLE_TOOLS, KNOWN_UNSUPPORTED, MOD_SUPPRESSED_TOOLS

GATE = "AnyToolOwnedGate"
POLL_INTERVAL = 0.5

QUEST_CHECKS = {
    "Collect Snak Trap": ("FilboMainQuest2", "Active"),
    "Collect Sauce Slinger": ("WambusMainQuest1", "Active"),
    "Collect Buggy Ball": ("GrambleMainQuest1", "Active"),
    "Collect SnakGrappler": ("GetHook", "ConditionMet"),
    "Collect Lunchpad": ("CromdoMainQuest1", "Active"),

    # --- Story missions (all require Sauce Slinger at minimum) ---
    "Gone Home!": ("FilboInterview", "Completed"),
    "Wambus Goes to Seed": ("WambusMainQuest5", "Completed"),
    "Mystery Grumpus!": ("MeetFloofty", "Completed"),
    "Beffica Gets Bored": ("BefficaMainQuest4", "Completed"),

    # --- Story missions (require Sauce Slinger + Buggy Ball) ---
    "Gramble Loses Sleep": ("GrambleMainQuest3", "Completed"),
    "Filbo's Cold Welcome": ("SmallCelebration", "Completed"),
    "Triffany Bones up": ("TriffanyMainQuest3", "Completed"),
    "Mail Time!": ("MailQuest1", "Completed"),
    "Wiggle Rocks The Beach": ("WiggleMainQuest3", "Completed"),
    "Snaxburg Gets Spooked": ("GhostStories4", "Completed"),
    "Get Hooked": ("GetHook", "Completed"),

    # --- Story missions (require Sauce Slinger + Buggy Ball + Lunchpad) ---
    "Cromdo Cashes In": ("CromdoMainQuest4", "Completed"),

    # --- Story missions (require Sauce Slinger + Buggy Ball + Trip Shot + SnakGrappler) ---
    "Snorpy Goes Outside": ("SnorpyMainQuest3", "Completed"),
    "Chandlo Lives Large": ("ChandloMainQuest5", "Completed"),

    # --- Story missions (require Sauce Slinger + Buggy Ball + Trip Shot + SnakGrappler + Lunchpad) ---
    "Snaxburg Isn't Safe": ("TheIntruder2", "Completed"),
    "Floofty Changes Everything": ("FlooftyMainQuest4", "Completed"),
    "Shelda Speaks in Riddles": ("SheldaMainQuest4", "Completed"),
    "Eggabell Keeps Her Cool": ("EggabellMainQuest3", "Completed"),
}

GOAL_AREA_KEY = "GameCurrentArea"
GOAL_TARGET_VALUE = "$LevelCredits"
DEFAULT_GOLDEN_SNAX_REQUIRED = 20
FILLER_ITEMS = {"BUNGER!", "BOPSICLE!", "STRABBY!", "CRAPPLE!"}


def read_save_sections(save_path):
    text = save_path.read_text(encoding="utf-16", errors="ignore")
    text = text.replace("\ufeff", "").replace("\x00", "")
    chunks = re.split(r"<\?xml[^>]*\?>", text, flags=re.IGNORECASE)

    sections = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            root = ET.fromstring(chunk)
        except ET.ParseError:
            return None
        values = {}
        for child in root:
            name = child.get("name")
            value = child.get("value")
            if name is not None:
                values[name] = value
        sections[root.tag] = values
    return sections


def quest_status(value):
    if value is None:
        return None
    return value.split(";")[0]


class BugsnaxContext(CommonContext):
    game = "Bugsnax"
    items_handling = 0b111

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.pm = None
        self.save_path = None
        self.item_id_to_name = {}
        self.location_name_to_id = {}
        self.checked_locations_local = set()
        self.last_captured_state = {}
        self.last_quest_status = {}
        self.last_area_state = {}
        self.baseline_established = False

        self.goaled = False
        self.reached_credits = False
        self.golden_snax_count = 0
        self.golden_snax_required = DEFAULT_GOLDEN_SNAX_REQUIRED

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_msgs([{"cmd": "GetDataPackage", "games": [self.game]}])
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        super().on_package(cmd, args)

        if cmd == "DataPackage":
            game_data = args["data"]["games"].get(self.game)
            if game_data:
                item_name_to_id = game_data["item_name_to_id"]
                self.item_id_to_name = {v: k for k, v in item_name_to_id.items()}
                self.location_name_to_id = game_data["location_name_to_id"]
                logger.debug(f"Got {len(item_name_to_id)} items, "
                            f"{len(self.location_name_to_id)} locations from DataPackage.")

        elif cmd == "Connected":
            self.checked_locations_local = set()
            self.last_captured_state = {}
            self.last_quest_status = {}
            self.last_area_state = {}
            self.baseline_established = False
            self.goaled = False
            self.reached_credits = False
            self.golden_snax_count = 0
            logger.debug(f"Connected! Slot: {self.slot}")
            slot_data = args.get("slot_data") or {}
            required = slot_data.get("golden_snax_required")
            if required is not None:
                self.golden_snax_required = required
            else:
                logger.warning(f"golden_snax_required missing from slot_data, "
                                f"using default of {DEFAULT_GOLDEN_SNAX_REQUIRED}.")
            logger.debug(f"Goal: reach credits AND collect {self.golden_snax_required} Golden Snax.")

            if SPECIAL_LOCATIONS:
                logger.debug(f"Note: not auto-detecting these (need separate logic later): "
                            f"{', '.join(SPECIAL_LOCATIONS)}")

            if self.pm is None:
                self.pm = get_pymem()
            if self.save_path is None:
                self.save_path = find_save_path()
                logger.debug(f"Using save file: {self.save_path}")

        elif cmd == "ReceivedItems":
            for item in args["items"]:
                item_id = item.item if hasattr(item, "item") else item["item"]
                item_name = self.item_id_to_name.get(item_id, f"<unknown {item_id}>")
                logger.debug(f"Received item: {item_name}")
                asyncio.create_task(self.apply_item(item_name))

    async def apply_item(self, item_name):
        if item_name in GRANTABLE_TOOLS:
            internal = GRANTABLE_TOOLS[item_name]
            grant_value = 2 if internal in MOD_SUPPRESSED_TOOLS else 1
            write_item(self.pm, GATE, max(read_item(self.pm, GATE), 1))
            write_item(self.pm, f"{internal}_Selectable", grant_value)
            logger.debug(f"  Granted {item_name} via memory write (value={grant_value}).")
            return

        if item_name == "Golden Snax":
            self.golden_snax_count += 1
            logger.debug(f"  Golden Snax: {self.golden_snax_count}/{self.golden_snax_required} "
                        f"(server-side tracking only, no memory write needed)")
            await self.maybe_send_goal()
            return

        if item_name in FILLER_ITEMS:
            logger.debug(f"  ({item_name} -- junk filler, nothing to grant)")
            return

        if item_name in KNOWN_UNSUPPORTED:
            logger.debug(f"  (can't grant {item_name!r} yet: {KNOWN_UNSUPPORTED[item_name]})")
            return

        logger.debug(f"  (unrecognized item {item_name!r}, skipping)")

    async def maybe_send_goal(self):
        if self.goaled:
            return
        if self.reached_credits and self.golden_snax_count >= self.golden_snax_required:
            await self.send_goal()

    async def send_goal(self):
        if self.goaled:
            return
        self.goaled = True
        logger.debug(f"Goal complete! (credits reached, {self.golden_snax_count}/"
                    f"{self.golden_snax_required} Golden Snax) -- declaring victory!")
        await self.send_msgs([{"cmd": "StatusUpdate", "status": 30}])

    def send_location_check(self, loc_name):
        loc_id = self.location_name_to_id.get(loc_name)
        if loc_id is None:
            logger.warning(f"no location id for {loc_name!r}")
            return
        self.checked_locations_local.add(loc_name)
        asyncio.create_task(self.send_msgs([{"cmd": "LocationChecks", "locations": [loc_id]}]))

    def run_gui(self):
        from kvui import GameManager

        class BugsnaxManager(GameManager):
            logging_pairs = [("Client", "Archipelago")]
            base_title = "Bugsnax Client"

        self.ui = BugsnaxManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")


async def bugsnax_watcher(ctx: BugsnaxContext):
    """Background task: this watches the save file for captures/quest transitions/
    the credits transition, same detection logic as the previous version,
    now writing into ctx instead of self."""
    while True:
        if ctx.exit_event.is_set():
            return

        if ctx.save_path is not None and ctx.server is not None:
            sections = read_save_sections(ctx.save_path)
            if sections is not None:
                captured = sections.get("Captured", {})
                quests = sections.get("Quests", {})
                save = sections.get("Save", {})

                if not ctx.baseline_established:
                    pre_existing_captures = [k for k in BUG_CAPTURE_CHECKS.values() if captured.get(k) is not None]
                    if pre_existing_captures:
                        logger.warning(
                            f"NOTICE: your slot 2 save already has {len(pre_existing_captures)} "
                            f"capture(s) from BEFORE this session started. If this was supposed to "
                            f"be a fresh randomiser run, disconnect now, delete Bugsnax2.save, and "
                            f"start a truly new game before reconnecting."
                        )
                    ctx.last_captured_state = dict(captured)
                    ctx.last_quest_status = {
                        q: quest_status(quests.get(q))
                        for (q, _t) in QUEST_CHECKS.values() if quests.get(q) is not None
                    }
                    ctx.last_area_state = dict(save)
                    ctx.baseline_established = True

                for loc_name, save_key in BUG_CAPTURE_CHECKS.items():
                    if loc_name in ctx.checked_locations_local:
                        continue
                    new_val = captured.get(save_key)
                    old_val = ctx.last_captured_state.get(save_key)
                    if new_val is not None and old_val is None:
                        logger.debug(f"Detected capture: {loc_name}. Sending check...")
                        ctx.send_location_check(loc_name)
                    if new_val is not None:
                        ctx.last_captured_state[save_key] = new_val

                for loc_name, (quest_name, target_status) in QUEST_CHECKS.items():
                    if loc_name in ctx.checked_locations_local:
                        continue
                    new_status = quest_status(quests.get(quest_name))
                    old_status = ctx.last_quest_status.get(quest_name)
                    if new_status == target_status and old_status != target_status:
                        logger.debug(f"Detected '{quest_name}' -> {target_status}. "
                                    f"Sending check for '{loc_name}'...")
                        ctx.send_location_check(loc_name)
                    if new_status is not None:
                        ctx.last_quest_status[quest_name] = new_status

                new_area = save.get(GOAL_AREA_KEY)
                old_area = ctx.last_area_state.get(GOAL_AREA_KEY)
                if new_area == GOAL_TARGET_VALUE and old_area != GOAL_TARGET_VALUE:
                    ctx.reached_credits = True
                    logger.debug(f"Reached $LevelCredits. ({ctx.golden_snax_count}/"
                                f"{ctx.golden_snax_required} Golden Snax so far)")
                    await ctx.maybe_send_goal()
                if new_area is not None:
                    ctx.last_area_state[GOAL_AREA_KEY] = new_area

        await asyncio.sleep(POLL_INTERVAL)


async def main(args):
    ctx = BugsnaxContext(args.connect, args.password)
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    ctx.watcher_task = asyncio.create_task(bugsnax_watcher(ctx), name="BugsnaxWatcher")

    await ctx.exit_event.wait()
    ctx.server_address = None
    await ctx.shutdown()


def launch():
    import colorama
    parser = get_base_parser()
    args = parser.parse_args()
    colorama.init()
    asyncio.run(main(args))
    colorama.deinit()


if __name__ == "__main__":
    launch()
