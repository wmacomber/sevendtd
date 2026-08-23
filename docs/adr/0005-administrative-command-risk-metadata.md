# ADR 0005: Administrative risk metadata

Accepted. Prepared commands carry advisory risk. Library does not authorize. Raw execution remains.
Free-text helpers remain unavailable until game-console quoting is demonstrated against a live
server for that command grammar.

Captured generic help lists `gettime`, `saveworld`, and `shutdown`, establishing command presence
but not command-specific syntax. Their established public helpers remain for compatibility, with
unchanged raw commands and risks. Per-operation metadata marks their syntax unverified until
read-only `help <command>` evidence becomes available. Shutdown is never executed for verification;
world save is not executed automatically.

The verified `give` helper targets an integer entity ID, accepts one conservatively validated item
token, requires positive amount, and restricts optional quality to `1–6`. It is classified
`MUTATING`. CLI performs an exact item-catalog preflight unless explicitly bypassed.

The verified `li` item-search command uses the same prepared-command metadata path and is classified
`READ_ONLY`. Its query and raw result remain excluded from command logs.

Live observation established that `say` and `pm` consume only one unquoted word, while double-quoted
text preserves spaces, printable Unicode, and apostrophes without displaying wrapper quotes. Typed
builders therefore quote the complete message and reject unverified quote, backslash, control, and
separator characters. Both operations are classified `MUTATING`; CLI messaging deliberately avoids
confirmation because communication is its primary effect. Arguments and results remain excluded
from logs.

Controlled observation verified that `kick ENTITY_ID "REASON"` immediately disconnects the target
and displays the unquoted reason. Typed kick uses integer entity IDs, shares the verified text
validator, is classified `MUTATING`, and requires CLI confirmation unless `--yes` is supplied.

Controlled observation verified `ban add ENTITY_ID DURATION UNIT "REASON"`, `ban list`, and
`ban remove COMBINED_IDENTITY`. Ban creation is `DESTRUCTIVE`, listing is `READ_ONLY`, and removal is
`MUTATING`. Removal requires the cross-platform `combined_string` recorded in the ban entry; separate
platform/user arguments fail. Upstream removal text is non-authoritative because an unrelated Steam
identity produced the same success wording. Consumers must verify removal through a subsequent list
or successful reconnection.
