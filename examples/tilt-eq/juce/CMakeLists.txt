# JUCE wrapper for the tilt-EQ example: VST3 and AU through JUCE 9, CLAP through
# clap-juce-extensions. The DSP lives in ../core and is included by relative path.
#
#   cmake -S examples/tilt-eq/juce -B build/tilt-eq/juce -G Ninja \
#         -DCMAKE_BUILD_TYPE=Release -DJUCE_DIR=/path/to/JUCE
cmake_minimum_required(VERSION 3.22)
project(TILT_EQ VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# JUCE comes from a cache variable or the JUCE_DIR environment variable, never a fixed path.
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "Path to a JUCE 9.0.x checkout")
if(NOT EXISTS "${JUCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "Set JUCE_DIR (cache variable or environment) to a JUCE 9.0.x checkout")
endif()
add_subdirectory("${JUCE_DIR}" juce)

# CLAP: JUCE 9.0.6 has no native CLAP client, so use clap-juce-extensions,
# pinned to a tested commit. Change the pin only after re-running the example check.
include(FetchContent)
FetchContent_Declare(clap-juce-extensions
    GIT_REPOSITORY https://github.com/free-audio/clap-juce-extensions.git
    GIT_TAG 3837f4a6ed2ab0ba46aba69ae5b7041c7c64ce74
    GIT_SUBMODULES_RECURSE TRUE)
FetchContent_GetProperties(clap-juce-extensions)
if(NOT clap-juce-extensions_POPULATED)
    FetchContent_Populate(clap-juce-extensions)
    add_subdirectory(${clap-juce-extensions_SOURCE_DIR} ${clap-juce-extensions_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()

juce_add_plugin(TiltEq
    COMPANY_NAME "strangnet"
    BUNDLE_ID "com.strangnet.tilteq"
    PLUGIN_MANUFACTURER_CODE Stng
    PLUGIN_CODE Tilt
    FORMATS VST3 AU
    PRODUCT_NAME "Tilt EQ"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    AU_MAIN_TYPE kAudioUnitType_Effect
    VST3_CATEGORIES Fx EQ
    NEEDS_WEB_BROWSER FALSE
    NEEDS_CURL FALSE)

target_sources(TiltEq PRIVATE Source/PluginProcessor.cpp)

target_compile_definitions(TiltEq
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(TiltEq
    PRIVATE
        juce::juce_audio_utils
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags)

clap_juce_extensions_plugin(TARGET TiltEq
    CLAP_ID "com.strangnet.tilteq"
    CLAP_FEATURES audio-effect equalizer stereo mono)
