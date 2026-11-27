# Relays, attachments and the page's states

Facts checked against JUCE 9.0.6; see Sources. What makes a good parameter id, and why it never changes, belongs to the `audio-parameters` skill; this file only says how a parameter reaches the page.

## Three pairs, matched by name and by type

A control on the page is wired to a parameter through three objects that must agree:

| Parameter | C++ relay | C++ attachment | Page function | Page reads and writes |
|---|---|---|---|---|
| `AudioParameterFloat`, `AudioParameterInt` | `juce::WebSliderRelay` | `juce::WebSliderParameterAttachment` | `getSliderState(name)` | `getNormalisedValue()`, `getScaledValue()`, `setNormalisedValue(v)`, `sliderDragStarted()`, `sliderDragEnded()` |
| `AudioParameterBool` | `juce::WebToggleButtonRelay` | `juce::WebToggleButtonParameterAttachment` | `getToggleState(name)` | `getValue()`, `setValue(bool)` |
| `AudioParameterChoice` | `juce::WebComboBoxRelay` | `juce::WebComboBoxParameterAttachment` | `getComboBoxState(name)` | `getChoiceIndex()`, `setChoiceIndex(i)`, `properties.choices` |

- **The name** is the string the relay is constructed with, and the page passes the same string to the matching function. It's case-sensitive. Using the parameter id as the relay name keeps one name for everything.
- **The type** must match too. `getSliderState("bypass")` doesn't find a `WebToggleButtonRelay` named `bypass`: each function looks only among relays of its own class.
- A name or type that doesn't match **doesn't throw**. The library creates an unconnected state and logs one console warning containing "unknown to the backend". The control then does nothing, and nothing outside the web view's console says why. The binding checker catches both cases.
- Every state also carries `properties` sent by the attachment: for a slider `start`, `end`, `skew`, `name`, `label`, `numSteps`, `interval` and `parameterIndex`; for a toggle `name` and `parameterIndex`; for a combo box `name`, `parameterIndex` and `choices`.

## Register each relay with the browser options, and turn native integration on

```cpp
browser { juce::WebBrowserComponent::Options{}
              .withNativeIntegrationEnabled()
              .withOptionsFrom (driveRelay)
              .withOptionsFrom (bypassRelay)
              .withOptionsFrom (modeRelay)
              .withResourceProvider (...) }
```

- `withOptionsFrom(relay)` adds the relay's name to the list the page checks, the event listener that receives the page's edits, and a lifetime listener so the relay learns which browser to talk to. A relay that's constructed but never passed to `withOptionsFrom` is invisible to the page.
- **Relays don't turn native integration on.** Call `withNativeIntegrationEnabled()` yourself. Without it, JUCE's macOS web view has no handler for the page's messages: the library's calls fail in the console, and no edit reaches C++. (`withNativeFunction` turns native integration on by itself; relays and `withEventListener` don't.)
- The options are read once, when the browser is constructed. A relay added later doesn't reach an existing browser.

## Declare relays, then the browser, then the attachments

```cpp
private:
    juce::WebSliderRelay       driveRelay  { "drive" };
    juce::WebToggleButtonRelay bypassRelay { "bypass" };
    juce::WebComboBoxRelay     modeRelay   { "mode" };

    SinglePageBrowser browser { /* options as above */ };

    juce::WebSliderParameterAttachment       driveAttachment;
    juce::WebToggleButtonParameterAttachment bypassAttachment;
    juce::WebComboBoxParameterAttachment     modeAttachment;
```

C++ constructs members in declaration order and destroys them in reverse.
- **Each relay before the browser.** The browser's options hold the relays' listeners and plain pointers to the relays, and its destructor notifies each relay. A relay declared after the browser is destroyed first, so closing the editor touches a destroyed object. The options initialiser also needs the relays to exist already.
- **Each attachment after its relay.** An attachment keeps a reference to its relay and unregisters from it in its destructor.
- **Attachments after the browser** is the usual order, and JUCE's demo uses it. In 9.0.6 an attachment declared before the browser is also safe: the relay drops updates while it has no browser (or the browser isn't visible), and the page asks for an initial update when it creates each state, so nothing sent earlier is needed.
- Plain members are fine. `std::unique_ptr` members work too, but they add nothing: the same order applies to how they're created and destroyed.
- Initialise the attachments in the constructor's initialiser list: `driveAttachment (*state.getParameter ("drive"), driveRelay)`. `getParameter` returns `nullptr` for an unknown id, so a typo crashes when the editor opens.

The attachment constructor is `(RangedAudioParameter&, Relay&, UndoManager* = nullptr)`. Two arguments are enough. Pass the processor's `UndoManager` only if you want each gesture to start an undo transaction.

## What the attachment does

