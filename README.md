# CEF under Wine: renderer crashes with `0x80000003` at a fixed `libcef.dll` address

**TL;DR — set `WINE_SIMULATE_WRITECOPY=1`.**

Found while getting the Battle.net launcher (and through it Diablo IV) to run under a
self-built Wine wrapper on an Apple Silicon Mac. The root cause is not graphics,
not the sandbox and not the GPU process. It is how Wine reports the *previous*
page protection of a copy-on-write image page.

## Symptom

```
wine: Unhandled exception 0x80000003 in thread 0348 at address 6DE900E1 (thread 034c), starting debugger...
```

You are probably looking at this bug if **all** of these hold:

- the address is **byte-identical on every crash**, across fresh prefixes and reboots
- every CEF **renderer** process (`CrRendererMain`) dies and respawns in a loop, while the
  browser process (`CrBrowserMain`) and utility processes keep running fine
- there is **no** `[FATAL:...] Check failed:` line in the log, even though other
  Chromium `ERROR:` lines are being written
- GPU flags change nothing: `--in-process-gpu`, `--disable-gpu`,
  `--disable-gpu-compositing`, `--no-sandbox`, software GL — all identical crash

## Root cause

The address is Chromium's `IMMEDIATE_CRASH()` — the byte sequence `cc 0f 0b`
(`int3; ud2`). In official builds the `CHECK()` message is compiled out, which is why
nothing is logged. The failing check is `base::ProtectedMemory`'s read-only transition:

```c
DWORD old;
CHECK(VirtualProtect(page, 4096, PAGE_READONLY, &old));  /* succeeds */
CHECK(old == PAGE_READWRITE);                            /* 4 — fails under Wine */
```

Wine maps writable PE image sections copy-on-write and reports `PAGE_WRITECOPY (8)`
for a page that has never been written. Windows reports `PAGE_READWRITE (4)` for the
same page. Chromium protects a page it has not written to yet, so the mismatch is hit
every single time.

In Battle.net build `17778`'s `libcef.dll` the guarded region is exactly one page at
**RVA `0x097E9000`**, size `0x1000`, reached from a single call site at RVA `0x85D4E0`:

```asm
0085d4e3  mov byte ptr [0x19874cc4], 1   ; "initialized" flag (different page)
0085d4ea  push 0x1000                    ; size
0085d4ef  push 0x197e9000                ; addr   (preferred base 0x10000000)
0085d4f4  call 0x16d00a0                 ; SetReadOnly(addr, size)
```

## Fix

```sh
export WINE_SIMULATE_WRITECOPY=1
```

The switch already exists in CrossOver-derived Wine sources
(`dlls/ntdll/unix/loader.c:hacks_init`, `dlls/ntdll/unix/virtual.c:NtProtectVirtualMemory`):
it sets `VPROT_COPIED` and adjusts the protection value returned to the application.
No binary patching, no modified game or DLL files, no launcher flags needed.

If your Wine build does not have the switch, the equivalent behaviour is: report
`PAGE_READWRITE` instead of `PAGE_WRITECOPY` as the old protection of an image page.

## Verification

`tools/writecopy-probe32.c` maps a private, uninitialised copy of `libcef.dll` and
checks the actual target page. Same engine, same prefix, only the switch differs:

| operation | switch `0` | switch `1` |
|---|---:|---:|
| initial `VirtualQuery` protection | 8 | 8 |
| `VirtualProtect(READONLY)`, returned old | **8** | **4** |
| `READWRITE` → touch byte → `READONLY`, returned old | **8** | **4** |

Build with llvm-mingw (or any i686 PE toolchain):

```sh
i686-w64-mingw32-clang -nostdlib -Wl,-subsystem:console \
  -o writecopy-probe32.exe tools/writecopy-probe32.c -lkernel32
```

Adjust the DLL path and the RVA inside the file if your build differs.

## Confirming it is the same bug in your app (about two minutes)

1. Note the crash address and the module base (`winedbg` → `info share`, or
   `WINEDEBUG=+loaddll`). RVA = address − base.
2. `python3 tools/pe-inspect.py <the.dll> --addr <crash-addr> --base <module-base>`
   If it prints `cc 0f 0b`, it is a Chromium `CHECK`, not a debugger breakpoint —
   stop trying flags.
3. Re-run with `WINEDEBUG=+virtual,+seh` and find the last `NtProtectVirtualMemory`
   on the crashing thread. If its target page is the one in the faulting function and
   the new protection is `2` (`PAGE_READONLY`), this is the bug.
4. Set `WINE_SIMULATE_WRITECOPY=1`.

## Scope

This is ordinary compatibility debugging. It is not specific to Battle.net: any
Chromium/CEF application under Wine can hit it, since `base::ProtectedMemory` is
generic Chromium infrastructure. Nothing here modifies, bypasses or circumvents any
game binary, DRM or anti-cheat mechanism.

## Not included

No logs, no game files, no Wine or engine binaries, no account data. Only the finding,
a probe and a small PE inspection helper.

## License

MIT, see `LICENSE`.
