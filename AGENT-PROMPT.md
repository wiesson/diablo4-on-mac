# Prompts for reuse

Two ready-to-paste prompts: one for people who have exactly this symptom, one for the
general method behind the finding.

## 1. "I have this exact crash" (fastest path)

```
My CEF/Chromium-based Windows app crashes under Wine. Every CEF renderer process dies
with an unhandled exception 0x80000003 (STATUS_BREAKPOINT) at one byte-identical
address inside libcef.dll, and respawns in a loop. The browser process keeps running.
GPU flags (--in-process-gpu, --disable-gpu, --no-sandbox, software GL) change nothing,
and there is no "[FATAL:...] Check failed" line anywhere in the log.

Please verify whether this is the known Wine copy-on-write reporting bug:

1. Get the module base of libcef.dll (winedbg "info share", or WINEDEBUG=+loaddll)
   and compute RVA = crash address - module base.
2. Read the three bytes at that RVA in libcef.dll on disk. If they are cc 0f 0b
   (int3; ud2), it is Chromium's IMMEDIATE_CRASH, i.e. a failed CHECK() whose message
   is compiled out - not a debugger breakpoint.
3. Disassemble backwards from there to find the branch that jumps to it. If it is
   a comparison against 4 after a call to KERNEL32!VirtualProtect, the failing check is
   CHECK(old_protection == PAGE_READWRITE).
4. If confirmed, re-run the app with WINE_SIMULATE_WRITECOPY=1.

Do not modify any game or application binary. Do not add more browser flags.
Report what you found at each step before changing anything.
```

## 2. "Diagnose any repeatable fixed-address crash in a PE under Wine"

This is the method that produced the finding. It is not specific to CEF.

```
A Windows application under Wine crashes repeatedly at ONE byte-identical address.
Diagnose it statically before changing any configuration. Do not add flags by trial
and error, and do not modify application binaries.

Step 1 - Establish what the address is.
  Get the faulting module and its load base from the log (WINEDEBUG=+loaddll) or from
  winedbg's module list. RVA = faulting address - module base. Sanity-check that the
  RVA falls inside the module's virtual size.

Step 2 - Read the instruction, do not guess it.
  Parse the PE section headers, map the RVA to a file offset, and dump the bytes.
    cc 0f 0b  -> int3; ud2 = Chromium/LLVM IMMEDIATE_CRASH: a failed CHECK whose
                 message is stripped in official builds. Stop looking for it in logs.
    cc alone  -> a plain breakpoint, often a debugger-detection or an assert stub.
    0f 0b     -> ud2, usually an unreachable/abort path.

Step 3 - Recover the failing condition.
  Disassemble backwards to the start of the enclosing function. Identify the branch
  whose target is the faulting address: that branch's condition IS the assertion that
  failed. Note the exact compared value.

Step 4 - Name the API involved.
  If the function calls through the IAT (call dword ptr [X]), resolve X against the
  import directory to get DLL!Symbol. Now you know which API returned something the
  application refused to accept.

Step 5 - Find the caller and the data.
  Scan .text for direct call sites of the faulting function. If there is exactly one,
  read the arguments it pushes: they usually name the exact address, size or object
  involved, which turns the hypothesis into a single measurable value.

Step 6 - Measure, then fix.
  Write the smallest possible probe that calls the same API the same way and prints
  the value the application rejected. Run it once with each candidate configuration
  and compare. Only then change the configuration.

Report each step's concrete output. If a step contradicts the hypothesis, say so
instead of continuing.
```

## Why the method matters here

Every renderer flag tried before this analysis was wasted effort: the crash was
a page-protection assertion and no browser flag could ever have moved it. The
decisive evidence was three bytes read from a DLL on disk, with the application
not running.
