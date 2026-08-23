"""Read-only item catalog and server-side item search resource."""

import re

from sevendtd.admin.builders import SAFE_ITEM_NAME, prepare_search_items
from sevendtd.exceptions import SevenDTDCommandError
from sevendtd.models.catalogs import ItemCatalog, ItemDefinition, ItemSearchResult
from sevendtd.models.commands import CommandResult
from sevendtd.resources.commands import CommandsNamespace
from sevendtd.transport.http import HTTPTransport

SEARCH_SUMMARY = re.compile(r"Listed ([0-9]+) matching items\.", flags=re.ASCII)


def parse_item_search_result(query: str, result: CommandResult) -> ItemSearchResult:
    lines = result.result.splitlines()
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        raise SevenDTDCommandError("item search response is missing its result summary")

    summary = SEARCH_SUMMARY.fullmatch(lines[-1])
    if summary is None:
        raise SevenDTDCommandError("item search response has an invalid result summary")

    names: list[str] = []
    for line in lines[:-1]:
        if not line.startswith("    "):
            raise SevenDTDCommandError("item search response contains an unexpected item line")
        name = line[4:]
        if SAFE_ITEM_NAME.fullmatch(name) is None:
            raise SevenDTDCommandError("item search response contains an unsafe item name")
        names.append(name)

    total = int(summary.group(1))
    if len(names) != total:
        raise SevenDTDCommandError("item search response count does not match its result summary")
    return ItemSearchResult(
        query=query,
        names=tuple(names),
        total=total,
        observed_at=result.observed_at,
        raw_result=result.result,
    )


class ItemsNamespace:
    def __init__(self, transport: HTTPTransport, commands: CommandsNamespace) -> None:
        self._transport = transport
        self._commands = commands

    async def all(self) -> ItemCatalog:
        data, meta = await self._transport.request_json(
            "GET", "/api/item", list[ItemDefinition], resource="items.all"
        )
        return ItemCatalog(items=tuple(data), observed_at=meta.server_time)

    async def search(self, query: str) -> ItemSearchResult:
        prepared = prepare_search_items(query)
        result = await self._commands.execute(
            prepared.text,
            operation=prepared.metadata.name,
            risk=prepared.metadata.risk.value,
        )
        return parse_item_search_result(query, result)
