# Carbondale ET Dashboard

Automatically tracks daily evapotranspiration (ETo) and precipitation from the
CoAgMET weather station at Carbondale, CO (CBL01), and shows it on a
multi-year comparison dashboard. Built for irrigation scheduling decisions.

## How it works

- `scripts/scrape_et.py` fetches the daily data table from
  coagmet.colostate.edu and saves it to `data/et_data.json`.
- `.github/workflows/update-et-data.yml` runs that script automatically once
  a day and commits any new data.
- `index.html` is a static dashboard (hosted via GitHub Pages) that reads
  `data/et_data.json` and renders the current-conditions summary plus a
  multi-year comparison chart with zoom/year-toggle controls.

Once set up, this runs itself. You don't need to do anything day to day.

## One-time setup

1. **Create the repo.** Push everything in this folder to a new GitHub repo
   (public — GitHub Pages on a free plan requires a public repo).

   ```bash
   cd coagmet-et-dashboard
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

2. **Allow the workflow to push commits.** In the repo on GitHub:
   `Settings → Actions → General → Workflow permissions` → select
   **Read and write permissions** → Save.

3. **Run the first backfill manually.** Go to the **Actions** tab →
   **Update ET data** → **Run workflow**. This does a one-time pull of the
   full history (2020-01-01 through today) and creates `data/et_data.json`.
   It may take a minute or two since it's pulling several years of data.

4. **Turn on GitHub Pages.** `Settings → Pages` → Source: **Deploy from a
   branch** → Branch: `main`, folder: `/ (root)` → Save. GitHub will give you
   a URL like `https://<your-username>.github.io/<repo-name>/`.

5. **Bookmark that URL.** From now on, the page always shows current data —
   the Action re-runs every day (around 6-7am Mountain Time, see the cron
   schedule in the workflow file if you want to change it) and commits
   whatever's new, which GitHub Pages then serves automatically.

## Checking that it's working

- **Actions tab** shows a green check after each run, with a short summary
  in the logs (how many new/corrected days were found).
- If a run fails, the most likely cause is the source site changing its page
  structure. Open the Action's log to see the error, and check
  `coagmet.colostate.edu/table/daily/cbl01` manually to compare against what
  `scrape_et.py` expects (see `COLUMNS` near the top of the script).

## Local testing (optional)

```bash
pip install -r requirements.txt
python scripts/scrape_et.py
```

This will create/update `data/et_data.json` locally, which you can open
`index.html` against directly (or just push and let Pages serve it).

## Notes

- The scraper re-fetches the last 30 days on every run (not just "today"),
  since the station sometimes backfills or corrects recent readings.
- If you ever want a second station, duplicate the `STATION` constant logic
  in `scrape_et.py` and give it its own data file / chart series.
