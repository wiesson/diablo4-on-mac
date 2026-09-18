# Set up Battle.net and launch Diablo IV

[Back to the guide](../README.md)

The goal is simple: open Battle.net, sign in, click **Play**, and reach Diablo IV
with your account already connected.

## Before you start

You need an Apple Silicon Mac with Rosetta, a Battle.net account with Diablo IV,
and a Wine wrapper that supports the components below. A **wrapper** is the Mac app
that starts Wine. Its **prefix** (sometimes called a bottle) is the folder containing
the Windows installation and settings. Its **engine** is the Wine runtime itself.

Already have Battle.net and Diablo installed? Keep that download. Back up the
wrapper's configuration and prefix before changing the engine; use a separate
prefix for experiments. A running download or game is not the time to replace DLLs.

Starting from scratch? This guide documents a manually assembled, working setup.
It does not yet provide a tested clean-install procedure or assemble the runtime
for you. Obtain the runtime components from their publishers, then use your wrapper's
installation workflow. The versions below are our tested reference, not a claim
that any Wine 11 download or any Apple Silicon Mac will behave identically.

## The tested setup

| Part | Working reference |
|---|---|
| Mac | M3 Max, 40-core GPU, 48 GB memory |
| macOS | 27.0, build 26A428; Rosetta enabled |
| Wine | Complete GameToMac 0.1.13 Alpha, build 47 engine; based on CodeWeavers Wine 11 / CrossOver 26.3 sources |
| Diablo compatibility overlay | The **matching** Diablo4 engine overlay from that same bundle |
| Shared runtime dependencies | Frameworks from Sikarugir wrapper template 1.0.17 |
| Game graphics | Apple D3DMetal; `libd3dshared.dylib`, D3D11/D3D12/DXGI updated from GPTK 4.0 beta 2; template `atidxx64` retained |
| Launcher graphics | 32-bit DXMT v0.80 DLLs and matching Unix bridge from the GameToMac Overwatch overlay |
| Windows profile | Windows 10 |
| Verified apps | Battle.net 17778; Diablo IV 3.2.1.73552 |

GameToMac supplied the engine components; its GUI was not used to launch this
Battle.net installation. The retail CrossOver application was not used either.

The original Sikarugir Wine 11 engine could run Battle.net, but did not pass our
D3D12 device test. Replacing only its `ntdll.so` with the GameToMac file is **not**
the working recipe: the loader, Wine server, Windows DLLs, and Unix libraries must
be a matching set. Likewise, a newer DXMT build from a different wrapper is not
necessarily compatible with this engine's window driver.

## Configure the launcher

Find your wrapper's **environment variables** or **launch configuration**. The
exact UI depends on the wrapper. Save the following settings for the process that
starts Battle.net, so the game it launches inherits them:

| Setting | Value used | Purpose |
|---|---|---|
| `WINE_SIMULATE_WRITECOPY` | `1` | Fixes the diagnosed Battle.net login-window crash in this engine |
| `WINEMSYNC` | `1` | Enables the engine's MSync synchronization path |
| `WINEESYNC` | `0` | Keeps ESync disabled in this profile |
| `ROSETTA_ADVERTISE_AVX` | `1` | Advertises AVX support to the Windows application |
| `D3DM_ENABLE_METALFX` | `0` | Leaves this renderer option disabled in the tested baseline |
| `DXMT_ALLOW_CROSS_PROCESS_SWAPCHAIN` | `1` | Preserves the setting used with the matching launcher renderer |
| `MTL_HUD_ENABLED` | `0` | Keeps the Metal diagnostics overlay off for normal play |
| `WINEDEBUG` | `-all` | Disables verbose Wine logging during normal play |

These are the settings of a successful configuration, not individually measured
performance improvements. In particular, the write-copy switch is available in
the tested CrossOver-derived engine; setting it in an unrelated build may do nothing.

Our Battle.net launch argument was:

```text
--in-process-gpu
```

