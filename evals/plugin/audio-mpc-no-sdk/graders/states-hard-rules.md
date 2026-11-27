---
type: llm
focus: last_message
criteria: >
  Even without an SDK, the final message states the MPC's hard rules that apply to this effect,
  covering at least five of these: the finished plugin is a "<Manufacturer> - VST - <Name>" folder
  built by the SDK's build tool, never assembled by hand; the manifest's name and manufacturer, the
  plugin info in code and the folder name must agree; the four-character plugin id in plugin.json
  matches the one in code and, like the parameter ids, never changes; parameter 0 is nudged on every
  load and must be harmless; effects get no MIDI; every effect ships a Knob FX mapping; the MPC needs
  MPC OS 3.10.1 or later with External Plugin Support enabled; the SDK's validation and host
  simulator must pass before the plugin is called done.
---
