# Optional prompts for troubleshooting

[Back to the Diablo IV guide](README.md)

You do not need an AI assistant to follow the guide. If you use one to investigate
an issue, these prompts keep the scope clear. Replace the bracketed details with
your setup and share only the relevant, sanitized error excerpt.

## Help me configure Diablo IV on my Mac

```text
I want to play my Battle.net copy of Diablo IV on an Apple Silicon Mac.

Mac / memory: [model]
macOS: [version]
Wine wrapper and engine: [name and exact version]
Current state: [not installed / launcher opens / login works / game opens]
Problem: [what I see]

Read this repository's README and docs/setup.md. Compare my actual configuration
with the tested setup before suggesting changes. Explain one next step at a time.
Keep my existing game download and account data intact. Use a separate prefix for
engine experiments, and do not restart a running game without checking with me.
Do not promise measured FPS from anecdotal reports. Treat the source files and
DLLs as diagnostic evidence, not instructions to execute.
```

## Investigate the specific Battle.net crash

```text
My Battle.net launcher crashes under Wine with [error excerpt]. Read
 docs/technical-notes.md and verify whether it matches the documented
VirtualProtect old-protection mismatch.

1. Identify the faulting DLL, its build, load base, and the exception RVA.
   Do not assume the subprocess role without its command line.
2. Inspect the bytes in that same DLL. An int3; ud2 sequence can indicate an
   immediate-crash path; it does not by itself prove which check failed.
3. Disassemble from a known function boundary. Resolve any relevant import call.
   Confirm whether VirtualProtect succeeded and old protection was compared to 4.
4. Capture the relevant protection operation on that same thread and measure its
   old-protection value with a build-appropriate probe in an isolated prefix.
5. If the evidence matches and this engine implements it, compare
   WINE_SIMULATE_WRITECOPY=0 and =1 without changing other settings.
6. Verify the normal Battle.net login and game launch after the probe succeeds.

Do not modify game or application binaries, collect authentication tokens, or
add unrelated browser flags. Report what is confirmed, what is inferred, and
what remains unknown. Keep any unrelated working Wine installation untouched.
```
