# URLs
baseUrl = http://server.example:26980
Prefix all URLs in this document with the value contained within `baseUrl`.
For authentication/authorization, all requests must include the headers `X-SDTD-API-TOKENNAME` and `X-SDTD-API-SECRET`. Credential values are intentionally omitted. Any previously published development credentials should be rotated if still valid.

## Get server info

### Request

GET `/api/serverinfo`

### Response

```json
{
	"data": [
		{
			"name": "GameType",
			"type": "string",
			"value": "7DTD"
		},
		{
			"name": "GameName",
			"type": "string",
			"value": "Sanitized Test Server"
		},
		{
			"name": "GameHost",
			"type": "string",
			"value": "Sanitized Test Host"
		},
		{
			"name": "ServerDescription",
			"type": "string",
			"value": "Sanitized server description"
		},
		{
			"name": "ServerWebsiteURL",
			"type": "string",
			"value": ""
		},
		{
			"name": "LevelName",
			"type": "string",
			"value": "Adino Mountains"
		},
		{
			"name": "GameMode",
			"type": "string",
			"value": "Survival"
		},
		{
			"name": "IP",
			"type": "string",
			"value": "192.0.2.10"
		},
		{
			"name": "SteamID",
			"type": "string",
			"value": "00000000000000000"
		},
		{
			"name": "ServerVersion",
			"type": "string",
			"value": "V.3.10.14"
		},
		{
			"name": "Platform",
			"type": "string",
			"value": "LinuxServer"
		},
		{
			"name": "ServerLoginConfirmationText",
			"type": "string",
			"value": ""
		},
		{
			"name": "Region",
			"type": "string",
			"value": "NorthAmericaEast"
		},
		{
			"name": "Language",
			"type": "string",
			"value": "English"
		},
		{
			"name": "UniqueId",
			"type": "string",
			"value": "00000000000000000000000000000000"
		},
		{
			"name": "CombinedPrimaryId",
			"type": "string",
			"value": "EOS_sanitized"
		},
		{
			"name": "CombinedNativeId",
			"type": "string",
			"value": ""
		},
		{
			"name": "PlayGroup",
			"type": "string",
			"value": "Standalone"
		},
		{
			"name": "SandboxPreset",
			"type": "string",
			"value": ""
		},
		{
			"name": "SandboxCode",
			"type": "string",
			"value": "SANITIZED"
		},
		{
			"name": "Port",
			"type": "int",
			"value": 26900
		},
		{
			"name": "CurrentPlayers",
			"type": "int",
			"value": 0
		},
		{
			"name": "MaxPlayers",
			"type": "int",
			"value": 8
		},
		{
			"name": "FreePlayerSlots",
			"type": "int",
			"value": 8
		},
		{
			"name": "GameDifficulty",
			"type": "int",
			"value": -1
		},
		{
			"name": "DayNightLength",
			"type": "int",
			"value": 60
		},
		{
			"name": "BloodMoonFrequency",
			"type": "int",
			"value": 7
		},
		{
			"name": "BloodMoonRange",
			"type": "int",
			"value": 0
		},
		{
			"name": "BloodMoonWarning",
			"type": "int",
			"value": 1
		},
		{
			"name": "ZombiesRun",
			"type": "int",
			"value": -1
		},
		{
			"name": "ZombieFeralSense",
			"type": "int",
			"value": 0
		},
		{
			"name": "ZombieMove",
			"type": "int",
			"value": 0
		},
		{
			"name": "ZombieMoveNight",
			"type": "int",
			"value": 3
		},
		{
			"name": "ZombieFeralMove",
			"type": "int",
			"value": 3
		},
		{
			"name": "ZombieBMMove",
			"type": "int",
			"value": 3
		},
		{
			"name": "XPMultiplier",
			"type": "int",
			"value": 500
		},
		{
			"name": "DayCount",
			"type": "int",
			"value": 3
		},
		{
			"name": "Ping",
			"type": "int",
			"value": -1
		},
		{
			"name": "DropOnDeath",
			"type": "int",
			"value": 1
		},
		{
			"name": "DropOnQuit",
			"type": "int",
			"value": 0
		},
		{
			"name": "BloodMoonEnemyCount",
			"type": "int",
			"value": 8
		},
		{
			"name": "EnemyDifficulty",
			"type": "int",
			"value": 0
		},
		{
			"name": "PlayerKillingMode",
			"type": "int",
			"value": 3
		},
		{
			"name": "CurrentServerTime",
			"type": "int",
			"value": 978976
		},
		{
			"name": "DayLightLength",
			"type": "int",
			"value": 18
		},
		{
			"name": "BlockDurabilityModifier",
			"type": "int",
			"value": -1
		},
		{
			"name": "BlockDamagePlayer",
			"type": "int",
			"value": 100
		},
		{
			"name": "BlockDamageAI",
			"type": "int",
			"value": 100
		},
		{
			"name": "BlockDamageAIBM",
			"type": "int",
			"value": 100
		},
		{
			"name": "AirDropFrequency",
			"type": "int",
			"value": 3
		},
		{
			"name": "LootAbundance",
			"type": "int",
			"value": 100
		},
		{
			"name": "LootRespawnDays",
			"type": "int",
			"value": 7
		},
		{
			"name": "MaxSpawnedZombies",
			"type": "int",
			"value": 64
		},
		{
			"name": "LandClaimCount",
			"type": "int",
			"value": 5
		},
		{
			"name": "LandClaimSize",
			"type": "int",
			"value": 41
		},
		{
			"name": "LandClaimDeadZone",
			"type": "int",
			"value": 30
		},
		{
			"name": "LandClaimExpiryTime",
			"type": "int",
			"value": 7
		},
		{
			"name": "LandClaimDecayMode",
			"type": "int",
			"value": 0
		},
		{
			"name": "LandClaimOnlineDurabilityModifier",
			"type": "int",
			"value": 4
		},
		{
			"name": "LandClaimOfflineDurabilityModifier",
			"type": "int",
			"value": 4
		},
		{
			"name": "LandClaimOfflineDelay",
			"type": "int",
			"value": 0
		},
		{
			"name": "PartySharedKillRange",
			"type": "int",
			"value": 100
		},
		{
			"name": "MaxSpawnedAnimals",
			"type": "int",
			"value": 50
		},
		{
			"name": "ServerVisibility",
			"type": "int",
			"value": 2
		},
		{
			"name": "BedrollExpiryTime",
			"type": "int",
			"value": 45
		},
		{
			"name": "BedrollDeadZoneSize",
			"type": "int",
			"value": 15
		},
		{
			"name": "WorldSize",
			"type": "int",
			"value": 6144
		},
		{
			"name": "MaxChunkAge",
			"type": "int",
			"value": -1
		},
		{
			"name": "DeathPenalty",
			"type": "int",
			"value": 1
		},
		{
			"name": "QuestProgressionDailyLimit",
			"type": "int",
			"value": 10
		},
		{
			"name": "AllowSpawnNearFriend",
			"type": "int",
			"value": 2
		},
		{
			"name": "StormFreq",
			"type": "int",
			"value": 100
		},
		{
			"name": "AISmellMode",
			"type": "int",
			"value": 3
		},
		{
			"name": "JarRefund",
			"type": "int",
			"value": 60
		},
		{
			"name": "IsDedicated",
			"type": "bool",
			"value": true
		},
		{
			"name": "IsPasswordProtected",
			"type": "bool",
			"value": false
		},
		{
			"name": "ShowFriendPlayerOnMap",
			"type": "bool",
			"value": true
		},
		{
			"name": "BuildCreate",
			"type": "bool",
			"value": false
		},
		{
			"name": "EACEnabled",
			"type": "bool",
			"value": false
		},
		{
			"name": "SanctionsIgnored",
			"type": "bool",
			"value": true
		},
		{
			"name": "Architecture64",
			"type": "bool",
			"value": true
		},
		{
			"name": "StockSettings",
			"type": "bool",
			"value": false
		},
		{
			"name": "StockFiles",
			"type": "bool",
			"value": true
		},
		{
			"name": "ModdedConfig",
			"type": "bool",
			"value": false
		},
		{
			"name": "RequiresMod",
			"type": "bool",
			"value": false
		},
		{
			"name": "AirDropMarker",
			"type": "bool",
			"value": true
		},
		{
			"name": "EnemySpawnMode",
			"type": "bool",
			"value": true
		},
		{
			"name": "IsPublic",
			"type": "bool",
			"value": true
		},
		{
			"name": "AllowSpawnNearBackpack",
			"type": "bool",
			"value": true
		},
		{
			"name": "AllowCrossplay",
			"type": "bool",
			"value": false
		},
		{
			"name": "BiomeProgression",
			"type": "bool",
			"value": true
		}
	],
	"meta": {
		"serverTime": "2026-08-21T21:12:06.2882390+00:00"
	}
}
```

