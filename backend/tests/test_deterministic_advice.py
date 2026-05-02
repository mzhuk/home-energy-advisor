from app.advice.deterministic import DISCLAIMER, build_deterministic_advice
from app.advice.models import AreaId, Priority
from app.homes.schemas import BuildPeriod, HeatingSystem, HomeProfile, HomeSize, Residents


def home_profile(
    *,
    build_period: BuildPeriod = BuildPeriod.Y1980_2000,
    home_size: HomeSize = HomeSize.Y100_200,
    residents: Residents = Residents.THREE_FOUR,
    heating_system: HeatingSystem = HeatingSystem.OTHER_UNKNOWN,
    has_ev: bool = False,
) -> HomeProfile:
    return HomeProfile(
        id="home_test",
        name="Test home",
        build_period=build_period,
        home_size=home_size,
        residents=residents,
        heating_system=heating_system,
        has_ev=has_ev,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def priorities_by_area(home: HomeProfile) -> dict[AreaId, Priority]:
    advice = build_deterministic_advice(home, ai_context=["context"])
    return {area.area_id: area.priority for area in advice.areas}


def test_old_gas_home_prioritizes_heat_pump_and_smart_controls() -> None:
    advice = build_deterministic_advice(
        home_profile(build_period=BuildPeriod.PRE_1978, heating_system=HeatingSystem.GAS),
        ai_context=["context"],
    )

    priorities = {area.area_id: area.priority for area in advice.areas}
    heat_pump = next(area for area in advice.areas if area.area_id == AreaId.HEAT_PUMP)

    assert priorities[AreaId.HEAT_PUMP] == Priority.HIGH
    assert priorities[AreaId.SMART_CONTROLS] == Priority.HIGH
    assert priorities[AreaId.SOLAR] == Priority.MEDIUM
    assert "heat pump readiness" in advice.summary
    assert "insulation only as readiness context" in heat_pump.insight
    assert advice.disclaimer == DISCLAIMER


def test_in_progress_home_prioritizes_integrated_energy_planning() -> None:
    advice = build_deterministic_advice(
        home_profile(build_period=BuildPeriod.IN_PROGRESS, has_ev=True),
        ai_context=["context"],
    )

    assert [area.area_id for area in advice.areas] == [
        AreaId.SOLAR,
        AreaId.BATTERY,
        AreaId.HEAT_PUMP,
        AreaId.SMART_CONTROLS,
        AreaId.EV_CHARGING,
    ]
    assert {area.priority for area in advice.areas} == {Priority.HIGH}
    assert "Plan the energy system as one package now" in advice.summary


def test_post_2000_heat_pump_home_focuses_on_optimization() -> None:
    advice = build_deterministic_advice(
        home_profile(
            build_period=BuildPeriod.POST_2000,
            heating_system=HeatingSystem.HEAT_PUMP,
        ),
        ai_context=["context"],
    )

    priorities = {area.area_id: area.priority for area in advice.areas}
    smart_controls = next(area for area in advice.areas if area.area_id == AreaId.SMART_CONTROLS)

    assert priorities[AreaId.HEAT_PUMP] == Priority.MEDIUM
    assert priorities[AreaId.SMART_CONTROLS] == Priority.HIGH
    assert "already on an efficient heating path" in advice.summary
    assert "avoid aggressive setbacks" in smart_controls.insight


def test_large_busy_household_prioritizes_storage_and_monitoring() -> None:
    priorities = priorities_by_area(
        home_profile(home_size=HomeSize.OVER_200, residents=Residents.FIVE_PLUS)
    )

    assert priorities[AreaId.BATTERY] == Priority.HIGH
    assert priorities[AreaId.SMART_CONTROLS] == Priority.HIGH
    assert priorities[AreaId.HEAT_PUMP] == Priority.HIGH


def test_small_light_household_keeps_battery_lower_priority() -> None:
    priorities = priorities_by_area(
        home_profile(home_size=HomeSize.UNDER_100, residents=Residents.ONE_TWO)
    )

    assert priorities[AreaId.BATTERY] == Priority.LOW


def test_ev_owner_gets_ev_area_and_load_management_priorities() -> None:
    advice = build_deterministic_advice(home_profile(has_ev=True), ai_context=["context"])
    priorities = {area.area_id: area.priority for area in advice.areas}
    ev_area = next(area for area in advice.areas if area.area_id == AreaId.EV_CHARGING)

    assert priorities[AreaId.EV_CHARGING] == Priority.HIGH
    assert priorities[AreaId.BATTERY] == Priority.HIGH
    assert priorities[AreaId.SMART_CONTROLS] == Priority.HIGH
    assert "scheduled charging" in ev_area.first_step


def test_non_ev_owner_omits_ev_area() -> None:
    advice = build_deterministic_advice(home_profile(has_ev=False), ai_context=["context"])

    assert AreaId.EV_CHARGING not in [area.area_id for area in advice.areas]


def test_same_input_returns_same_advice() -> None:
    home = home_profile(
        build_period=BuildPeriod.Y1980_2000,
        home_size=HomeSize.Y100_200,
        residents=Residents.THREE_FOUR,
        heating_system=HeatingSystem.GAS,
        has_ev=True,
    )

    first = build_deterministic_advice(home, ai_context=["context"])
    second = build_deterministic_advice(home, ai_context=["context"])

    assert first == second

