from app.advice.models import AdviceResponse, AreaAdvice, AreaId, Priority
from app.homes.schemas import BuildPeriod, HeatingSystem, HomeProfile, HomeSize, Residents

DISCLAIMER = (
    "This is directional planning advice, not a substitute for professional electrical, roofing, "
    "HVAC, or code compliance assessment."
)


def build_deterministic_advice(home: HomeProfile, ai_context: list[str]) -> AdviceResponse:
    priorities = _priorities(home)
    areas = [
        _solar_advice(home, priorities[AreaId.SOLAR]),
        _battery_advice(home, priorities[AreaId.BATTERY]),
        _heat_pump_advice(home, priorities[AreaId.HEAT_PUMP]),
        _smart_controls_advice(home, priorities[AreaId.SMART_CONTROLS]),
    ]
    if home.has_ev:
        areas.append(_ev_charging_advice(home, priorities[AreaId.EV_CHARGING]))

    return AdviceResponse(
        summary=_summary(home, priorities),
        areas=areas,
        disclaimer=DISCLAIMER,
    )


def _priorities(home: HomeProfile) -> dict[AreaId, Priority]:
    solar = Priority.MEDIUM
    battery = Priority.MEDIUM
    heat_pump = Priority.MEDIUM
    smart_controls = Priority.MEDIUM
    ev_charging = Priority.LOW

    if home.build_period == BuildPeriod.IN_PROGRESS:
        solar = Priority.HIGH
        battery = Priority.HIGH
        heat_pump = Priority.HIGH
        smart_controls = Priority.HIGH
        ev_charging = Priority.HIGH if home.has_ev else Priority.LOW
    elif home.build_period == BuildPeriod.PRE_1978:
        heat_pump = Priority.HIGH
        smart_controls = Priority.HIGH

    if home.heating_system == HeatingSystem.GAS:
        heat_pump = Priority.HIGH
        smart_controls = Priority.HIGH
        solar = _max_priority(solar, Priority.MEDIUM)
    elif home.heating_system == HeatingSystem.HEAT_PUMP:
        smart_controls = Priority.HIGH
        heat_pump = _min_priority(heat_pump, Priority.MEDIUM)

    if home.home_size == HomeSize.OVER_200:
        battery = Priority.HIGH
        smart_controls = Priority.HIGH
        heat_pump = _max_priority(heat_pump, Priority.HIGH)
    elif home.home_size == HomeSize.UNDER_100:
        battery = _min_priority(battery, Priority.LOW)

    if home.residents == Residents.FIVE_PLUS:
        battery = Priority.HIGH
        smart_controls = Priority.HIGH
    elif home.residents == Residents.ONE_TWO and home.home_size == HomeSize.UNDER_100:
        battery = Priority.LOW

    if home.has_ev:
        ev_charging = Priority.HIGH
        battery = Priority.HIGH
        smart_controls = Priority.HIGH

    return {
        AreaId.SOLAR: solar,
        AreaId.BATTERY: battery,
        AreaId.HEAT_PUMP: heat_pump,
        AreaId.SMART_CONTROLS: smart_controls,
        AreaId.EV_CHARGING: ev_charging,
    }


def _summary(home: HomeProfile, priorities: dict[AreaId, Priority]) -> str:
    if home.build_period == BuildPeriod.IN_PROGRESS:
        return (
            "Plan the energy system as one package now: solar-ready roof layout, battery location, "
            "heat pump design, smart control wiring, and EV charging capacity if needed."
        )
    if home.heating_system == HeatingSystem.GAS:
        return (
            "Start with heat pump readiness and smart heating control, then size solar and storage "
            "around the future electrified load profile."
        )
    if home.heating_system == HeatingSystem.HEAT_PUMP:
        return (
            "The home is already on an efficient heating path, so prioritize monitoring, "
            "scheduling, solar sizing, and storage only where it improves self-consumption."
        )
    if priorities[AreaId.BATTERY] == Priority.HIGH:
        return (
            "Focus first on measured electricity demand and load management, then decide how much "
            "solar and battery capacity the household can use well."
        )
    return (
        "Use the profile as a starting point: confirm heating demand, check solar potential, add "
        "simple monitoring, and treat storage as a follow-on sizing decision."
    )


