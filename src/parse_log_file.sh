#!/bin/bash
set -eo pipefail
git -C "$1" show "$2" | ./parse_lua.lua -
