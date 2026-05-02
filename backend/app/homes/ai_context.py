from app.homes.schemas import BuildPeriod, HeatingSystem, HomeCreateRequest, HomeSize, Residents

BUILD_PERIOD_CONTEXT: dict[BuildPeriod, str] = {
    BuildPeriod.PRE_1978: (
        "Treat the home as likely to have weaker baseline efficiency and higher heating demand. "
        "Prioritize practical heat pump readiness, smart heating control, and realistic "
        "expectations for solar-plus-storage benefits. Mention insulation only as supporting "
        "context for heat pump performance."
    ),
    BuildPeriod.Y1980_2000: (
        "Treat the home as moderately efficient with possible upgrade opportunities. Focus on "
        "balanced advice across solar panels, battery storage, heat pump modernization, and "
        "smart controls."
    ),
    BuildPeriod.POST_2000: (
        "Treat the home as likely to have stronger baseline efficiency. Emphasize optimization: "
        "solar sizing, battery value, heat pump tuning, smart monitoring, automation, and energy "
        "use scheduling."
    ),
    BuildPeriod.IN_PROGRESS: (
        "Treat the home as a strong opportunity for integrated planning from the beginning. "
        "Prioritize solar readiness, battery placement, heat pump design, EV charging "
        "infrastructure, wiring, sensors, and smart control architecture."
    ),
}

HOME_SIZE_CONTEXT: dict[HomeSize, str] = {
    HomeSize.UNDER_100: (
        "Assume lower overall heating and electricity demand. Recommend right-sized solar, "
        "smaller battery options, compact heat pump solutions, and simple smart controls."
    ),
    HomeSize.Y100_200: (
        "Assume moderate demand. Provide balanced system sizing guidance for solar, storage, "
        "heat pumps, and smart controls."
    ),
    HomeSize.OVER_200: (
        "Assume higher demand and more complex energy management. Prioritize zoning, larger or "
        "staged heat pump planning, expanded solar potential, battery capacity analysis, and "
        "detailed monitoring."
    ),
}

RESIDENTS_CONTEXT: dict[Residents, str] = {
    Residents.ONE_TWO: (
        "Assume lighter and more flexible energy use. Emphasize scheduling, smaller storage "
        "needs, and smart controls that shift consumption to solar production hours."
    ),
    Residents.THREE_FOUR: (
        "Assume typical family energy patterns. Recommend balanced solar, storage, smart "
        "heating schedules, and monitoring for daily routines."
    ),
    Residents.FIVE_PLUS: (
        "Assume high hot water, heating, appliance, and charging demand. Prioritize load "
        "management, smart controls, solar self-consumption, and battery usefulness."
    ),
}

HEATING_SYSTEM_CONTEXT: dict[HeatingSystem, str] = {
    HeatingSystem.GAS: (
        "Treat heat pump conversion as a major opportunity. Explain likely benefits, readiness "
        "checks, smart thermostat/control needs, and how solar can support electrified heating."
    ),
    HeatingSystem.HEAT_PUMP: (
        "Treat the home as already on an efficient heating path. Focus on optimization, smart "
        "controls, monitoring, scheduling, maintenance, and whether solar or storage can improve "
        "operating cost."
    ),
    HeatingSystem.OTHER_UNKNOWN: (
        "Ask clarifying questions when needed. Give cautious advice and focus on assessment "
        "steps before recommending specific heat pump changes."
    ),
}

EV_CONTEXT = {
    True: (
        "Include EV charging in solar, battery, and smart control advice. Discuss charging "
        "schedules, load management, solar self-consumption, and future home power station value."
    ),
    False: (
        "Do not center EV charging in recommendations. Mention EV readiness only as optional "
        "future-proofing when discussing solar, storage, or smart electrical planning."
    ),
}


def build_ai_context(request: HomeCreateRequest) -> list[str]:
    return [
        BUILD_PERIOD_CONTEXT[request.build_period],
        HOME_SIZE_CONTEXT[request.home_size],
        RESIDENTS_CONTEXT[request.residents],
        HEATING_SYSTEM_CONTEXT[request.heating_system],
        EV_CONTEXT[request.has_ev],
    ]