## Get server stats

### Request

GET `/api/serverstats`

### Response

```json
{
	"data": {
		"gameTime": {
			"days": 41,
			"hours": 18,
			"minutes": 58
		},
		"players": 0,
		"hostiles": 0,
		"animals": 0
	},
	"meta": {
		"serverTime": "2026-08-21T21:18:47.8840500+00:00"
	}
}
```

## Get map config

### Request

GET `/api/map/config`

### Response

```json
{
	"data": {
		"enabled": true,
		"mapBlockSize": 128,
		"maxZoom": 4,
		"mapSize": {
			"x": 6144,
			"y": 255,
			"z": 6144
		}
	},
	"meta": {
		"serverTime": "2026-08-21T21:18:21.5521840+00:00"
	}
}
```

## Get online players

### Request

GET `/api/player`

### Response

```json
{
	"data": {
		"players": [
			{
				"entityId": 171,
				"name": "sanitized-player",
				"platformId": {
					"combinedString": "Steam_sanitized",
					"platformId": "Steam",
					"userId": "sanitized"
				},
				"crossplatformId": {
					"combinedString": "EOS_sanitized",
					"platformId": "EOS",
					"userId": "sanitized"
				},
				"totalPlayTimeSeconds": null,
				"lastOnline": null,
				"online": true,
				"ip": "192.0.2.20",
				"ping": 8,
				"position": {
					"x": 563.46875,
					"y": 38.09375,
					"z": -506.71875
				},
				"level": 116,
				"health": 300,
				"stamina": 250,
				"score": 1295,
				"deaths": 21,
				"kills": {
					"zombies": 1387,
					"players": 12
				},
				"banned": {
					"banActive": false,
					"reason": null,
					"until": null
				}
			}
		]
	},
	"meta": {
		"serverTime": "2026-08-21T21:29:58.1256990+00:00"
	}
}
```