def _solar_advice(home: HomeProfile, priority: Priority) -> AreaAdvice:
    if home.build_period == BuildPeriod.IN_PROGRESS:
        insight = (
            "Because the home is still in progress, roof orientation, conduit routes, inverter "
            "location, and future battery wiring can be planned together before finishes are "
            "locked."
        )
        first_step = (
            "Ask the designer or installer to reserve roof zones and electrical pathways for solar."
        )
    elif home.heating_system == HeatingSystem.GAS:
        insight = (
            "Solar should be sized with future electrified heating in mind, since moving from gas "
            "to a heat pump can shift more of the home's energy use to electricity."
        )
        first_step = (
            "Collect annual electricity and gas usage so a solar quote can model future load."
        )
    elif home.heating_system == HeatingSystem.HEAT_PUMP:
        insight = (
            "Solar can support an already efficient heating setup when production and heat pump "
            "schedules are aligned."
        )
        first_step = (
            "Compare heat pump runtime against daylight production windows before sizing panels."
        )
    else:
        insight = (
            "Solar potential is useful, but the right size depends on first clarifying the heating "
            "system and expected electrical load."
        )
        first_step = (
            "Gather utility bills and heating equipment details before requesting solar designs."
        )

    return AreaAdvice(
        area_id=AreaId.SOLAR,
        title="Solar panels",
        priority=priority,
        insight=insight,
        first_step=first_step,
        default_prompt="Given my home profile, what are the best improvements for my solar setup?",
        suggested_questions=[
            "How should I think about solar sizing for this home?",
            "Should solar planning change if I add a heat pump or battery later?",
            "What information should I prepare before asking installers for quotes?",
        ],
    )


def _battery_advice(home: HomeProfile, priority: Priority) -> AreaAdvice:
    if home.has_ev:
        insight = (
            "An EV increases controllable electricity demand, so storage should be judged "
            "alongside charging schedules, solar self-consumption, and peak-load management."
        )
        first_step = (
            "Map when the EV is usually parked at home and whether charging can move to sunny "
            "hours."
        )
    elif home.home_size == HomeSize.OVER_200 or home.residents == Residents.FIVE_PLUS:
        insight = (
            "A larger or busier household may use more evening electricity, which can make battery "
            "storage more relevant after actual loads are measured."
        )
        first_step = "Install or review monitoring data to see evening and overnight consumption."
    elif home.home_size == HomeSize.UNDER_100 and home.residents == Residents.ONE_TWO:
        insight = (
            "With lighter demand, a smaller battery or no battery may be more appropriate than a "
            "large storage system."
        )
        first_step = "Estimate daily surplus solar before considering storage capacity."
    else:
        insight = (
            "Battery value depends on how much solar would otherwise be exported and how much load "
            "can be shifted into stored energy."
        )
        first_step = "Review hourly usage or smart meter data before selecting a battery size."

    return AreaAdvice(
        area_id=AreaId.BATTERY,
        title="Home power station",
        priority=priority,
        insight=insight,
        first_step=first_step,
        default_prompt="Given my home profile, would a home battery or power station be useful?",
        suggested_questions=[
            "What signals show that battery storage is worth considering?",
            "Should I install solar first and add storage later?",
            "How should EV charging affect battery sizing?",
        ],
    )


