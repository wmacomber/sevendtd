import pytest

from sevendtd.admin.builders import (
    prepare_ban,
    prepare_ban_list,
    prepare_get_time,
    prepare_give,
    prepare_kick,
    prepare_message,
    prepare_save_world,
    prepare_say,
    prepare_search_items,
    prepare_shutdown,
    prepare_unban,
)
from sevendtd.admin.metadata import (
    ADMIN_OPERATIONS,
    VERIFIED_OPERATIONS,
    BanDurationUnit,
    CommandRisk,
)
from sevendtd.exceptions import SevenDTDCommandError


def test_verified_no_argument_builders() -> None:
    assert prepare_get_time().text == "gettime"
    assert prepare_get_time().metadata.risk is CommandRisk.READ_ONLY
    assert prepare_save_world().text == "saveworld"
    assert prepare_shutdown().metadata.risk is CommandRisk.SERVER_CONTROL


def test_legacy_admin_helpers_are_presence_observed_but_syntax_unverified() -> None:
    assert VERIFIED_OPERATIONS is ADMIN_OPERATIONS
    for name in ("get_time", "save_world", "shutdown"):
        metadata = ADMIN_OPERATIONS[name]
        assert not metadata.syntax_verified
        assert metadata.verification_evidence is not None
        assert "generic help" in metadata.verification_evidence


def test_message_builders_quote_observed_console_text() -> None:
    broadcast = prepare_say("CLI café apostrophe's test")
    private = prepare_message(171, "CLI test alpha bravo")

    assert broadcast.text == 'say "CLI café apostrophe\'s test"'
    assert private.text == 'pm 171 "CLI test alpha bravo"'
    assert broadcast.metadata.risk is CommandRisk.MUTATING
    assert private.metadata.risk is CommandRisk.MUTATING


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        " leading",
        "trailing ",
        'double"quote',
        "back\\slash",
        "line\nbreak",
        "tab\there",
        "x;shutdown",
        "x|shutdown",
        "x&shutdown",
    ],
)
def test_message_builders_reject_unverified_text(text: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_say(text)
    with pytest.raises(SevenDTDCommandError):
        prepare_message(171, text)


@pytest.mark.parametrize("entity_id", ["171", True, 1.0])
def test_private_message_rejects_non_integer_entity_id(entity_id: object) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_message(entity_id, "hello")  # type: ignore[arg-type]


def test_kick_builder_with_and_without_reason() -> None:
    without_reason = prepare_kick(171)
    with_reason = prepare_kick(171, "CLI moderation test")

    assert without_reason.text == "kick 171"
    assert with_reason.text == 'kick 171 "CLI moderation test"'
    assert with_reason.metadata.risk is CommandRisk.MUTATING


@pytest.mark.parametrize("entity_id", ["171", True, 1.0])
def test_kick_rejects_non_integer_entity_id(entity_id: object) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_kick(entity_id)  # type: ignore[arg-type]


@pytest.mark.parametrize("reason", ["", " trailing ", 'bad"reason', "x;shutdown", "line\nbreak"])
def test_kick_rejects_unsafe_reason(reason: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_kick(171, reason)


def test_ban_builders_cover_lifecycle() -> None:
    without_reason = prepare_ban(171, 3, BanDurationUnit.MINUTE)
    with_reason = prepare_ban(171, 3, BanDurationUnit.MINUTE, "CLI moderation test")
    listing = prepare_ban_list()
    removal = prepare_unban("EOS_sanitized")

    assert without_reason.text == "ban add 171 3 minute"
    assert with_reason.text == 'ban add 171 3 minute "CLI moderation test"'
    assert listing.text == "ban list"
    assert removal.text == "ban remove EOS_sanitized"
    assert with_reason.metadata.risk is CommandRisk.DESTRUCTIVE
    assert listing.metadata.risk is CommandRisk.READ_ONLY
    assert removal.metadata.risk is CommandRisk.MUTATING


@pytest.mark.parametrize(
    ("entity_id", "duration", "unit"),
    [
        ("171", 3, BanDurationUnit.MINUTE),
        (True, 3, BanDurationUnit.MINUTE),
        (171, 0, BanDurationUnit.MINUTE),
        (171, True, BanDurationUnit.MINUTE),
        (171, 3, "minutes"),
    ],
)
def test_ban_rejects_invalid_required_arguments(
    entity_id: object, duration: object, unit: object
) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_ban(entity_id, duration, unit)  # type: ignore[arg-type]


@pytest.mark.parametrize("reason", ["", " trailing ", 'bad"reason', "x;shutdown"])
def test_ban_rejects_unsafe_reason(reason: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_ban(171, 3, BanDurationUnit.MINUTE, reason)


@pytest.mark.parametrize(
    "identity", ["", "EOS bad", "EOS/bad", "EOS\\bad", "EOS;shutdown", "EOS|shutdown"]
)
def test_unban_rejects_unsafe_combined_identity(identity: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_unban(identity)


def test_give_builder_with_and_without_quality() -> None:
    without_quality = prepare_give(171, "resourceYuccaFibers", 2)
    with_quality = prepare_give(171, "gunPistolT1", 1, 6)

    assert without_quality.text == "give 171 resourceYuccaFibers 2"
    assert with_quality.text == "give 171 gunPistolT1 1 6"
    assert with_quality.metadata.risk is CommandRisk.MUTATING


def test_item_search_builder_is_read_only() -> None:
    prepared = prepare_search_items("resourceWood")
    assert prepared.text == "li resourceWood"
    assert prepared.metadata.risk is CommandRisk.READ_ONLY


@pytest.mark.parametrize(
    "query",
    [
        "",
        "resource Wood",
        "*",
        'resource"Wood',
        "resource/Tool",
        "resource\\Tool",
        "x\nshutdown",
        "x;shutdown",
        "x|shutdown",
    ],
)
def test_item_search_builder_rejects_unsafe_query(query: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_search_items(query)


@pytest.mark.parametrize(
    ("entity_id", "item_name", "amount", "quality"),
    [
        ("171", "terrStone", 1, None),
        (True, "terrStone", 1, None),
        (171, "", 1, None),
        (171, "terr Stone", 1, None),
        (171, 'terr"Stone', 1, None),
        (171, "terr\\Stone", 1, None),
        (171, "terr;shutdown", 1, None),
        (171, "terrStone", 0, None),
        (171, "terrStone", True, None),
        (171, "terrStone", 1, 0),
        (171, "terrStone", 1, 7),
        (171, "terrStone", 1, True),
    ],
)
def test_give_builder_rejects_invalid_arguments(
    entity_id: object,
    item_name: str,
    amount: object,
    quality: object,
) -> None:
    with pytest.raises(SevenDTDCommandError):
        prepare_give(entity_id, item_name, amount, quality)  # type: ignore[arg-type]
