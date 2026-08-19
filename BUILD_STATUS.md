# ClipCatcher Build Status

## Current State

- Repository: `ThankyouJerry/ClipCatcher`
- Default branch: `main`
- Current app version: `2.0.10`
- Latest published release: `v2.0.10`
- GitHub Pages: `https://thankyoujerry.github.io/ClipCatcher/`

## Build Outputs

- Windows release asset: `ClipCatcher-Windows.zip`
- macOS release asset: `ClipCatcher-macOS.zip`

## Automation

- Windows builds are handled by GitHub Actions when a `v*` tag is pushed.
- macOS builds are produced locally with `./build_macos.sh` and uploaded to the GitHub Release.
- The packaged app smoke check uses:

```bash
python src/main.py --smoke
```

## Next Release Checklist

1. Confirm local source checks pass.
2. Build or attach macOS asset.
3. Push a new tag, for example `v2.0.11`.
4. Confirm the Windows GitHub Actions build succeeds.
5. Upload or replace the macOS asset on the release.
6. Confirm README and GitHub Pages still point to the latest release page.
