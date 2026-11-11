#!/usr/bin/env python3
"""Worst-case stack per task entry of the linked image: the call graph from
the disassembly of the ELF, the frame sizes from the .su files (-fstack-usage)
of the objects and, for the link-time optimised code, of the LTO link
(BUILD_DIR/lto/*.ltrans.su); VLA bytes from a table (Opus at N = 960, C = 2,
16 kHz output). Library functions without .su count with the frame of their
prologue (push and sub sp). Indirect calls are followed only where CALLBACKS
names the targets (printf output, SimpleLink events and spawned functions);
ALLOWANCE adds the interrupt frame, the saved context and ROM driver calls.
A panic counts in full once; a second one inside it stops at once (NESTED),
and one raised inside the kernel's critical sections does not wait.

usage: tools/stackcheck.py ELF BUILD_DIR [IGNORED,FUNCS] ENTRY...
  e.g. tools/stackcheck.py build/cfw.elf build x,y player.o:task cloud.o:task
A function is named by its name, or file.o:name where the name is not
unique (static functions, the source file's base name).
SPDX-License-Identifier: GPL-3.0-or-later
"""
import glob, os, re, subprocess, sys
elf, builddir = sys.argv[1], sys.argv[2]
TOOLS = "../hackiebox_cfw_ng_cfw/arm-sdk/10-2020-q4-major/bin/arm-none-eabi-"
REPO = os.getcwd() + "/"

def base(name):
    """the name without the suffixes link-time optimisation adds"""
    return re.sub(r"(\.lto_priv\.\d+)+$", "", name)

def rel(path):
    path = path.split(":")[0]
    return path[len(REPO):] if path.startswith(REPO) else path

# functions of the image: address -> (name, source file)
funcs = {}
for line in subprocess.run([TOOLS + "nm", "-l", "--defined-only", elf], capture_output=True, text=True).stdout.splitlines():
    p = line.split(None, 3)
    if len(p) >= 3 and p[1] in "tTW":
        funcs[int(p[0], 16) & ~1] = (p[2], rel(p[3]) if len(p) > 3 else "")
by_name = {}
for a, (n, f) in funcs.items():
    by_name.setdefault(base(n), []).append(a)

def label(a):
    n, f = funcs[a]
    b = base(n)
    return b if len(by_name[b]) == 1 else f"{os.path.splitext(os.path.basename(f))[0]}.o:{b}"

# frame sizes: (source file, name) -> bytes; the LTO link's files last, so
# that they replace stale ones of earlier builds without LTO
frame, dynamic = {}, set()
sus = [s for s in glob.glob(builddir + "/**/*.su", recursive=True) if "/lto/" not in s]
for su in sus + sorted(glob.glob(builddir + "/lto/*.su")):
    for line in open(su):
        loc, size, kind = line.rstrip("\n").split("\t")
        parts = loc.split(":")
        frame[(parts[0], parts[-1])] = int(size)
        if "dynamic" in kind:
            dynamic.add(base(parts[-1]))
by_su_name = {}
for (f, n), s in frame.items():
    by_su_name.setdefault(n, []).append(s)

def own(a):
    n, f = funcs[a]
    b = base(n)
    if (f, b) in frame:
        return frame[(f, b)]
    cand = by_su_name.get(b, [])
    return max(cand) if cand else prologue.get(a, 0)

vla = {
    "celt_decode_with_ec": 504 + 44 + 3840 + 7680,
    "quant_all_bands": 2496,
    "bands.o:quant_band": 704,
    "bands.o:deinterleave_hadamard": 352, "bands.o:interleave_hadamard": 352,
    "alg_unquant": 704,
    "decode_pulses": 4 * (128 + 2),
    "compute_allocation": 336,
    "clt_mdct_backward": 3840,
    "celt_decoder.o:celt_decode_lost": 7680 + 3840,
    "pitch_search": 664 + 974 + 1240,
    "_celt_autocorr": 2048,
    "celt_fir": 48 + 2096,
    "celt_iir": 48 + 2208,
    "remove_doubling": 4 * 1025,
    "opus_decoder.o:opus_decode_frame": 16,
}

def vla_of(a):
    n, f = funcs[a]
    b = base(n)
    return vla.get(f"{os.path.splitext(os.path.basename(f))[0]}.o:{b}", vla.get(b, 0))

# call graph: direct calls and tail calls to another function's start
calls, indirect, selfcall, prologue, subbed, cur = {}, set(), set(), {}, set(), None
dis = subprocess.run([TOOLS + "objdump", "-d", "--no-show-raw-insn", elf], capture_output=True, text=True).stdout
for line in dis.splitlines():
    m = re.match(r"^([0-9a-f]+) <([^>]+)>:", line)
    if m:
        a = int(m.group(1), 16)
        cur = a if a in funcs else None
        if cur is not None:
            calls.setdefault(cur, set())
        continue
    if cur is None:
        continue
    m = re.search(r"\t(?:push|stmdb)(?:\.w)?\s+(?:sp!, )?\{([^}]*)\}", line)
    if m and cur not in subbed:  # until the frame is allocated: varargs functions push twice
        prologue[cur] = prologue.get(cur, 0) + 4 * sum(int(r.split("-")[1][1:]) - int(r.split("-")[0].strip()[1:]) + 1 if "-" in r else 1
                                for r in m.group(1).split(","))
    m = re.search(r"\tsub(?:\.w)?\s+sp, (?:sp, )?#(\d+)", line)
    if m and cur in prologue and cur not in subbed:
        prologue[cur] += int(m.group(1))
        subbed.add(cur)
        continue
    m = re.search(r"\t(bl|blx|b(?:eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?(?:\.[wn])?|cbn?z)\s+(?:r\d+, )?([0-9a-f]+) <([^>+]+)>", line)
    if m:
        t = int(m.group(2), 16)
        if t in funcs and t != cur:
            calls[cur].add(t)
        elif t == cur and m.group(1) == "bl":
            selfcall.add(cur)
    elif re.search(r"\tblx\s+r\d", line):
        indirect.add(cur)

