from Models.adidasRunnersEventModel import AdidasRunnersEvent


def test_init_sets_all_fields_correctly():
    ev = AdidasRunnersEvent(
        id="123",
        name="Treino Leve",
        category="Run",
        startDate="2025-01-01T10:00:00Z",
    )
    assert ev.id == "123"
    assert ev.name == "Treino Leve"
    # category deve ser string com o valor exato informado
    assert ev.category == "Run"
    assert ev.startDate == "2025-01-01T10:00:00Z"


def test_category_is_string_not_tuple():
    ev = AdidasRunnersEvent("1", "A", "Run", "2025-01-01T00:00:00Z")
    assert isinstance(ev.category, str), "category deve ser str, não tuple"
    assert ev.category == "Run"


def test_startDate_preserves_input_string():
    iso = "2024-12-31T23:59:59Z"
    ev = AdidasRunnersEvent("9", "Virada", "Party", iso)
    assert ev.startDate == iso


def test_instances_are_independent():
    ev1 = AdidasRunnersEvent("1", "Name1", "Run", "2025-01-01T00:00:00Z")
    ev2 = AdidasRunnersEvent("2", "Name2", "Walk", "2025-02-02T00:00:00Z")
    assert ev1.id != ev2.id
    assert ev1.name != ev2.name
    assert ev1.category != ev2.category
    assert ev1.startDate != ev2.startDate