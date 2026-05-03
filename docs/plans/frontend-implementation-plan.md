# Frontend Implementation Plan

## Frontend Constraints

Build a full-viewport desktop layout with `1440 x 900` as the minimum supported size.

```text
left sidebar: fixed 260px profiles
center: 900 x 600 house image + hotspots
right panel: min 280px, grows with available screen width, full viewport height
bottom panel: 900px wide global chat under the scene, grows with available screen height
```

No mobile support, responsive breakpoints, drawers, or touch-first behavior are required.

## Frontend Structure

```text
frontend/src/
  api/client.ts
  types/api.ts
  state/useAppState.ts
  components/
    ProfileSidebar.vue
    HomeConfigurator.vue
    HouseScene.vue
    AdvicePanel.vue
    ChatPanel.vue
```

## API Client

- Use native `fetch`.
- Do not add Axios.
- Centralize JSON parsing.
- Parse standard error envelope.
- Expose typed methods for all `/api/v1` endpoints.

Required client methods:

```text
listHomes
createHome
getHome
getAdvice
generateAdvice
getChat
sendChatMessage
```

## House Image

```text
source: assents/energy-effective-house.png
copy to: frontend/src/assets/energy-effective-house.png
render size: 900 x 600
```

Hotspots use percentage coordinates over the image:

```text
solar: roof panels
battery: garage/utility area
heat_pump: exterior heating marker
smart_controls: visible control/interior marker
ev_charging: charger/car area, hidden when has_ev=false
```

## Chat Behavior

- Store one shared `chatHistory` per selected profile.
- Global chat filters `source=global`.
- Hotspot chat filters selected hotspot source.
- All submits call `POST /api/v1/homes/{home_id}/chat`.
- Preserve draft input per source.
- Disable only the active sending source.
- Render guardrail errors inline.
- Render fake-provider demo note visibly.

## Frontend Implementation Sequence

### 1. Frontend Setup

- Scaffold `frontend/` with Vue 3, Vite, TypeScript, and `@vitejs/plugin-vue`.
- Configure scripts:
  - `npm run dev`
  - `npm run build`
  - `npm run typecheck`
  - `npm run test:e2e:headed`
- Add `src/types/api.ts` matching backend response/request contracts exactly, including error envelope.
- Add `src/api/client.ts` using native `fetch`.
- Implement one lightweight `state/useAppState.ts` composable containing:
  - `homes`
  - `selectedHomeId`
  - `selectedArea`
  - `adviceByHomeId`
  - `chatByHomeId`
  - `draftBySource`
  - `sendingSource`
  - `errorBySource`
- Build the full-viewport app frame in `App.vue` using:
  - `260px` sidebar
  - `900px` scene column
  - `minmax(280px, 1fr)` right panel that receives extra screen width
  - `minmax(300px, 1fr)` bottom global chat region under the scene
  - right panel spanning the full viewport height for more advice and focused chat space

Acceptance checks:

- TypeScript types prevent untyped API response usage.
- No Axios dependency is added.
- API base URL uses `VITE_API_BASE_URL`.
- The simplified frame fills the browser viewport and remains usable at `1440 x 900`.

### 2. Profiles UI

- Implement `ProfileSidebar.vue`:
  - list profile names
  - show selected profile
  - show create-profile action
  - keep sidebar visible during loading/errors
- Implement `HomeConfigurator.vue`:
  - required text input for profile name
  - five segmented/selectable question groups using the exact labels from the shared plan
  - disabled submit until all required values are selected
  - preserve answers when API errors occur
- On create:
  - call `POST /homes`
  - select returned profile
  - call `POST /homes/{id}/advice`
  - load `GET /homes/{id}/chat`
- Persist selected home ID in `localStorage`.
- On app load:
  - fetch profiles
  - select stored ID if present and still valid
  - otherwise select most recently updated profile
  - if no profiles, show configurator-first state

Acceptance checks:

- User can create at least two profiles and switch without losing each profile's chat/advice state.
- Configurator cannot submit incomplete profiles.

### 3. House And Advice UI

- Copy `assents/energy-effective-house.png` to `frontend/src/assets/energy-effective-house.png` without modifying image content.
- Render the scene at `900 x 600`.
- Implement `HouseScene.vue` with image and absolutely positioned hotspot layer.
- Implement hotspot config directly inside `HouseScene.vue` as data:
  - area ID
  - label
  - x/y percentages
  - optional visibility condition
- Render stable-size hotspot buttons directly inside `HouseScene.vue`.
- Hide `ev_charging` when selected profile has `has_ev=false`.
- Disable hotspots until profile and advice are loaded.
- Implement `AdvicePanel.vue`:
  - no-selected-area empty state
  - title, priority, insight, first step
  - default prompt button
  - suggested question buttons
  - provider/fallback note when present
- Suggested prompt/question buttons send chat messages with the selected area source.

Acceptance checks:

- Hotspots align with the fixed `900 x 600` scene inside the full-viewport layout.
- Advice panel provides useful information before chat is used.
- EV hotspot never appears for non-EV homes.

### 4. Chat UI

- Implement `ChatPanel.vue` reusable for any `source`.
- Use `ChatPanel.vue` directly for both selected hotspot chat and global chat.
- Chat panels receive shared `chatHistory` and filter visible messages by source.
- All sends call `sendChatMessage(homeId, source, draft)` and append the returned user and assistant messages locally.
- Refresh chat with `GET /chat` when switching profiles.
- Preserve draft text per source in `useAppState`.
- Disable only the source currently sending; do not block unrelated chat boxes.
- Render user and assistant messages distinctly. Timestamps are not required for the demo.
- Render guardrail/provider errors inline in the panel where the user submitted the message.
- Fake provider demo note should be visibly rendered as part of the fake response text.

Acceptance checks:

- Solar-source messages display only in solar chat.
- Global-source messages display only in global chat.
- Backend history remains unified even though UI display is filtered.

### 5. Frontend Testing And E2E

- Run `npm run typecheck`.
- Run `npm run build`.
- Configure Playwright Chromium project.
- Set viewport to `1440 x 900`.
- Run headed with one worker through `npm run test:e2e:headed`.
- Use UI interactions only for the golden path, not direct API setup calls.

Command:

```text
npm run test:e2e:headed
```

Equivalent:

```text
npx playwright test --headed --project=chromium --workers=1
```

Golden path:

- Create first profile.
- Generate advice.
- Open solar hotspot.
- Ask about smaller panels in solar chat.
- Ask about panel types in global chat.
- Confirm global answer uses prior solar context.
- Create second profile.
- Switch back.
- Confirm advice and chat history reload.

Required frontend checks:

- Full-viewport desktop layout remains usable at `1440 x 900`.
- Provided image renders.
- Hotspots align with `900 x 600` image.
- Multi-profile creation and switching.
- Advice loads per profile.
- Chat filters display by source.
- Backend history remains unified.
- Guardrail errors render clearly.
- Playwright headed golden path passes.