## Get hostiles

### Request

GET `/api/hostile`

### Response

```json
{
	"data": [
		{
			"id": 9512,
			"name": "zombieScreamerRadiated",
			"position": {
				"x": 500,
				"y": 38,
				"z": -527
			}
		},
		{
			"id": 9513,
			"name": "zombieArleneRadiated",
			"position": {
				"x": 464,
				"y": 38,
				"z": -550
			}
		},
		{
			"id": 9514,
			"name": "zombieWightRadiated",
			"position": {
				"x": 507,
				"y": 38,
				"z": -496
			}
		},
		{
			"id": 9515,
			"name": "zombieSpider",
			"position": {
				"x": 456,
				"y": 38,
				"z": -516
			}
		},
		{
			"id": 9516,
			"name": "zombieArleneRadiated",
			"position": {
				"x": 471,
				"y": 38,
				"z": -494
			}
		},
		{
			"id": 9517,
			"name": "zombieMarleneFeral",
			"position": {
				"x": 474,
				"y": 38,
				"z": -503
			}
		}
	],
	"meta": {
		"serverTime": "2026-08-21T21:31:46.4740300+00:00"
	}
}
```

## Get animals

### Request

GET `/api/animal`

### Response

(I think a response that actually has some animals would look similar to the `/api/hostile` endpoint response)
```json
{
	"data": [],
	"meta": {
		"serverTime": "2026-08-21T21:33:05.1245840+00:00"
	}
}
```

## Send a command

### Observed message quoting

