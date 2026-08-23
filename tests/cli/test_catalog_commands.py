from datetime import UTC, datetime
from typing import Any

import pytest
from typer.testing import CliRunner

import sevendtd.cli.app as cli_module
from sevendtd.models.catalogs import (
    EntityClass,
    EntityClassCatalog,
    ItemCatalog,
    ItemDefinition,
    ItemSearchResult,
)
from sevendtd.models.commands import CommandResult

runner = CliRunner()


def item_catalog() -> ItemCatalog:
    return ItemCatalog(
        items=(
            ItemDefinition(name="terrStone", localizedName="Stone", isBlock=True),
            ItemDefinition(name="resourceYuccaFibers", localizedName="Yucca Fibers", isBlock=False),
        ),
        observed_at=datetime.now(UTC),
    )


def command_result() -> CommandResult:
    return CommandResult(
        command="give",
        parameters="171 terrStone 1",
        result="ok",
        observed_at=datetime.now(UTC),
    )


def message_result(command: str, parameters: str) -> CommandResult:
    return CommandResult(
        command=command,
        parameters=parameters,
        result="ok",
        observed_at=datetime.now(UTC),
    )


def test_catalog_filters_are_case_insensitive() -> None:
    catalog = item_catalog()
    assert [item.name for item in catalog.search("yucca").items] == ["resourceYuccaFibers"]
    assert [item.name for item in catalog.search("", blocks_only=True).items] == ["terrStone"]
    classes = EntityClassCatalog(
        items=(EntityClass(name="zombieTemplateMale", id=-1, manualSpawnType="None"),),
        observed_at=datetime.now(UTC),
    )
    assert len(classes.search("ZOMBIE").items) == 1


def test_item_search_command_emits_json(monkeypatch: pytest.MonkeyPatch) -> None:
    observed = ItemSearchResult(
        query="resourceWood",
        names=("resourceWoodBundle", "resourceWood"),
        total=2,
        observed_at=datetime.now(UTC),
        raw_result="    resourceWoodBundle\n    resourceWood\nListed 2 matching items.\n",
    )
    monkeypatch.setattr(cli_module, "run", lambda state, operation: observed)

    result = runner.invoke(cli_module.app, ["item-search", "resourceWood", "--json"])

    assert result.exit_code == 0
    assert '"query":"resourceWood"' in result.stdout
    assert '"total":2' in result.stdout


def test_item_search_rejects_unsafe_query_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> object:
        calls.append((state, operation))
        return object()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["item-search", "resource Wood"])

    assert result.exit_code == 2
    assert calls == []


def test_entity_search_command_emits_filtered_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = EntityClassCatalog(
        items=(EntityClass(name="zombieTemplateMale", id=-1, manualSpawnType="None"),),
        observed_at=datetime.now(UTC),
    )
    monkeypatch.setattr(cli_module, "run", lambda state, operation: observed)

    result = runner.invoke(cli_module.app, ["entity-search", "zombie", "--json"])

    assert result.exit_code == 0
    assert '"name":"zombieTemplateMale"' in result.stdout


def test_existing_items_and_entity_classes_commands_remain_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        (
            item_catalog().search("stone"),
            EntityClassCatalog(
                items=(EntityClass(name="zombieTemplateMale", id=-1, manualSpawnType="None"),),
                observed_at=datetime.now(UTC),
            ),
        )
    )
    monkeypatch.setattr(cli_module, "run", lambda state, operation: next(responses))

    item_result = runner.invoke(cli_module.app, ["items", "stone", "--json"])
    entity_result = runner.invoke(cli_module.app, ["entity-classes", "zombie", "--json"])

    assert item_result.exit_code == 0
    assert entity_result.exit_code == 0


@pytest.mark.parametrize(
    ("arguments", "observed"),
    [
        (["say", "CLI café apostrophe's test"], message_result("say", "")),
        (["message", "171", "CLI test alpha bravo", "--json"], message_result("pm", "171")),
    ],
)
def test_message_commands_execute_without_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    observed: CommandResult,
) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return observed

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, arguments)

    assert result.exit_code == 0
    assert len(calls) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        ["say", "x;shutdown"],
        ["message", "171", 'double"quote'],
    ],
)
def test_message_commands_reject_unsafe_text_before_network(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "run",
        lambda state, operation: calls.append((state, operation)),
    )

    result = runner.invoke(cli_module.app, arguments)

    assert result.exit_code == 2
    assert calls == []


