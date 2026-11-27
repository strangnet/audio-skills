---
type: llm
focus: last_message
criteria: >
  The final message says the build output is in the project's own build folder
  (my-plugin/build/, including the "Example Audio - VST - Grit" folder and the native library in
  build/native/), and that the SDK keeps its tool cache, with the host simulator, inside the SDK
  clone (mpc-sdk/.sdk-tools/).
---
