# Economics job openings map

Builds `index.html`, an interactive world map (Equal Earth projection) of every posting
in an AEA Job Openings for Economists (JOE) export. Blue dots are academic jobs and orange
dots are industry/nonacademic jobs. Clicking a dot lists that city's postings, each linked
to its JOE listing.

## Updating the map

1. On JOE, go to **Listings → Download Options → XML** and save the file as
   `joe_full_xml.xml` in this folder (replace the old one).
2. Run:

   ```
   python3 build_map.py
   ```

3. Upload the new `index.html` to your website.

The "Updated through" date in the footer is the date the XML file was saved.
Requires Python 3.8+ and nothing else; no packages to install.

## What's in this folder

| File | Purpose |
|---|---|
| `build_map.py` | Reads the JOE XML and writes `index.html` |
| `template.html` | The page design (HTML/CSS/JS); the build script fills in the data |
| `geocode.py` | Turns JOE city/state/country text into map coordinates |
| `geo/cities15000.zip` | GeoNames world cities list used for coordinates (CC BY 4.0, geonames.org) |
| `geo/places.json` | Saved coordinates, so only new cities are looked up |
| `geo/overrides.json` | Hand-entered coordinates for places GeoNames can't match |
| `joe_full_xml.xml` | The JOE export the current map was built from |
| `index.html` | The finished map, the only file the website needs |

## Cities that can't be placed

New cities are matched automatically. To see any that couldn't be, run

```
python3 geocode.py
```

and add each one to `geo/overrides.json` in the same format as the existing entries, e.g.

```
"Hanover|New Hampshire|UNITED STATES": [43.702, -72.290]
```

An optional third value sets the label shown on the map. Postings that list no location,
or are fully remote, aren't shown.

## Publishing

Only `index.html` needs to go on the website, and it can be renamed. If your site publishes
everything in its folder (for example GitHub Pages), keep this folder outside the published
directory, or exclude everything except `index.html`, so the scripts, the JOE export and the
3 MB city list aren't served.

When opened, the page loads D3 and the country and US-state outlines from cdn.jsdelivr.net,
so viewers need an internet connection.
