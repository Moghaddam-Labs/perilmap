# PerilMap

PerilMap shows how exposed the area around a home is to climate-related perils, before the insurance
quote arrives. Find your postcode, mark your home on the map, and get clear risk bands and
plain-English explanations.

> **Status: planning.** There's no app yet. This repo currently holds a data test, which checks that
> London's flood data can be stored in small grid files and searched quickly and accurately.

**Guidance only.** Results will not be an insurance quote, survey or financial advice. They describe
risk to an area of land, not whether a particular property will flood.

## Planned scope

- **England first, starting with London.** Each region is a plug-in, so the core never hard-codes one.
- **Flooding:** rivers and sea, and surface water, with the distance to the nearest zone in each band.
- **Subsidence:** a rough area indicator from free geology data.
- **Heat:** temperature exposure across London.

Groundwater and reservoir flooding won't be covered at launch, and the app will say so plainly.

## Run the data test

You'll need Python 3.11 or newer. The test doesn't use a database or need any credentials.

**1. Set up**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
```

**2. Download the data**

Download Greater London from each dataset as an ESRI Geodatabase, and unzip it into a `data/` folder.
Git ignores this folder. Surface water is too large to download in one go, so draw a few areas.
They can overlap.

- [Risk of Flooding from Rivers and Sea](https://environment.data.gov.uk/explore/96ab4342-82c1-4095-87f1-0082e8d84ef1?download=true), layer `rofrs_4band`
- [Risk of Flooding from Surface Water](https://environment.data.gov.uk/explore/b5aaa28d-6eb9-460e-8d6f-43caa71fbe0e?download=true), layer `rofsw`

**3. Build the grid files and measure them**

Replace the paths with your own. List every download for a dataset in the same command.

```bash
python -m data_test inspect data/*.gdb
python -m data_test build rivers_and_sea data/rofrs_4band.gdb
python -m data_test build surface_water data/rofsw_1.gdb data/rofsw_2.gdb
python -m data_test measure
```

The grid files go in `grids/`, and the report goes in `reports/flood-data-test.md`. Each build prints
a coverage map, so you can spot any part of London that was missed.

## Run the tests

```bash
ruff check .
ruff format --check .
pytest
```

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
