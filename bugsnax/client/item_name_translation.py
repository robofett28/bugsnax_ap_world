"""
item_name_translation.py

"""

# apworld item name -> bugsnax_memory internal name
GRANTABLE_TOOLS = {
    "Buggy Ball": "StrabbyBall",
    "Snak Trap": "SnapTrap",    # Not used as of now
    "SnakGrappler": "Hookshot",
    "Sauce Slinger": "Slingshot",
    "Lunchpad": "Launchpad",
    "Trip Shot": "Tripwire",
}

MOD_SUPPRESSED_TOOLS = {"StrabbyBall", "Slingshot", "Launchpad", "Hookshot", "Tripwire"}

# Items that exist in the pool but we can't grant yet (this is more laziness on my behalf - Rob)
KNOWN_UNSUPPORTED = {
    "Bug Net": "special case — checked by existence, not value (see notes)",
    "Snaktivator": "not yet hunted — entangled with the eating system",
}