def test_kick_confirmation_then_executes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return message_result("kick", '171 "CLI moderation test"')

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(
        cli_module.app,
        ["kick", "171", "--reason", "CLI moderation test", "--json"],
        input="y\n",
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert '"command":"kick"' in result.stdout


def test_kick_decline_does_not_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "run",
        lambda state, operation: calls.append((state, operation)),
    )

    result = runner.invoke(cli_module.app, ["kick", "171"], input="n\n")

    assert result.exit_code == 1
    assert calls == []


def test_kick_yes_bypasses_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return message_result("kick", "171")

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["kick", "171", "--yes"])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_kick_rejects_reason_before_confirmation_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "run",
        lambda state, operation: calls.append((state, operation)),
    )

    result = runner.invoke(
        cli_module.app,
        ["kick", "171", "--reason", "x;shutdown", "--yes"],
    )

    assert result.exit_code == 2
    assert calls == []


def test_ban_confirms_destructive_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return message_result("ban", 'add 171 3 minute "CLI moderation test"')

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(
        cli_module.app,
        ["ban", "171", "3", "minute", "--reason", "CLI moderation test", "--json"],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "DESTRUCTIVE" in result.stdout
    assert len(calls) == 1


def test_ban_decline_does_not_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "run",
        lambda state, operation: calls.append((state, operation)),
    )

    result = runner.invoke(cli_module.app, ["ban", "171", "3", "minute"], input="n\n")

    assert result.exit_code == 1
    assert calls == []


def test_ban_list_executes_without_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return message_result("ban", "list")

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["ban-list", "--json"])

    assert result.exit_code == 0
    assert len(calls) == 1
    assert '"parameters":"list"' in result.stdout


def test_unban_yes_executes_with_combined_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        calls.append((state, operation))
        return message_result("ban", "remove EOS_sanitized")

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["unban", "EOS_sanitized", "--yes", "--json"])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_unban_rejects_unsafe_identity_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "run",
        lambda state, operation: calls.append((state, operation)),
    )

    result = runner.invoke(cli_module.app, ["unban", "EOS;shutdown", "--yes"])

    assert result.exit_code == 2
    assert calls == []


def test_give_exact_item_preflight_then_executes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    def fake_run(state: object, operation: object) -> object:
        del state
        calls.append(operation)
        return item_catalog() if len(calls) == 1 else command_result()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["give", "171", "terrStone", "1", "--yes"])
    assert result.exit_code == 0
    assert len(calls) == 2


def test_give_case_mismatch_does_not_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def fake_run(state: object, operation: object) -> ItemCatalog:
        del state
        calls.append(operation)
        return item_catalog()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(cli_module.app, ["give", "171", "terrstone", "1", "--yes"])
    assert result.exit_code == 2
    assert len(calls) == 1


def test_give_preflight_can_be_bypassed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def fake_run(state: object, operation: object) -> CommandResult:
        del state
        calls.append(operation)
        return command_result()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(
        cli_module.app,
        ["give", "171", "terrStone", "1", "--no-validate-item", "--yes", "--json"],
    )
    assert result.exit_code == 0
    assert len(calls) == 1


def test_give_declined_confirmation_does_not_execute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    def fake_run(state: object, operation: object) -> ItemCatalog:
        del state
        calls.append(operation)
        return item_catalog()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(
        cli_module.app,
        ["give", "171", "terrStone", "1"],
        input="n\n",
    )
    assert result.exit_code == 1
    assert len(calls) == 1


def test_give_unsafe_item_fails_before_network(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def fake_run(state: object, operation: object) -> object:
        del state
        calls.append(operation)
        return command_result()

    monkeypatch.setattr(cli_module, "run", fake_run)
    result = runner.invoke(
        cli_module.app,
        ["give", "171", "terr;shutdown", "1", "--no-validate-item", "--yes"],
    )
    assert result.exit_code == 2
    assert calls == []
