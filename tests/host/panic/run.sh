#!/bin/sh
# Host test of the breakdown marker in the retained words (panic.c).
# SPDX-License-Identifier: GPL-3.0-or-later
set -e
cd "$(dirname "$0")/../../.."
B=build/host/panic
mkdir -p $B
# unused functions of panic.c are dropped, so they need no stubs
gcc -fsanitize=address,undefined -fno-sanitize-recover=all -g -O1 -Wall -Wno-unused-function -Wno-pointer-to-int-cast -ffunction-sections -Wl,--gc-sections -Uunix -DCFW_HIBERNATE=1 -DCFW_BUILD_TIME=1u -DCFW_VERSION=\"0.1.0\" -Itests/host/panic/inc -Itests/host/player/inc -Itests/host/inc -Isrc -o $B/panic_test tests/host/panic/harness.c
$B/panic_test