`say` broadcasts to every connected player. `pm`/`sayplayer` accepts a player name, Steam ID, or
entity ID and sends only to that player. Typed support uses entity IDs.

Controlled chat observations established:

- `say CLI test alpha bravo` displayed only `Server: CLI`.
- `say "CLI test alpha bravo"` displayed `Server: CLI test alpha bravo` to every player.
- `pm 171 CLI test alpha bravo` displayed only `From Server: CLI` to the target.
- `pm 171 "CLI test alpha bravo"` displayed the complete message only to the target.
- Quoted `CLI café apostrophe's test` preserved Unicode and the apostrophe.
- Wrapper double quotes were not displayed.

Double-quote escaping, backslashes, and command separators remain unverified. Typed builders reject
them.

### Observed kick behavior

`kick 171 "CLI moderation test"` immediately disconnected the target and displayed `CLI moderation
test` as the reason. Captured response data, with player identity sanitized:

```json
{
  "command": "kick",
  "parameters": "171 \"CLI moderation test\"",
  "result": "Kicking Player sanitized-player: CLI moderation test\n"
}
```

### Observed ban lifecycle

`ban add 171 3 minutes "CLI moderation test"` disconnected the target immediately. The game displayed
the expiry timestamp and unquoted reason. The response identified the active ban using the player's
cross-platform `combinedString`.

`ban list` returned:

```text
Ban list entries:
  Banned until - UserID (name) - Reason
  2026-08-22 22:32:20 - EOS_sanitized (sanitized-player) - CLI moderation test
```

`ban remove PLATFORM USER_ID` failed with an argument-count error. Removal accepts one combined
identity token. The active entry was removed only when supplied the value from
`players[n].crossplatformId.combinedString`:

```text
ban remove EOS_sanitized
```

After removal, `ban list` returned only its two header lines and the player reconnected successfully.
Using a non-banned Steam combined identity still returned `removed from ban list`; removal result text
therefore does not prove that a matching entry existed. Verify using a subsequent list or reconnection.

### Request

The string value assigned to `command` is equivalent to typing a command in the admin console.

The captured generic help catalog lists `gettime`, `saveworld`, and `shutdown`. This establishes
their presence and summaries only. Command-specific `help <command>` responses were unavailable in
the release-readiness environment, so helper syntax remains explicitly unverified. Neither
`saveworld` nor `shutdown` was executed during closure work.

POST `/api/command`

BODY
```json
{
    "command": "help"
}
```

### Response

