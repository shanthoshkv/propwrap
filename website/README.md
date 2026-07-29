# propwrap project website

Official live page: **[https://aboutkvs.vercel.app/propwrap.html](https://aboutkvs.vercel.app/propwrap.html)**

This folder holds the same single-file site for the repo / local preview:

| File | Role |
|------|------|
| `index.html` | Default local / GitHub Pages entry |
| `propwrap.html` | Same content (matches Vercel path name) |

Visual language matches [Oberth Forge](https://aboutkvs.vercel.app/oberth_forge.html): Bebas Neue + Syne + JetBrains Mono, void/fire/ice palette.

## Preview

```bash
# from repository root
python -m http.server 8080 --directory website
```

Open **http://localhost:8080** or **http://localhost:8080/propwrap.html**.

## GitHub Pages (optional)

Repo → Settings → Pages → deploy from branch → `/website`.
