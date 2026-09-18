# Diablo IV on Apple Silicon

A practical guide to getting **Diablo IV through Battle.net** running smoothly on
your Mac — from a working launcher to your first game, graphics settings, and sound.

This started with an evening of getting Diablo IV running on an M3 Max. Battle.net
would open with one Wine setup, while the game would run with another. We eventually
got both working together, including account login, gameplay, and Bluetooth audio.
These are the settings and lessons worth sharing.

**Verified on September 17, 2026:** M3 Max (40-core GPU, 48 GB memory), macOS 27.0,
Battle.net build 17778, Diablo IV 3.2.1.73552. Gameplay felt very smooth; we have not
recorded a benchmark or tested other Macs.

## Start here

1. **[Set up Battle.net and launch Diablo IV](docs/setup.md)** — what you need,
   the working configuration, and how to check that both apps use it.
2. **[Find comfortable graphics and audio settings](docs/settings.md)** — start
   with a stable baseline, then tune for your display.
3. **[Fix a problem](docs/troubleshooting.md)** — launcher crashes, “Playing Now”
   without a game window, login errors, or missing headphone audio.

You will need your own Diablo IV license and a Wine wrapper with compatible graphics
components. This repository is a configuration guide, not a game download or an
automatic installer. The [tested components](docs/setup.md#the-tested-setup)
are documented so you can compare your setup before changing it.

## The setting that got our launcher working

In our CrossOver-derived Wine build, Battle.net's login window needed this
environment variable:

```sh
WINE_SIMULATE_WRITECOPY=1
```

Add it to the configuration that **launches Battle.net**. It is a Wine setting, not
a Diablo IV command-line argument. It fixes the particular launcher crash we
diagnosed; the game still needs a compatible Wine engine and D3DMetal setup.
The [setup guide](docs/setup.md#configure-the-launcher) explains where it belongs.

## A few things that made the difference

- Launch the game through the configured **Battle.net**, so it receives your login.
- Use **D3DMetal for Diablo IV** and a matching **32-bit DXMT for Battle.net**.
- Keep the working Wine engine and its matching components together.
- Connect Bluetooth headphones **before starting the game**.
- Get into the game first; adjust graphics one setting at a time afterward.

## Interested in the Wine fix?

The launcher bug that led to this guide involved how Wine reports memory protection.
You do not need to understand that detail to follow the guide.

The [technical write-up](docs/technical-notes.md) preserves the diagnosis and
verification. The small utilities in [`tools/`](tools/) and the optional
[troubleshooting prompts](AGENT-PROMPT.md) are for deeper investigation.

Documentation and included tools: [MIT license](LICENSE). Wine, Apple graphics
components, Battle.net, and Diablo IV are separate projects with their own licenses;
their binaries and account data are not included here.
