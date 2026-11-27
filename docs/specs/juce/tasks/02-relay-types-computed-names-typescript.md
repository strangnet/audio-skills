# 02: The checker handles relay types, computed names and TypeScript pages

Status: done
Spec: [juce](../../juce.md)
Blocked by: 01

## Delivers
The checker reports a relay requested with the wrong state type, gives one warning instead of errors when a relay type's names are computed on one side, and reads state requests in TypeScript and JSX page sources. JUCE's WebView plugin demo passes as a fixture.

## Scenarios
- Checker: a relay requested with the wrong state type → `relay-type` error
- Checker: names that aren't string literals on one side for one relay type → one `relay-name` warning, no unmatched-name errors for that type
- Checker: a page written in TypeScript or JSX → its state calls are read