```json
{
	"data": {
		"command": "help",
		"parameters": "",
		"result": "*** Generic Console Help ***\nTo get further help on a specific topic or command type (without the brackets)\n    help <topic / command>\n\nGeneric notation of command parameters:\n   <param name>              Required parameter\n   <entityId / player name>  Possible types of parameter values\n   [param name]              Optional parameter\n\n*** List of Help Topics ***\noutput => Prints commands to log file\noutputdetailed => Prints commands with details to log file\nsearch => Search for all commands matching a string\n* => Search for all commands matching a string\n\n*** List of Commands ***\n AccDecay SetAccDecay SetAccuracyDecay sad => Accuracy Decay for guns, show/hide/reset/<Decimal value>\n admin => Manage user permission levels\n AdminSpeed as => AdminSpeed\n agemap => Output debug map for chunk age/protection/save status.\n ai => AI commands\n aiddebug => Toggles AIDirector debug output.\n audio => Watch audio stats\n automation auto => Automation Script Runner\n automove => Player auto movement\n ban => Manage ban entries\n bents => Switches block entities on/off or counts them\n buff => Applies a buff to the local player\n buffplayer => Apply a buff to a player\n camera cam => Lock/unlock camera movement or load/save a specific camera position\n ccphysics => Enables or disables changes to CCPhysics layer interactions. Reloading the game session may be necessary to fully apply if changed.\n challenges => Complete certain challenges\n chunkcache cc => shows all loaded chunks in cache\n chunkobserver co => Place a chunk observer on a given position.\n chunkreset cr => resets the specified chunks\n commandpermission cp => Manage command permission levels\n config => Import/export config data from/to external file\n createwebuser => Create a web dashboard user account\n creativemenu cm => enables/disables the creativemenu\n cvar => Commands to set, get, track or list CVars.\n damagereset => Reset damage on all blocks in the currently loaded POI\n debuff => Removes a buff from the local player\n debuffplayer => Remove a buff from a player\n debuggamestats => GameStats commands\n debugjiggle dgj => \n debugmenu dm => enables/disables the debugmenu \n debugpanels => allows usage of debug display panels (F3 menu) via command console\n debugshot dbs => Creates a screenshot with some debug information\n debugweather => Dumps internal weather state to the console.\n decomgr => \"decomgr\": Saves a debug texture visualising the DecoOccupiedMap.\n\"decomgr state\": Saves a debug texture visualising the location/state of all of the DecoObjects saved in decorations.7dtd.\n discord dc => Toggle Discord debug window\n dms => Gives control over Dynamic Music functionality.\n Dynamic mesh zz => Dynamic mesh\n Dynamic mesh debug zd => Dynamic mesh debug\n dynamicproperties dprop => Dynamic Properties debugging\n enablerendering => Disable live map rendering\n exception => Throw an exception / log messages\n exhausted => Makes the player exhausted.\n expiryinfo => Prints location and expiry day/time for the next [x] chunks set to expire.\n exportcurrentconfigs => Exports the current game config XMLs\n exportprefab => Exports a prefab from a world area\n fallingblocks fb => FallingBlocks WIP Settings\n floatingorigin fo => \n ForceEventDate => Specify date for testing event dates\n fov => Camera field of view\n ftw fellthroughworld => Log the fell through world debug information for testing purposes.\n gamestage => Shows the gamestage of the local player\n getgamepref gg => Gets game preferences\n getgamestat ggs => Gets game stats\n getlogpath glp => Get the path of the logfile the game currently writes to\n getoptions => Gets game options\n getsandboxoptions gso => Gets the current game's Sandbox Options\n gettime gt => Get the current game time\n gfx => Graphics commands\n give  => give an item to a player (entity id or name)\n givequest => Gives a quest to the player or add to quest tier\n giveself => usage: giveself itemName [qualityLevel=6] [count=1] [putInInventory=false] [spawnWithMods=true]\n giveselfxp => usage: giveselfxp 10000\n givexp => Give XP to a player\n graph => Draws graphs on screen\n help => Help on console and specific commands\n invalidatecaches => Invalidate contents of web file caches\n jds => Server junk drone commands.\n junkDrone jd => Local player junk drone commands.\n kick => Kicks user with optional reason. \"kick playername reason\"\n kickall => Kicks all users with optional reason. \"kickall reason\"\n kill => Kill a given entity\n killall => Kill all entities\n lgo listgameobjects => List all active game objects\n lights => Light debugging\n listdlc dlcs => List the available DLC and their current entitlement status.\n listents le => lists all entities\n listitems li => lists all items that contain the given substring\n listplayerids lpi => Lists all players with their IDs for ingame commands\n listplayers lp => lists all players\n listthreads lt => lists all threads\n logenv => Log the process environment variables\n loggamestate lgs => Log the current state of the game\n loglevel => Telnet/Web only: Select which types of log messages are shown\n loot => Loot commands\n mapdata => Writes some map data to an image\n mem => Prints memory information and unloads resources or changes garbage collector\n memcl => Prints memory information on client and calls garbage collector\n memprofile mprof => Toggles screen Memory Profiler UI\n meshdatamanager mdm => Toggle the MeshDataManager\n mumblepositionalaudio mpa => Mumble Positional Audio related tools\n na => Test new HD stuff.\n networkclient netc => Client side network commands\n networkserver nets => Server side network commands\n newweathersurvival => Enables/disables new weather survival\n occlusion => Control OcclusionManager\n openiddebug => enable/disable OpenID debugging\n overlap => Toggle LocalPlayer's Character Controller Overlap Recovery\n overridemaxplayercount => Override Max Server Player Count\n pathtest => enable a path testing utility mode\n performanceprofiler pp => Performance Profiling Utility\n permissionsallowed pallowed pa => Apply a mask to permissions for testing purposes (respects the existing conditions though).\n pirs => tbd\n placeblockrotations pbr => Places all rotations of the currently held block\n placeblockshapes pbs => Places all shapes of the currently held variant helper block\n playerOwnedEntities poe => Lists player owned entities.\n playervisitmap pvm => Teleports the player through a rectangular area with optional memory logging\n pois => Switches distant POIs on/off\n poiwaypoints pwp => Adds waypoints for specified POIs.\n pplist => Lists all PersistentPlayer data\n prefab => Prefab commands\n prefabeditor prefabedit predit => Open the Prefab Editor\n prefabupdater => \n profilenetwork => Writes network profiling information\n profiler => Utilities for collection profiling data from a variety of sources\n profiling => Enable Unity profiling for 300 frames\n regionreset rr => Resets chunks within a target region, or for the entire map.\n reloadentityclasses rec => reloads entityclasses xml data.\n removequest => usage: removequest questname\n rendermap => render the current map to a file\n repairchunkdensity rcd => check and optionally fix densities of a chunk\n reply re => send a message to  the player who last sent you a PM\n resetallstats => Resets all achievement stats (and achievements when parameter is true)\n saveworld sa => Saves the world manually.\n say => Sends a message to all connected clients\n sayplayer pm => send a message to a single player\n ScreenEffect => Sets a screen effect\n sdcs => Control entity sex, race, and variant\n sdminfo => SaveDataManager Information\n setgamepref sg => sets a game pref\n setgamestat sgs => sets a game stat\n settargetfps => Set the target FPS the game should run at (upper limit)\n settempunit stu => Set the current temperature units.\n settime st => Set the current game time\n setwatervalue swv => Sets the water value for all flow-permitting blocks within the current selection area, specified in the range of 0 (empty) to 1 (full).\n show => Shows custom layers of rendering.\n showalbedo albedo => enables/disables display of albedo in gBuffer\n showchunkdata sc => shows some date of the current chunk\n showClouds => Artist command to show one layer of clouds.\n showhits => Show hit entity info\n shownexthordetime => Displays the wandering horde time\n shownormals norms => enables/disables display of normal maps in gBuffer\n showspecular spec => enables/disables display of specular values in gBuffer\n showswings => Show melee swing arc rays\n showtriggers => Sets the visibility of the block triggers.\n shutdown => shuts down the game\n signeditordebug sed => Toggles visibility of the Sign Editor debug panel. \n signtexman stm => Allows enabling/disabling the Sign Texture Manager and configuring various baking settings.\n sleep => Makes the main thread sleep for the given number of seconds (allows decimals)\n sleeper => Drawn or list sleeper info\n smoothpoi => Smoothens the POI\n smoothworldall swa => Applies some batched smoothing commands.\n spawnairdrop => Spawns an air drop\n spawnentity se => spawns an entity\n spawnentityat sea => Spawns an entity at a give position\n spawnscouts => Spawns zombie scouts\n SpawnScreen => Display SpawnScreen\n spawnsupplycrate => Spawns a supply crate where the player is\n spawnwandering spawnw => Spawn wandering entities\n spectator spectatormode sm => enables/disables spectator mode\n spectrum => Force a particular lighting spectrum.\n squarespiral sqs => Move the player chunk by chunk in a square spiral. Will start off paused and required un-pausing. Also gives god mode and flying at the start.\n stab => stability\n starve hungry food => Makes the player starve (optionally specify the amount of food you want to have in percent).\n switchview sv => Switch between fpv and tpv\n SystemInfo => List SystemInfo\n teleport tp => Teleport the local player\n teleportplayer tele => Teleport a given player\n teleportpoirelative tppr => Teleport the local player within the current POI\n testCensor tcc => Censorship testing toggle.\n testDismemberment tds => Dismemberment testing toggle.\n testloop => Test code in a loop\n testoccreport toccr => Test the occlusion manager self reporting to backtrace, requires Backtrace to be enabled at build creation\n thirsty => Makes the player thirsty (optionally specify the amount of water you want to have in percent).\n tls => Spams the log with until stopped\n tppoi => Open POI Teleporter window\n traderarea => ...\n transformdebug tdbg => Transform Debugging\n trees => Switches trees on/off\n twitch => usage: twitch <command> <params>\n twitchadmin => Twitch Admin Commands\n uioptions uio => Allows overriding of some options that control the presentation of the UI\n unlock => Force unlock inventories for everyone or a specific player.\n version => Get the currently running version of the game and loaded mods\n versionui => Toggle version number display\n visitmap => Visit an given area of the map. Optionally run the density check on each visited chunk.\n vpois visitpois => \n weather => Control weather settings\n weathersurvival => Enables/disables weather survival\n webpermission => Manage web permission levels\n webtokens => Manage web tokens\n whitelist => Manage whitelist entries\n worldchunkreset wcr => Resets all unprotected chunks across the world.\n wsmats workstationmaterials => Set material counts on workstations.\n xui => Execute XUi operations\n\n"
	},
	"meta": {
		"serverTime": "2026-08-21T21:14:03.5379820+00:00"
	}
}
```

