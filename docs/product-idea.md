# Product Idea

## Home Energy Advisor

Home Energy Advisor is a web application where users configure a profile for their home and receive AI-assisted energy efficiency recommendations. The experience should feel more engaging than a standard form: the main interface is a beautiful modern energy-efficient house scene with solar panels, an EV charging station near a car under a roof, and a polished yard. The house itself becomes an interactive navigation surface for exploring improvement areas.

The app should remain simple and focused, but it should demonstrate thoughtful full-stack design, pragmatic LLM integration, and a clean user experience.

## Product Experience

### Visual Concept

The first screen should present a good-looking modern home as the central visual element. The house should suggest an energy-efficient lifestyle:

- Solar panels on the roof
- EV charging station outside near a car
- Covered parking or garage area
- Attractive, modern yard
- Clean, calm, contemporary design

This image should not be only decorative. It should become the main interaction surface once the user has configured their home.

### Advice Scope

The app should focus on four primary energy improvement categories:

- Solar panels
- Home power stations and battery storage
- Internal heating with heat pumps
- Smart controls for monitoring and operation

Other topics may be mentioned only when they directly affect these categories. For example, insulation can be referenced as context for heat pump sizing or heating efficiency, but it should not become a primary recommendation category.

### Home Configurator

Before showing personalized advice, the app should guide the user through a compact interactive configurator. The configurator should use predefined controls rather than a long open-ended form. Controls may include segmented buttons, dropdowns, sliders, toggles, and short text fields.

The goal is to ask only the highest-signal questions needed to generate useful advice for solar, storage, heat pumps, EV readiness, and smart controls.

1. When was your home built?
2. How large is your home?
3. How many people live in your home?
4. What heating system do you currently use?
5. Do you own an electric car?

#### Question and Answer Options

| Question | Options | Why it matters |
| --- | --- | --- |
| When was your home built? | Pre-1978, 1980-2000, After 2000, In progress | Home age gives a rough signal for insulation quality, heating demand, and how easy it may be to plan modern systems. |
| How large is your home? | Under 100 sq m, 100-200 sq m, Over 200 sq m | Home size helps estimate heating demand, solar potential, battery usefulness, and smart control needs. |
| How many people live in your home? | 1-2, 3-4, 5+ | Household size influences hot water use, electricity consumption patterns, EV charging needs, and storage value. |
| What heating system do you currently use? | Gas, Heat pump, Other or not sure | The existing heating system is central to heat pump advice and expected savings potential. |
| Do you own an electric car? | Yes, No | EV ownership changes the value of solar, battery storage, charging schedules, and smart energy management. |

#### Session AI Instructions From Answers

The app should convert each configurator answer into short predefined AI instructions saved in the user's session. These instructions should be included as context when generating hotspot advice or chat responses.

| Answer | Saved AI instruction |
| --- | --- |
| Home built before 1978 | Treat the home as likely to have weaker baseline efficiency and higher heating demand. Prioritize practical heat pump readiness, smart heating control, and realistic expectations for solar-plus-storage benefits. Mention insulation only as supporting context for heat pump performance. |
| Home built between 1980 and 2000 | Treat the home as moderately efficient with possible upgrade opportunities. Focus on balanced advice across solar panels, battery storage, heat pump modernization, and smart controls. |
| Home built after 2000 | Treat the home as likely to have stronger baseline efficiency. Emphasize optimization: solar sizing, battery value, heat pump tuning, smart monitoring, automation, and energy use scheduling. |
| Home is in progress | Treat the home as a strong opportunity for integrated planning from the beginning. Prioritize solar readiness, battery placement, heat pump design, EV charging infrastructure, wiring, sensors, and smart control architecture. |
| Home size under 100 sq m | Assume lower overall heating and electricity demand. Recommend right-sized solar, smaller battery options, compact heat pump solutions, and simple smart controls. |
| Home size 100-200 sq m | Assume moderate demand. Provide balanced system sizing guidance for solar, storage, heat pumps, and smart controls. |
| Home size over 200 sq m | Assume higher demand and more complex energy management. Prioritize zoning, larger or staged heat pump planning, expanded solar potential, battery capacity analysis, and detailed monitoring. |
| 1-2 residents | Assume lighter and more flexible energy use. Emphasize scheduling, smaller storage needs, and smart controls that shift consumption to solar production hours. |
| 3-4 residents | Assume typical family energy patterns. Recommend balanced solar, storage, smart heating schedules, and monitoring for daily routines. |
| 5+ residents | Assume high hot water, heating, appliance, and charging demand. Prioritize load management, smart controls, solar self-consumption, and battery usefulness. |
| Gas heating | Treat heat pump conversion as a major opportunity. Explain likely benefits, readiness checks, smart thermostat/control needs, and how solar can support electrified heating. |
| Heat pump heating | Treat the home as already on an efficient heating path. Focus on optimization, smart controls, monitoring, scheduling, maintenance, and whether solar or storage can improve operating cost. |
| Other or not sure heating | Ask clarifying questions when needed. Give cautious advice and focus on assessment steps before recommending specific heat pump changes. |
| Owns an electric car | Include EV charging in solar, battery, and smart control advice. Discuss charging schedules, load management, solar self-consumption, and future home power station value. |
| Does not own an electric car | Do not center EV charging in recommendations. Mention EV readiness only as optional future-proofing when discussing solar, storage, or smart electrical planning. |

### Interactive House Hotspots

After the user completes the configurator, the house scene should expose clickable areas. Each area should represent a major part of the home and open a focused advice panel or chat experience.

Suggested hotspot areas:

- Roof and solar panels
- Home power station and battery storage
- Heat pump and indoor heating
- Smart controls and monitoring
- EV charging, when relevant

Each hotspot should provide:

- A short default insight based on the user profile
- A priority level
- A practical first step
- A default prompt the user can send to the AI
- A focused chat experience scoped to that part of the house

Example default prompt:

```text
Given my home profile, what are the best improvements for my solar panel setup?
```

### Global AI Chat

In addition to hotspot-specific conversations, the bottom section of the UI should include a global chat component. This chat should let the user ask broader questions about their whole home.

Example questions:

- What should I improve first if I only have a limited budget?
- Which upgrades will likely reduce my bills the most?
- Should I install solar panels before adding battery storage?
- Can you create a phased 6-month improvement plan?
- How should I use smart controls to reduce energy waste?

The global chat should use the complete home profile and, when available, previously generated hotspot insights.
