#!/bin/bash

tmpfile=$(mktemp -d)
wd="$tmpfile/smods"
mkdir "$wd"
# Note: requires a modified lovely from https://github.com/WilsontheWolf/lovely-injector/tree/recommender-changes
# The fork of lovely used is modified to have debug info in the apply_patches, disable logging and skip load_now modules
LD_PRELOAD="./liblovely.so" LOVELY_MOD_DIR="$tmpfile" /usr/bin/nvim -l parse_lovely_changes.lua "$wd" "$1" "$2"
rm -rf "$tmpfile"
