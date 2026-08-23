from datetime import UTC, datetime

from sevendtd.models.catalogs import EntityClass, EntityClassCatalog, ItemCatalog, ItemDefinition


def test_item_catalog_exact_lookup_and_unknown_field() -> None:
    item = ItemDefinition.model_validate(
        {
            "name": "terrStone",
            "localizedName": "Stone",
            "isBlock": True,
            "futureField": "retained",
        }
    )
    catalog = ItemCatalog(items=(item,), observed_at=datetime.now(UTC))
    assert catalog.get("terrStone") is item
    assert catalog.get("terrstone") is None
    assert item.model_extra == {"futureField": "retained"}


def test_entity_class_accepts_signed_ids() -> None:
    entity_class = EntityClass(name="zombieTemplateMale", id=-1767388301, manualSpawnType="None")
    catalog = EntityClassCatalog(items=(entity_class,), observed_at=datetime.now(UTC))
    assert catalog.items[0].id == -1767388301


def test_item_catalog_searches_names_and_localized_names() -> None:
    catalog = ItemCatalog(
        items=(
            ItemDefinition(name="terrStone", localizedName="Stone", isBlock=True),
            ItemDefinition(name="resourceYuccaFibers", localizedName="Plant Fibers", isBlock=False),
        ),
        observed_at=datetime.now(UTC),
    )

    assert [item.name for item in catalog.search("STONE").items] == ["terrStone"]
    assert [item.name for item in catalog.search("plant").items] == ["resourceYuccaFibers"]
    assert catalog.search("fiber", blocks_only=True).items == ()
    assert [item.name for item in catalog.search("", blocks_only=True).items] == ["terrStone"]


def test_entity_class_catalog_searches_names_case_insensitively() -> None:
    catalog = EntityClassCatalog(
        items=(
            EntityClass(name="zombieTemplateMale", id=-1, manualSpawnType="None"),
            EntityClass(name="animalChicken", id=2, manualSpawnType="Animal"),
        ),
        observed_at=datetime.now(UTC),
    )

    assert [item.name for item in catalog.search("ZOMBIE").items] == ["zombieTemplateMale"]
    assert catalog.search("vehicle").items == ()