## Get log events

This endpoint requires an SSE connection.

### Request

GET `/sse/?events=log`

### Response

an open event stream that sends events like:
```
event: logLine
data: {"id":204,"msg":"[Web] [SSE] 'log': Connection opened from 192.0.2.30:33892 (Left open: 1, total opened: 6, closed: 5)","type":"Log","trace":null,"isotime":"2026-08-21T21:39:02.3346510+00:00","uptime":"3935239"}
```

and

```
: KeepAlive
```

and probably many other types of things for which I don't currently have an example.

## Map tiles

### Request

GET `/map/2/-3/-5.png?t=1787347070059`

### Response

a 128px by 128px PNG file showing explored map content, or transparency where content has not been
rendered. Transparency, unexplored, invalid, and out-of-bounds semantics remain unclassified.

### Observed world-to-tile projection

For game `V 3.1.0 (b14)`, dashboard bundle evidence `22c85370…56b36b1`, `mapBlockSize=128`, and
native zooms `0–4`, dashboard source and sanitized live marker observations establish:

```text
span(zoom) = 128 × 2^(4 - zoom)
coord_a = floor(world_x / span)
coord_b = -floor(-world_z / span) - 1
```

Resulting bounds are `x ∈ [coord_a×span, (coord_a+1)×span)` and
`z ∈ (coord_b×span, (coord_b+1)×span]`. The dashboard maps player `x` and `z` into its map projection
and rewrites Leaflet tile Y as `-y-1`. Independent holdouts matched after forcing dashboard refresh.
Raw coordinates retain neutral names because other server/dashboard versions remain unverified.
Pixel conversion is unknown.