def _heat_pump_advice(home: HomeProfile, priority: Priority) -> AreaAdvice:
    if home.heating_system == HeatingSystem.GAS:
        insight = (
            "Gas heating makes heat pump conversion a major opportunity, especially if controls "
            "and solar planning are designed around the new electrical load."
        )
        first_step = (
            "Book a professional heat-load assessment and review existing radiators or ducts."
        )
    elif home.heating_system == HeatingSystem.HEAT_PUMP:
        insight = (
            "The heat pump is already the efficient backbone; the biggest gains are likely from "
            "tuning schedules, monitoring runtime, and keeping maintenance disciplined."
        )
        first_step = (
            "Check current schedules, setpoints, filters, and runtime data before changing "
            "hardware."
        )
    else:
        insight = (
            "The heating system needs clarification before specific heat pump recommendations "
            "are reliable."
        )
        first_step = (
            "Identify the current heating equipment, distribution system, and hot-water setup."
        )

    if home.build_period == BuildPeriod.PRE_1978:
        insight += (
            " Because the home is older, mention insulation only as readiness context for comfort "
            "and heat pump sizing."
        )
    elif home.build_period == BuildPeriod.IN_PROGRESS:
        insight = (
            "A new build or major project can design heat pump equipment, emitters, hot water, "
            "controls, and solar support as one integrated system."
        )
        first_step = (
            "Ask the HVAC designer for room-by-room load calculations and control-zone planning."
        )

    return AreaAdvice(
        area_id=AreaId.HEAT_PUMP,
        title="Heat pump heating",
        priority=priority,
        insight=insight,
        first_step=first_step,
        default_prompt="Given my home profile, what should I improve around heat pump heating?",
        suggested_questions=[
            "What should a heat pump readiness assessment include?",
            "How should smart controls support heating efficiency?",
            "How does solar planning change if heating becomes electric?",
        ],
    )


def _smart_controls_advice(home: HomeProfile, priority: Priority) -> AreaAdvice:
    if home.residents == Residents.FIVE_PLUS or home.home_size == HomeSize.OVER_200:
        insight = (
            "Higher demand and more varied routines make monitoring, zoning, and scheduling "
            "especially valuable for avoiding waste and managing peaks."
        )
        first_step = (
            "Start with whole-home monitoring and heating zones before adding complex automation."
        )
    elif home.residents == Residents.ONE_TWO:
        insight = (
            "A smaller household can often shift flexible loads to sunny hours with simple "
            "controls and clear usage feedback."
        )
        first_step = (
            "Use basic schedules for heating, hot water, appliances, and any future charging."
        )
    else:
        insight = (
            "Smart controls can coordinate solar production, heating schedules, hot water, and "
            "storage without requiring major construction."
        )
        first_step = (
            "Choose one monitoring view that shows solar production, household load, and heating "
            "use."
        )

    if home.heating_system == HeatingSystem.HEAT_PUMP:
        insight += (
            " Keep heat pump schedules steady and avoid aggressive setbacks unless data supports "
            "them."
        )

    return AreaAdvice(
        area_id=AreaId.SMART_CONTROLS,
        title="Smart controls",
        priority=priority,
        insight=insight,
        first_step=first_step,
        default_prompt=(
            "Given my home profile, how should smart controls monitor and operate my home?"
        ),
        suggested_questions=[
            "Which energy metrics should I monitor first?",
            "How can controls shift demand to solar production hours?",
            "What automation should I avoid until I have better data?",
        ],
    )


def _ev_charging_advice(home: HomeProfile, priority: Priority) -> AreaAdvice:
    if home.build_period == BuildPeriod.IN_PROGRESS:
        insight = (
            "EV charging can be planned into the electrical design now, including charger "
            "location, load management, solar coordination, and future battery integration."
        )
        first_step = (
            "Reserve panel capacity, conduit, and a charger location before electrical rough-in."
        )
    else:
        insight = (
            "EV charging should be coordinated with solar production and household peaks so the "
            "car becomes a flexible load instead of a strain on the system."
        )
        first_step = (
            "Review charger capacity, typical parking hours, and whether scheduled charging is "
            "enabled."
        )

    return AreaAdvice(
        area_id=AreaId.EV_CHARGING,
        title="EV charging",
        priority=priority,
        insight=insight,
        first_step=first_step,
        default_prompt=(
            "Given my home profile, how should I optimize EV charging with solar and storage?"
        ),
        suggested_questions=[
            "When should I charge to use more solar energy?",
            "Do I need load management for home EV charging?",
            "How should a battery affect my charging schedule?",
        ],
    )


def _max_priority(current: Priority, candidate: Priority) -> Priority:
    return current if _priority_rank(current) >= _priority_rank(candidate) else candidate


def _min_priority(current: Priority, candidate: Priority) -> Priority:
    return current if _priority_rank(current) <= _priority_rank(candidate) else candidate


def _priority_rank(priority: Priority) -> int:
    return {
        Priority.LOW: 1,
        Priority.MEDIUM: 2,
        Priority.HIGH: 3,
    }[priority]
