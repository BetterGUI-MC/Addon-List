# Addon-List
This repo contains details of all BetterGUI addons. Mainly used by the addon downloader

# Format
```json
{
  "<addon-name>": {
    "file-name": "<filename>",
    "version": "<version>",
    "description": "<description>",
    "authors": [
      "author1",
      "author2",
      "..."
    ],
    "source-code": "<src-repo-link>",
    "direct-link": "<direct-download-link>",
    "wiki": "<wiki-link>"
  }
}
```

# Example
```json
{
  "ASCII-Placeholders": {
    "file-name": "ASCII-Placeholders.jar",
    "version": "1.1",
    "description": "Add complex texts as placeholders",
    "authors": ["HSGamer"],
    "source-code": "https://github.com/BetterGUI-MC/ASCII-Placeholders/",
    "direct-link": "https://ci.codemc.io/view/Author/job/BetterGUI-MC/view/Addon/job/ASCII-Placeholders/lastSuccessfulBuild/artifact/target/ASCII-Placeholders.jar",
    "wiki": "https://github.com/BetterGUI-MC/ASCII-Placeholders/blob/master/src/main/resources/config.yml"
  }
}
```