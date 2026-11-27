---
type: llm
focus: last_message
criteria: >
  The final message says JUCE should be found through a CMake cache variable or an environment
  variable (for example JUCE_DIR, or find_package with CMAKE_PREFIX_PATH), not through an
  absolute path written into CMakeLists.txt.
---
