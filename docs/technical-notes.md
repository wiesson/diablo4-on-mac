# Technical notes: the Battle.net write-copy crash

[Back to the guide](../README.md) · [Working configuration](setup.md)

This is the investigation behind one launcher fix. If you just want to play,
start with the setup guide; these tools are optional.

## What we observed

With the tested CrossOver-derived Wine engine, Battle.net build 17778 repeatedly
raised an unhandled `0x80000003` inside its 32-bit `libcef.dll`. A fresh prefix
reproduced it. Switching renderer flags did not change the failing instruction.
We did not capture enough command-line evidence to label every crashing child
process as a CEF renderer; the exception and module mapping are the stronger evidence.

In the recorded run:

```text
faulting address: 0x6DE900E1
libcef load base: 0x6C7C0000
relative virtual address (RVA): 0x016D00E1
```

Absolute addresses can change between runs. Compare the instruction and its RVA
within the **same DLL build**, rather than requiring an identical absolute address.

## The rejected return value

Static inspection identified an `int3; ud2` sequence (`cc 0f 0b`). The preceding
instructions call `KERNEL32!VirtualProtect`, check that the call succeeded, and
then compare the returned old protection with `4` (`PAGE_READWRITE`). The crash
at this RVA is the branch taken when that second comparison fails.

Equivalent pseudocode for the observed checks:

```c
DWORD old;
CHECK(VirtualProtect(page, 4096, PAGE_READONLY, &old));
CHECK(old == PAGE_READWRITE);
```

The disassembly establishes the comparison, not an exact Chromium source-level
symbol name. The sequence is consistent with Chromium's immediate-crash paths;
**those three bytes alone do not identify the failing check or its cause**.
No descriptive CHECK message was present in our captured logs.

The actual `+virtual,+seh` trace showed the failing thread changing the page at
`0x75FA9000` to protection `2` (`PAGE_READONLY`), immediately before the exception.
That page is at RVA `0x097E9000` in this libcef build, with size `0x1000`.

The probe below reproduced Wine reporting the old protection as `8`
(`PAGE_WRITECOPY`), where this application requires `4` (`PAGE_READWRITE`). We
have not included an independent native-Windows probe run, so the verified claim
is about the application's expectation and the measured Wine behavior.

## The existing compatibility switch

```sh
WINE_SIMULATE_WRITECOPY=1
```

In the bundled Wine source, `dlls/ntdll/unix/loader.c:hacks_init` reads the variable.
`dlls/ntdll/unix/virtual.c:NtProtectVirtualMemory` uses it to mark the copy-on-write
page as copied and adjust the old protection returned to the caller.

It is already implemented in the tested CrossOver-derived engine. We did not
patch libcef, Battle.net, or Diablo IV. Do not implement a blanket replacement of
all `PAGE_WRITECOPY` values: the existing implementation handles view/page state,
and the correct behavior is more specific than renaming a constant.

With the switch enabled, Battle.net loaded the login page, the user signed in,
and a normal Diablo launch completed SSO authentication and entered the game.
The launch profile also retained the matched DXMT components and
`--in-process-gpu`; we did not establish that those could be removed.

## Controlled comparison

[`writecopy-probe32.c`](../tools/writecopy-probe32.c) loads a private, uninitialized
libcef image mapping and checks the target page. It modifies only its own process's
mapping, not the DLL on disk. It writes a small result log inside the test prefix.

Same engine and prefix, changing only the switch:

| Operation | Switch `0` | Switch `1` |
|---|---:|---:|
| Initial `VirtualQuery` protection | 8 | 8 |
| `VirtualProtect(READONLY)`, returned old | **8** | **4** |
| `READWRITE` → touch byte → `READONLY`, returned old | **8** | **4** |

The probe is **specific to the recorded Battle.net DLL build**: its Windows path
and page RVA are hardcoded. Verify and adapt both before using it with a different
build. Use a separate test prefix for diagnostic programs.

A build recipe matching the toolchain used in the investigation:

```sh
clang -target i686-pc-windows-msvc -O2 -ffreestanding \
  -c tools/writecopy-probe32.c -o writecopy-probe32.obj

# Supply a PE linker (lld-link) and the matching Wine i386 import library.
lld-link /entry:mainCRTStartup /subsystem:console /nodefaultlib \
  /out:writecopy-probe32.exe writecopy-probe32.obj \
  /path/to/engine/lib/wine/i386-windows/libkernel32.a
```

The repository does not install that toolchain or provide engine binaries.
Run the resulting executable under the test engine once with the switch `0` and
once with `1`, keeping the rest of the environment unchanged. Our launcher settings
are in the [setup guide](setup.md#configure-the-launcher).

## Inspecting your own crash

1. Get the faulting address and libcef's load base from the same run, for example
   with `WINEDEBUG=+loaddll,+seh`. Calculate RVA = fault address − module base.
2. Inspect that RVA in the **same DLL** with the read-only PE helper:

   ```sh
   python3 tools/pe-inspect.py libcef.dll --addr 0x6DE900E1 --base 0x6C7C0000
   python3 tools/pe-inspect.py libcef.dll --iat 0x197BC9E0
   ```

   These example addresses belong to build 17778. Byte inspection and import
   lookup use only Python's standard library. This helper's import lookup is
   intended for the 32-bit PE used here.
3. Disassemble from a known function boundary and identify the branch leading to
   the crash. Verify the API called through the import table and the compared value.
   The helper's optional `--disasm N` needs Capstone and shows a window around the
   address; that window is not guaranteed to begin on an instruction boundary.
4. If the comparison matches, use a short `WINEDEBUG=+virtual,+seh` trace to locate
   the protection change on the **same thread**, then confirm the returned value
   with a probe. A nearby `VirtualProtect` call or `cc 0f 0b` alone is insufficient.
5. Test the compatibility switch with the same engine and reproduce the normal
   application launch, not just the synthetic probe.

## Scope of the result

The verified fix is for this Battle.net/libcef build and Wine configuration.
Other CEF applications may encounter a similar mismatch, but need their own evidence.
This is a compatibility fix, not an FPS optimization or proof that all of
GameToMac's custom patches are required.

The original Sikarugir engine's slow Diablo start is a separate finding. Its log
reached “Initializing graphics subsystem,” which does not establish successful
D3D12 device creation. Its BOOLEAN probe passed. Neither result justifies assuming
that this CEF crash, a BOOLEAN issue, and game startup speed share one cause.
