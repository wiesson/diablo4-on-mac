# Something is not working

[Back to the guide](../README.md)

Start with what you see. Keep a working installation intact while investigating.

| What you see | First thing to try |
|---|---|
| Battle.net's login window crashes or keeps restarting | In the tested engine, set `WINE_SIMULATE_WRITECOPY=1` on the Battle.net launch configuration, then restart that wrapper normally |
| “Playing Now,” but no Diablo window | Check that you used the configured wrapper, not an older shortcut. The label alone does not prove that the game has finished starting |
| Diablo opens but reports login error 1910 | Exit the game and launch it through the signed-in Battle.net in the same prefix |
| Battle.net says “Update” | Complete the update, then use Play; an existing download may still need patching |
| No sound in Bluetooth headphones | Connect/select them in macOS, exit Diablo normally, then relaunch it from Battle.net |
| Sound stops only when switching apps | Check **Play in Background** in Diablo's sound settings |
| Graphics run slowly or stutter | Start with the [settings guide](settings.md); keep the engine unchanged while comparing graphics options |

## Battle.net still crashes

The write-copy setting addresses one confirmed failure, not every launcher crash.
Check that your Wine build actually implements the switch and that your wrapper
passes it to Battle.net. Adding `export` in a Terminal window does not configure
an unrelated app already open from Finder.

For our crash, Wine logged an unhandled `0x80000003` in `libcef.dll`. Disassembly
and a small probe confirmed the specific rejected memory-protection value. The
exception number alone is not enough to identify it. See the
[technical notes](technical-notes.md) if you need to establish whether yours matches.

We also encountered a separate renderer mismatch: Sikarugir's DXMT build expected
window-driver support absent from the GameToMac engine. The matching DXMT v0.80
components resolved that part; the write-copy setting resolved the later CEF crash.
Both compatibility and launch configuration matter.

## “Playing Now” without a window

Our old wrapper still launched the original Sikarugir engine after the separate
Diablo test worked. Returning to that shortcut reproduced the old behavior.
Make sure the launcher, prefix, and engine are those in your saved working setup.

If you inspect `FenrisDebug.txt` in the Diablo IV installation folder, check its
timestamp first. “Initializing graphics subsystem” is only the start of that step;
it does not prove successful rendering. Likewise, a high CPU reading does not
identify why startup is slow. Avoid repeatedly starting another copy while the
first is still running.

## A note about login code 1910

In our test it occurred during a direct game start without Battle.net SSO. Starting
through the working launcher resolved the login. That observation does not prove
that every occurrence of 1910 has the same cause. If it persists with a normal
signed-in launch, investigate authentication or service availability separately.

## Asking for help

Include your Mac/chip, macOS version, Wine engine version, Battle.net/game build,
how you launch the game, and which step fails. State whether this setup worked
before. Share a short, relevant error excerpt after removing account details,
credentials, tokens, and private paths; a full prefix or log archive is not needed.

The optional [assistant prompts](../AGENT-PROMPT.md) help keep deeper investigation
focused on evidence instead of accumulating unrelated switches.