## Items

### Observed console search

`listitems` (alias `li`) accepts one search string and returns internal item names containing that
string. Captured request command:

```text
li resourceWood
```

Captured result:

```text
    resourceWoodBundle
    resourceWood
Listed 2 matching items.
```

A search with no matches returns only:

```text
Listed 0 matching items.
```

The typed client restricts the search argument to one conservative console token. `li *` is
documented by upstream as a full listing, but consumers should use `/api/item` for typed full-catalog
data instead.

### Request

GET `/api/item`

### Response

```json
{
	"data": [
		{
			"name": "terrStone",
			"localizedName": "Stone",
			"isBlock": true
		},
		{
			"name": "terrainFiller",
			"localizedName": "Topsoil Terrain Filler (POI)",
			"isBlock": true
		},
// ...many more items...
	],
	"meta": {
		"serverTime": "2026-08-22T14:57:31.5564900+00:00"
	}
}
```

## Entities

### Request

GET `/api/entityclass`

### Response

```json
{
	"data": [
		{
			"name": "playerMale",
			"id": 2001454542,
			"manualSpawnType": "None"
		},
		{
			"name": "playerFemale",
			"id": 2129337093,
			"manualSpawnType": "None"
		},
		{
			"name": "zombieTemplateMale",
			"id": -1767388301,
			"manualSpawnType": "None"
		},
// ...many more entities...
	],
	"meta": {
		"serverTime": "2026-08-22T14:59:04.5650420+00:00"
	}
}
```
