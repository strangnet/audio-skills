#!/usr/bin/env bash
# A JUCE 9 compressor that was renamed from "Squish" to "Squash" and has no PLUGIN_CODE,
# so JUCE picks a random code on every configure. No toolchains are needed.
set -euo pipefail
mkdir -p Source

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.22)
project(Squash VERSION 1.1.0)
set(JUCE_DIR "$ENV{JUCE_DIR}" CACHE PATH "JUCE checkout")
add_subdirectory(${JUCE_DIR} juce)
# Renamed from "Squish" in 1.1.0.
juce_add_plugin(Squash
    COMPANY_NAME "Example"
    PLUGIN_MANUFACTURER_CODE Exmp
    FORMATS VST3 AU
    PRODUCT_NAME "Squash"
    COPY_PLUGIN_AFTER_BUILD TRUE)
target_sources(Squash PRIVATE Source/PluginProcessor.cpp)
target_link_libraries(Squash PRIVATE juce::juce_audio_utils)
CMAKE

cat > Source/PluginProcessor.cpp <<'CPP'
// Processor omitted from this excerpt: a stereo compressor with five parameters.
CPP
