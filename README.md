# Addon-List

This repo contains details of all BetterGUI addons. Mainly used by the addon downloader

# Format

```json
{
  "name": "<addon-name>",
  "version": "<version>",
  "description": "<description>",
  "author": [
    "author1",
    "author2",
    "..."
  ],
  "code": "<src-repo-link>",
  "download": "<direct-download-link>",
  "wiki": "<wiki-link>"
}
```

# Example

```json
{
  "name": "AdvancedCooldown",
  "version": "4.0",
  "description": "Cooldown with storage",
  "author": [
    "HSGamer"
  ],
  "code": "https://github.com/BetterGUI-MC/AdvancedCooldown/",
  "download": "https://ci.codemc.io/job/BetterGUI-MC/view/Addon/job/AdvancedCooldown/85/artifact/target/AdvancedCooldown-4.0.jar",
  "wiki": "https://bettergui-mc.github.io/Docs/addon/advanced-cooldown/index.html"
}
```