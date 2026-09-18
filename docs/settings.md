# Smooth gameplay and working audio

[Back to the guide](../README.md)

First reach the game with the [working launch configuration](setup.md). Then tune
for your Mac and display. We have one successful M3 Max setup, not a universal
“best settings” preset.

## Start with a comfortable baseline

| Setting | Starting point |
|---|---|
| Resolution | Choose one suitable for your display; lower it first if performance is poor |
| Ray tracing | Off, as in the successful setup |
| Frame-rate limit | Choose a target you can hold consistently, rather than chasing the highest number |
| VSync | Enabled in the saved working profile; compare off only if you want to test its effect |
| Texture quality | Adjust for your Mac's available memory; reduce it if you see memory pressure or stutter |
| Upscaling / frame generation | Leave these alone for the first successful run, then test supported options individually |

These are starting points for comparison. We have not benchmarked which preset or
upscaler is fastest. The launch profile disables the renderer's MetalFX option and
NVIDIA DLL paths; an option appearing in Diablo's menu does not by itself prove
that it is active or supported through this renderer.

### What our saved profile actually shows

After the successful session, the local preferences recorded **3440 × 1440**,
**VSync on**, a **150 FPS foreground cap**, and **ray tracing off**. A frame-rate
cap is a limit, not a measurement of achieved performance. These values are a
reference for that display, not requirements for your Mac.

The player described gameplay as feeling like 120 FPS. No FPS capture, frame-time
trace, or timed benchmark was taken, and we cannot tie that impression to a
controlled graphics preset. The verified result is successful, subjectively smooth
gameplay on the hardware listed in the README.

## Tune one thing at a time

1. Pick a repeatable area or fight and note your resolution, preset, and frame cap.
2. Measure actual FPS and frame pacing with an available game counter or, if it
   works with your renderer, the Metal HUD (`MTL_HUD_ENABLED=1` at launch).
3. Change one setting, repeat the same scene, and compare smoothness as well as FPS.
4. Save the combination you prefer and disable diagnostic logging/overlays afterward.

Do not change Wine engines, swap graphics libraries, and alter game quality at the
same time: you would lose the useful comparison with a working setup.

## Bluetooth headphones: connect before launch

This was the only remaining issue after we could play. macOS had switched to Beats
Studio Pro, but Diablo's output list still showed only the monitor and MacBook
speakers. Selecting “Default” did not make the headphones appear.

What worked:

1. Keep the headphones connected and select them as the output in macOS.
2. Exit **Diablo IV normally**, leaving Battle.net open.
3. Click **Play** again. In our test, headphone audio then worked.

If your device is already listed, first try selecting it explicitly under
**Options → Sound → Sound Output Device** and applying the change.

Diablo also has a **Play in Background** option. Our saved profile has it off, so
silence when switching away from the game is a separate thing to check. Turn it on
if you want audio while another app is in front.

## Keep the working setup easy to return to

Save your launcher configuration and component versions. Before an engine or renderer
upgrade, keep a backup of the working prefix and runtime. Do not delete an older
wrapper if your new launcher still uses its Frameworks directory or other files.

There is no need to revisit the Wine crash analysis while the game is working.
If something changes, start with [the symptom guide](troubleshooting.md).