CALLBACKS = {
    "_printf_common": r"__ssputs_r$",
    "_SlAsyncEventGenericHandler": r"(_sl_HandleAsync_\w+|_SlDrv\w*Event\w*|SimpleLink\w+Handler)$",
    "spawn_task": r"_SlDrvMsgReadSpawnCtx$",
}
for a, (n, f) in funcs.items():
    if base(n) in CALLBACKS:
        calls[a] |= {t for t, (m, _) in funcs.items() if re.match(CALLBACKS[base(n)], base(m))}
ALLOWANCE = 32 + 32 + 32  # exception frame, r4-r11 saved at a switch, ROM driver calls

# nested calls of a function that calls itself, the outermost included:
# delete_tree goes down to depth 3; quant_partition halves the band until
# LM is -1, from LM 3 for 20 ms frames; the decoder calls itself once for
# concealment.
RECURSION = {"delete_tree": 4, "quant_partition": 5, "opus_decode_frame": 2, "opus_decode_native": 2}

# celt_decode_lost is called before the VLAs of celt_decode_with_ec exist.
NO_VLA = {("celt_decode_with_ec", "celt_decode_lost")}
IGNORE = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and "," in sys.argv[3] else set()
PANIC = {"rtos_assert_failed", "vApplicationStackOverflowHook", "panic", "panic_from", "do_panic"}
NESTED = 8 + 16 + 24 + 64  # assert, panic, do_panic, vTaskSuspend
# Kernel code that runs with the scheduler suspended or interrupts masked:
# a panic there is not paced, so do_panic does not delay or suspend.
KERNEL = {"xTaskResumeAll", "xTaskIncrementTick", "vApplicationTickHook", "xTaskPriorityDisinherit",
          "xTaskPriorityInherit", "xTaskRemoveFromEventList", "vTaskPlaceOnEventList", "vTaskSwitchContext",
          "xTaskCheckForTimeOut", "vTaskPriorityDisinheritAfterTimeout", "vPortEnterCritical", "vPortExitCritical",
          "vTaskSuspendAll", "vTaskMissedYield", "send_from_isr"}
PACED = {"vTaskDelay", "vTaskSuspendAll", "xTaskResumeAll", "vTaskSuspend"}
memo = {}

def kind(f):
    return base(funcs[f][0]).split(".")[0]

def depth(f, kern=False, in_panic=False, stack=(), calm=False):
    kern = kern or kind(f) in KERNEL or kind(f).startswith("prv") or "FromISR" in kind(f)
    if f in stack:
        sys.exit(f"stackcheck: recursion at {label(f)}")
    key = (f, kern, in_panic, calm)
    if key in memo:
        return memo[key]
    best, path, bestown = 0, [], 0
    for g in calls.get(f, ()):
        if label(g) in IGNORE or (kern and kind(f) == "do_panic" and kind(g) in PACED) or (calm and kind(g) in PANIC):
            continue
        if in_panic and kind(g) in PANIC and kind(f) not in PANIC:
            d, p = NESTED, [label(g) + ":nested"]
        else:
            d, p = depth(g, kern, in_panic or kind(f) in PANIC, stack + (f,), calm)
        o = own(f) + (0 if (base(funcs[f][0]), base(funcs[g][0])) in NO_VLA else vla_of(f))
        if o + d > bestown + best:
            best, path, bestown = d, p, o
    if not path:
        bestown = own(f) + vla_of(f)
    if f in selfcall:
        n = RECURSION.get(base(funcs[f][0]))
        if not n:
            sys.exit(f"stackcheck: recursion at {label(f)}")
        bestown += (n - 1) * (own(f) + vla_of(f))
    memo[key] = (bestown + best, [f"{label(f)}:{bestown}"] + path)
    return memo[key]

def find(entry):
    if ":" in entry:
        obj, n = entry.split(":")
        stem = obj[:-2]
        hits = [a for a in by_name.get(n, []) if os.path.splitext(os.path.basename(funcs[a][1]))[0] == stem]
    else:
        hits = by_name.get(entry, [])
    if len(hits) != 1:
        sys.exit(f"stackcheck: {entry}: {len(hits)} functions match")
    return hits[0]

for entry in [a for a in sys.argv[3:] if "," not in a]:
    d, p = depth(find(entry))
    d += ALLOWANCE
    c = depth(find(entry), calm=True)[0] + ALLOWANCE
    print(f"{entry}: {d} bytes ({(d+3)//4} words), without a panic {c} bytes ({(c+3)//4} words)")
    print("   " + " > ".join(p[:40]))

print("dynamic frames without a VLA entry:", " ".join(sorted({label(a) for a in funcs if base(funcs[a][0]) in dynamic and not vla_of(a)})))
print("functions with indirect calls:", " ".join(sorted(label(a) for a in indirect)))