- It listens to the parameter. Changes from any thread (host automation, a preset load) reach the page on the message thread, through the relay.
- It sends the parameter's properties and value whenever the page requests an initial update, which the page does when it creates each state.
- It turns the page's edits into parameter changes the host sees:
  - **Slider:** `sliderDragStarted()` begins a change gesture (and an undo transaction), each `setNormalisedValue` sets the value within it, and `sliderDragEnded()` ends it.
  - **Toggle and combo box:** each `setValue` or `setChoiceIndex` becomes one complete gesture by itself. The page needs no gesture calls.

## The page side

```js
import * as Juce from "./juce/index.js";

const drive = Juce.getSliderState("drive");
const render = () => {
  knob.value = drive.getNormalisedValue();
  label.textContent = `${drive.getScaledValue().toFixed(1)} ${drive.properties.label}`;
};
drive.valueChangedEvent.addListener(render);       // no arguments
drive.propertiesChangedEvent.addListener(render);
```

- **Listeners take no arguments.** `valueChangedEvent` and `propertiesChangedEvent` call each listener with nothing. Read the value inside the listener from the state (`getNormalisedValue()`, `getScaledValue()`, `getValue()`, `getChoiceIndex()`). A listener written as `(value) => ...` gets `undefined`.
- `addListener` returns an id; `removeListener(id)` removes it. A component that's created and destroyed (React and similar) must remove its listeners when it goes away.
- **Values arrive asynchronously.** A new state starts with placeholders (a 0 to 1 range, value 0) and asks the C++ side for an update. Render from the listeners, not once at start-up.
- `getNormalisedValue()` and `setNormalisedValue()` use the 0 to 1 range of `AudioProcessorParameter::getValue()`. `getScaledValue()` is the plain value in the parameter's units.
- Calling a state function twice with the same name returns the same object.

### Gestures

Wrap each user edit of a slider in `sliderDragStarted()` and `sliderDragEnded()`, so the host records one gesture:

```js
let editing = false;
const end = () => { if (editing) { editing = false; drive.sliderDragEnded(); } };
knob.addEventListener("input", () => {
  if (!editing) { editing = true; drive.sliderDragStarted(); }
  drive.setNormalisedValue(Number(knob.value));
});
knob.addEventListener("change", end);
window.addEventListener("pointerup", end);
window.addEventListener("blur", end);
```

- Without the calls, the values still reach the parameter, but outside any gesture. Hosts that record automation by touch (latch or touch modes) then record nothing, or a broken curve, and undo doesn't group the edit.
- Every path that edits a slider needs both calls: drags, the mouse wheel, keys, double-click to reset, a text entry. An edit that starts and never ends leaves the host holding the gesture open.
- The page's own edits come back through `valueChangedEvent` (the parameter changed, so the attachment reports it). Skip moving the control from the listener while the user is dragging it, or the knob fights the pointer.

## Slider ranges the page can't reproduce

The page maps between normalised and plain values with only `start`, `end`, `skew` and `interval`. A parameter whose `NormalisableRange` uses custom conversion functions, or a symmetric skew, normalises differently in the page than in the host, so the page sets wrong values. Give such parameters a plain linear or skewed range, or keep them off WebView sliders.

## Combo boxes need a choice parameter

The combo attachment fills `properties.choices` only for an `AudioParameterChoice`. Attached to any other parameter, `choices` is empty and `getChoiceIndex()` is meaningless.

## Telling the host which control is under the mouse

Some hosts ask the editor which parameter is under the mouse (`AudioProcessorEditor::getControlParameterIndex`). For a WebView editor, register a `juce::WebControlParameterIndexReceiver` with `withOptionsFrom`, return its `getControlParameterIndex()` from the override, and on the page create a `ControlParameterIndexUpdater` with an attribute name, set that attribute on each control to its state's `properties.parameterIndex`, and call `handleMouseMove(event)` on every `mousemove`.

## Sources

- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebControlRelays.h` and `.cpp`: the three relays, `withOptionsFrom` registration (event listener, initialisation data, lifetime listener), the null-guarded browser pointer.
- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebBrowserComponent.h` and `.cpp`: `withNativeIntegrationEnabled` (off by default), `withNativeFunction`, `WebViewLifetimeListener`; native integration turned on when native functions exist.
- JUCE 9.0.6 `modules/juce_gui_extra/native/juce_WebBrowserComponent_mac.mm`: the page's message handler installed only when native integration is enabled.
- JUCE 9.0.6 `modules/juce_audio_processors/utilities/juce_ParameterAttachments.h` and `.cpp`: the Web attachments' constructors (undo manager defaults to `nullptr`), the properties sent, gesture handling per control type, choices only for `AudioParameterChoice`.
- JUCE 9.0.6 `modules/juce_gui_extra/misc/juce_WebControlParameterIndexReceiver.h`.
- JUCE 9.0.6 `modules/juce_gui_extra/native/typescript/webview-interop/src/index.ts`: the state classes, listeners called with no arguments, the "unknown to the backend" warning, the normalisation formulas, `ControlParameterIndexUpdater`.
- JUCE 9.0.6 `examples/Plugins/WebViewPluginDemo.h` and `WebViewPluginDemoGUI/src/App.tsx`: member order, plain members, the gesture calls, listener removal.
