# Bugsnax Archipelago

An unofficial [Archipelago](https://archipelago.gg) randomiser for Bugsnax.

## Status

Currently in alpha. The core loop of catching, quests, tools, and final credits is working 
and has been tested end-to-end. Sauces and levels are yet to be randomised.
Expect this to be rough around the edges - please report anything weird to me via
[Issues](../../issues).

## Requirements

- Bugsnax (PC)
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) v.0.6.7 or later
- `pymem` (the client will offer to install this automatically on first run)

## Installation

Download the latest release from the [Releases page](../../releases) -- you need **both** files:

### 1. Install the apworld

1. Download `bugsnax.apworld`
2. Place it in your Archipelago install's `custom_worlds` folder

### 2. Install the mod

1. Download the mod `.zip`
2. Go to Bugsnax in your Steam library. Right click, manage -> browse local files
3. Place the mod directly into this Bugsnax root folder
4. This mod prevents story-quest tools (Sauce Slinger, Buggy Ball, Lunchpad, SnakGrappler, Trip Shot) from being handed out early by vanilla quest completion

### 3. Start a new game

The randomiser is **locked to save slot 2** - make sure to delete your save and start fresh on **save slot 2**

## Generating and playing

1. Generate a YAML using the options page for this game
2. Generate/host your seed as normal through Archipelago
3. Open the Archipelago Launcher and click **"Bugsnax Client"**
4. First run only: it'll offer to install `pymem` automatically
5. Enter your server address, slot name, and password (if any), and connect
6. Play! (On save slot 2)

## Options

| Option | Description |
|---|---|
| `golden_snax_required` | How many Golden Snax (MacGuffin item) you need to collect to goal, on top of beating the game. Range 1-50. |
| `golden_snax_extra` | Extra Golden Snax placed in the pool beyond what's required (padding, doesn't count toward the goal). Range 0-49, capped so required + extra never exceeds 50 total. |

## Known limitations

- Sauces are not randomised yet
- Region/area randomisation is not implemented
- `Bug Net` and `Snaktivator` exist in the item pool but can't be granted via memory yet

## Credits

- Apworld implementation: Robofett28
- Original concept and mod creation: Balenar