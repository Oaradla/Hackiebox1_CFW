# Toniebox custom firmware

Custom firmware (CFW) for the first-generation Toniebox, both kinds: the box
with the TI CC3200 chip and the box with the ESP32-S3. It works together with
teddyCloud. A box with the CFW plays Tonies like the original firmware and
adds the functions listed below; the settings for them are made in
teddyCloud's web UI. The original firmware stays on the box, and the way back
is always open.

The firmware is in test. Changing the firmware of a box is at your own risk
(see [Legal](#legal)).

**Manual with pictures:** [English](docs/manual/en.md) ·
[Deutsch](docs/manual/de.md). It covers installation, every setting and the
way back.

## Functions

| Function | What it does | Manual |
| --- | --- | --- |
| Tonie settings | Per Tonie: resume, global resume, shuffle, sleep timer with fade-out, own volume limits and LED brightness, slap, tilt and volume lock. | [7](docs/manual/en.md#7-tonie-settings) |
| Box settings | Volume limits in all 16 steps (the original knows 4), LED brightness including dimmed and off permanently, the three locks, switch-off times on battery and on the charging station. | [6](docs/manual/en.md#6-box-settings) |
| Event tags | A spare tag that changes the next Tonie or the whole box when placed: switch settings, a sleep timer, volume limit and LED set with the ears; optionally only until switch-off. | [8](docs/manual/en.md#8-event-tags) |
| Global resume | A Tonie continues on any box where it stopped on another one. | [9](docs/manual/en.md#9-global-resume) |
| Remote control | From teddyCloud and through MQTT from Home Assistant: pause, continue, stop, chapters, volume, play a Tonie or a library file without a tag, live state. | [10](docs/manual/en.md#10-remote-control) |
| Battery | Charge in percent from the running time, remaining time, charging station. | [5](docs/manual/en.md#5-the-box-in-teddycloud) |
| Switch off with both ears | Press both ears and let go within 2 seconds: the box switches off at once, also with a Tonie on it. On unless switched off per box. | [12](docs/manual/en.md#12-gestures-on-the-box) |
| Slap upside down | Box ears down, slap its side: back to the very beginning of the Tonie; with shuffle a new order. Always on. | [12](docs/manual/en.md#12-gestures-on-the-box) |
| Any NFC tag as a Tonie | Every ISO 15693 tag (stickers, cards) works like a Tonie; the box only reads its ID. Always on. | [7](docs/manual/en.md#7-tonie-settings) |
| Setup page | Own page in several languages: Wi-Fi with a scan list, server, certificates, delete functions (instead of the factory reset). | [4](docs/manual/en.md#4-the-setup-page-of-the-box) |
| Safe updates | Through teddyCloud with release, beta and alpha channels and GitHub download; a new build starts once as a trial and the box goes back on its own if it fails. | [11](docs/manual/en.md#11-box-update) |

A box without any CFW settings behaves like the original firmware, except for
the three functions marked always on. The settings are stored on the box's SD
card, so they also work offline.

Further differences from the original:

- **Server without patching the flash.** The box reads its server from the
  SD card (`/cfw/config.txt`) or the setup page and never contacts the
  manufacturer's servers on its own.
- **More robust.** Malformed server answers, broken files on the SD card,
  very long Wi-Fi names or odd inputs on the setup page are ignored instead
  of crashing the box.
- **Not there:** the factory reset through the ears (use the delete
  functions of the setup page). Of the original's log records the box sends
  only those teddyCloud evaluates.

## What you need

- A first-generation Toniebox with CC3200 or ESP32-S3. The Toniebox 2 and the
  box with the CC3235 are not supported.
- teddyCloud with CFW support ([teddycloud_cfw](https://github.com/Oaradla/teddycloud_cfw);
  global resume needs `tc_v0.7.1-cfw.9` or later). With an unmodified
  teddyCloud the box plays as usual, but none of the functions can be set.
- The release package `toniebox-cfw-<version>.zip` from the releases of this
  repository. teddyCloud can also download it itself.

How to get the firmware onto a box, original or already running with
teddyCloud: [manual, chapter 3](docs/manual/en.md#3-getting-the-custom-firmware-onto-a-box).

## Legal

Toniebox, Tonie and tonies are trademarks of tonies GmbH (formerly Boxine
GmbH). This project is not affiliated with, endorsed or supported by tonies
GmbH; the names only say which devices the software works with.

Changing the firmware of a box, opening it or connecting to its debug port
is at your own risk: a box can become unusable, and it can affect claims
against the manufacturer. The software comes without any warranty (see the
licence).

## For developers

### Repository

| Path | Content |
| --- | --- |
| `src/` | the firmware, shared by both platforms |
| `src/cc3200/` | the CC3200 platform: drivers, network processor, SD card |
| `esp32/` | the ESP32-S3 platform as an ESP-IDF project, see [`esp32/README.md`](esp32/README.md) |
| `card/cfw/setup.htm` | the setup page |
| `tools/` | `release.sh` (release package), `mkimage.py`, `esp32img.py`, `bootstate.py`, `taftest`, `stackcheck.py` |
| `tests/host/` | host tests of the shared code |
| `docs/` | [`protocol.md`](docs/protocol.md) (what a server has to do for the CFW), `tls-sni.md`, the manual |
| `third_party/` | libopus, FatFs, FreeRTOS, TI SimpleLink host driver, unedited |

### Building the CC3200 image

Requirements: GNU Arm Embedded toolchain 10-2020-q4, TI CC3200 SDK 1.5.0,
Python 3, GNU make. The defaults point at the copies in the neighbouring
`hackiebox_cfw_ng_cfw` repository; override them in `config.local.mk`:

```make
ARM_GCC_DIR = /opt/gcc-arm-none-eabi-10-2020-q4-major/bin
CC3200_SDK  = /opt/ti/cc3200-sdk
```

`make` builds `build/cfw-slot.bin`: the image (loaded at 0x20004000) with
the build block and the SHA-256 digest text at its end, usable as
`/revvox/boot/ng-cfwN.bin` of the SD bootloader. The build number is the
commit time; the version is `CFW_<CFW_VERSION>`.

Build switches (`make VAR=value`; the Makefile does not track flag changes,
so `make clean` after changing one):

| Switch | Default | Meaning |
| --- | --- | --- |
| `CFW_DEBUG` | 1 | 2 adds the verbose bring-up diagnostics (`debug_verbose`) on UART0 |
| `CFW_VERBOSE` | (none) | modules with `debug_verbose` output at level 1, e.g. `CFW_VERBOSE="net cloud"` (all at once do not fit the SRAM) |
| `CFW_LOG_UART` | 0 | 1 copies the binary log frames to UART0 |
| `CFW_HIBERNATE` | 1 | 1 uses hibernation for the off state and the hibernate restart; 0 an MCU reset and a wait with the processor running (drains the battery) |
| `CFW_OPUS_SMALL` | 1 | `cwrs.c` without its pulse-count tables, about 5 KB less SRAM |

`make stackcheck` prints the worst-case stack per activity from the `.su`
files and the call graph (needs a linked build).

### Memory budget (CC3200)

The image runs from SRAM: at most 212992 bytes of image, and all code, data
and stacks share the 240 KB from 0x20004000; the 16 KB below it hold the
no-init buffers (section `.lowram`) once the handover record is read. Current
build: about 160 KB code, 98 KB data and stacks (Opus decoder state 17.9 KB,
player stack 20 KB for the Opus worst case of packet-loss concealment, log
buffer 6.9 KB), about 1.6 KB left above the 1.75 KB main stack. Every further
feature has to pay for itself in SRAM.

### Release package

`tools/release.sh VERSION` builds `build/release/toniebox-cfw-VERSION.zip`
(stored without compression, so teddyCloud reads each file on its own):
`cc3200/ng-cfw.bin` with the SD bootloader, its preloader and a ready SD card
tree, `esp32/toniebox-cfw-esp32.bin`, `setup.htm` and the READMEs. It needs a
clean tree, ESP-IDF 5.4.2 and a clean checkout of the SD bootloader.

### Setup page

`card/cfw/setup.htm` goes to `/cfw/setup.htm` on the card. In setup mode the
firmware serves it itself on port 80 (`src/page.c` lists the interface);
without the file the box offers the network processor's own page (Wi-Fi
only).

The page has its own version, apart from the firmware's: `cfw-page-version`
in its head, raised in the same commit as any change to the page, and
`cfw-page-requires`, the oldest firmware it works with (raise it when the
page starts to use something only a newer firmware has). A release without a
change to the page does not make teddyCloud deliver it again. The page shows
its version and the firmware's (`GET /version.txt`).

### Tests

`sh tests/host/all.sh <content file with three chapters>` (for example
`tools/taftest` output) builds and runs every host test with the address and
undefined-behaviour sanitizers: player and extension features, cloud
requests and settings files, log stream and log connection, setup-mode rules,
the update install, the retained state and the setup page server. Nothing in
them replaces a test on a device.

### Code style

The conventions of the Revvox projects (teddyCloud):

- `make format` formats the own sources with the `.clang-format` in the
  root, `make format-check` only checks: Allman braces, 4 spaces, braces
  around every body. `third_party/`, `src/fatfs/` and `src/ffconf.h` are not
  formatted.
- Functions and variables in snake_case with the module as prefix, types as
  typedefs named `<name>_t`, macros and enum values in upper case.
- Vendored code is not edited in place: a patched file is a copy under
  `src/` (`src/fatfs/ff.c`, the patches marked `FF_TB_PATCHES`), identical to
  the original except the patch.
- Commits follow Conventional Commits, `type(scope): summary`. Style and
  refactoring commits keep the behaviour.

## Licence

GPL-3.0-or-later (`COPYING`), for both platforms (the ESP32 build uses
ESP-IDF, Apache-2.0). Third-party code under `third_party/` keeps its own
licence: libopus 1.1 (BSD-3-Clause), FatFs R0.15a (FatFs licence, BSD-1-Clause
style), FreeRTOS (MIT), TI SimpleLink host driver (BSD-3-Clause). The TI
CC3200 SDK is used from outside the repository.
