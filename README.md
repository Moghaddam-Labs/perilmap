# PerilMap

PerilMap shows how exposed the area around a home is to climate-related perils, before the insurance
quote arrives. Find your postcode, mark your home on the map, and get clear risk bands and
plain-English explanations.

> **Status: planning.** There's no app yet. This repo currently holds a data test, which checks that
> London's flood data fits the free database and can be searched quickly enough.

**Guidance only.** Results will not be an insurance quote, survey or financial advice. They describe
risk to an area of land, not whether a particular property will flood.

## Planned scope

- **England first, starting with London.** Each region is a plug-in, so the core never hard-codes one.
- **Flooding:** rivers and sea, and surface water, with the distance to the nearest zone in each band.
- **Subsidence:** a rough area indicator from free geology data.
- **Heat:** temperature exposure across London.

Groundwater and reservoir flooding won't be covered at launch, and the app will say so plainly.

## Run the data test

You'll need Python 3.11 or newer, and a Supabase project with PostGIS enabled.

**1. Set up**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
```

Add your Supabase connection string to `.env`. Git ignores this file.

**2. Download the data**

Download the area around Greater London from each dataset, in British National Grid, and put the
unzipped files in a `data/` folder. Git ignores this folder too.

- [Risk of Flooding from Rivers and Sea](https://environment.data.gov.uk/explore/96ab4342-82c1-4095-87f1-0082e8d84ef1?download=true)
- [Risk of Flooding from Surface Water](https://environment.data.gov.uk/explore/b5aaa28d-6eb9-460e-8d6f-43caa71fbe0e?download=true)

**3. Check the files and estimate the size**

These commands don't touch the database. Replace the paths with your own.

```bash
python -m data_test inspect data/RoFRS.gdb data/RoFSW.gdb
python -m data_test estimate rivers_and_sea data/RoFRS.gdb
python -m data_test estimate surface_water data/RoFSW.gdb
```

If the raw size is close to 400 MB or above, compare it with a simplified version by adding
`--simplify-metres 2`.

**4. Load and measure**

```bash
python -m data_test load rivers_and_sea data/RoFRS.gdb
python -m data_test load surface_water data/RoFSW.gdb
python -m data_test measure
```

Loading stops if the database reaches 400 MB. The report is saved to `reports/flood-data-test.md`.

**5. Start again if needed**

```bash
python -m data_test reset --yes
```

## Run the tests

```bash
export TEST_DATABASE_URL=postgresql://postgres:test@localhost:5432/perilmap_test
ruff check .
ruff format --check .
pytest
```

Without `TEST_DATABASE_URL`, the database tests are skipped. CI always runs them against PostGIS.

## Data sources

| Source | Publisher | Licence |
|---|---|---|
| [Risk of Flooding from Rivers and Sea](https://www.data.gov.uk/dataset/943d2bbb-aa08-45d1-96cb-42556cd01d94/risk-of-flooding-from-rivers-and-sea2) | Environment Agency | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) |
| [Risk of Flooding from Surface Water](https://www.data.gov.uk/dataset/risk-of-flooding-from-surface-water3) | Environment Agency | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) |

© Environment Agency copyright and/or database right 2025. All rights reserved.

## Licence

Proprietary. The source is public to view, but no rights are granted to copy, change or use it. See
[LICENSE](LICENSE).

---

Created by **Shaz Moghaddam** · London
[Website](https://shazmoghaddam.github.io/) · [LinkedIn](https://www.linkedin.com/in/shazmoghaddam/)
