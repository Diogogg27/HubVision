# Run doc — PromptHub landing page (static site)

Static HTML/CSS/JS site. No `package.json`, no build step, no dependencies to install.

## Reproduce uncommitted artifacts

None. There is no `.env.local` or any other generated/secret file; the site works
straight from the checkout. All assets (css, js, images, icons, fonts) are committed
in the repo.

## Run the server

Serve the project root with Python's built-in static server (Python 3.14 is
installed at `C:\Python314\python.exe`):

```bash
cd P:\LandingPage-PromptHub
python -m http.server 5173 --bind 127.0.0.1
```

Then open http://127.0.0.1:5173/.

Detached (PowerShell) form used by previews — stdout and stderr must go to
DIFFERENT files:

```powershell
(Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList '-m','http.server','5173','--bind','127.0.0.1' -WorkingDirectory 'P:\LandingPage-PromptHub' -RedirectStandardOutput 'P:\LandingPage-PromptHub\.freebuff\preview.log' -RedirectStandardError 'P:\LandingPage-PromptHub\.freebuff\preview.log.err' -WindowStyle Hidden -PassThru).Id
```

Note: the thread's HTML-file preview (`register_preview` with `htmlPath`) is NOT
sufficient for this project — it serves only `index.html` and 404s every sibling
asset (css/js/images). Always use the directory-rooted static server instead.