Keep this in **Battle.net's** launch arguments, not Diablo IV's additional arguments.
It was part of the working graphics configuration. It did not, by itself, fix the
write-copy crash. Disabling the browser GPU or adding `--no-sandbox` did not fix
that crash either.

### For a custom wrapper

The paths below illustrate our launch recipe with portable example directory names.
**They must point to an already assembled engine, renderer, dependencies, and prefix.**
Copying this command alone does not install or connect those components.

```sh
d4_engine="$HOME/Games/DiabloRuntime/Engine"
d4_prefix="$HOME/Games/DiabloRuntime/Prefix"
d4_frameworks="$HOME/Games/DiabloRuntime/Frameworks"
d4_renderer="$d4_frameworks/renderer/d3dmetal"

env \
  WINEPREFIX="$d4_prefix" \
  WINESERVER="$d4_engine/bin/wineserver" \
  WINELOADER="$d4_engine/bin/wine" \
  WINEDLLPATH="$d4_renderer/wine:$d4_engine/lib/wine" \
  DYLD_FALLBACK_LIBRARY_PATH="$d4_frameworks:$d4_frameworks/GStreamer.framework/Versions/1.0/lib:/usr/lib" \
  CX_APPLEGPTK_LIBD3DSHARED_PATH="$d4_renderer/external/libd3dshared.dylib" \
  WINE_SIMULATE_WRITECOPY=1 \
  WINEMSYNC=1 WINEESYNC=0 ROSETTA_ADVERTISE_AVX=1 \
  D3DM_ENABLE_METALFX=0 DXMT_ALLOW_CROSS_PROCESS_SWAPCHAIN=1 \
  MTL_HUD_ENABLED=0 WINEDEBUG=-all \
  WINEDLLOVERRIDES='winemenubuilder.exe=;mscoree,mshtml=;dxgi,d3d11,d3d12,atidxx64=n,b;nvapi64,nvngx=' \
  "$d4_engine/bin/wine" \
  'C:\Program Files (x86)\Battle.net\Battle.net.exe' --in-process-gpu
```

Use a clean launch environment; earlier `WINE*`, `CX_*`, `DYLD_*`, or experimental
renderer settings can otherwise survive from your shell. Our local launcher clears
those inherited settings before supplying its profile. The example explicitly sets
the main values but does not clear unrelated variables for you.

The assembled layout also matters:

- Apple 64-bit `d3d11.dll`, `d3d12.dll`, `dxgi.dll`, and `atidxx64.dll` are available
  in the prefix's `drive_c/windows/system32` and via the engine's 64-bit DLL paths.
- The corresponding Unix bridges (`d3d11.so`, `d3d12.so`, `dxgi.so`, `atidxx64.so`)
  resolve to the selected Apple `libd3dshared.dylib`.
- The 32-bit DXMT DLLs (`d3d11`, `dxgi`, `d3d10core`, `winemetal`) and their matching
  `winemetal.so` bridge serve Battle.net. Keep them distinct from the 64-bit game path.
- Engine dependency links and loader paths must resolve on **your** Mac. A copied
  engine with links into somebody else's home folder is not portable.

These packaging details are why a D3DMetal checkbox alone was insufficient in our
original wrapper. Preserve a working engine bundle rather than replacing libraries
one at a time in your everyday installation.

## Sign in and start the game

1. Connect your headphones, if you use them, and select the output in macOS.
2. Open **Battle.net through the configured wrapper** and sign in normally.
3. Install Diablo IV, or use Battle.net's option to locate an existing installation
   accessible from that prefix. Let Battle.net complete any update it requests.
4. Click **Play** in that same Battle.net window.
5. Confirm that you reach character selection and can enter the game with sound.

Use this same saved shortcut next time. If you kept an old wrapper for comparison,
its Play button will still launch its old engine and prefix.

Keep Battle.net as the normal entry point. Our standalone `Diablo IV.exe` test
rendered successfully but failed login with code 1910. A normal Battle.net launch
subsequently passed SSO authentication and entered the game.

Once this works, continue with [graphics and audio settings](settings.md).
