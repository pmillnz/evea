# evea

EVEA is a simple command line tool to find market order arbitrage in the online game, EVE.
It utilises the EVE Swagger Interface (ESI) to download market orders and supporting metadata, which is stored on the user's file system in the following directories:

* ./data/
  * --> ./data/orders/
  * --> ./data/routes/
  * --> ./data/regions/
  * --> ./data/systems/
  * --> ./data/types/
* ./output/

EVEA accepts some basic parameters via command line arguments and then attempts to find arbitrage "opportunities" that meet those parameters in the set of downloaded market orders.

## Pre-requisites:
- virtualenv
- json
- requests
- pandas
- argparse

## Set up:
- `cd /your/chosen/directory/`
- `git clone https://github.com/PeteMillsNZ/evea.git`
- `cd evea`
- `virtualenv evea`
- `pip install json`
- `pip install requests`
- `pip install pandas`
- `pip install argparse`

## Usage:

`python.py get_pure_arbitrage.py --args`

### Optional arguments:
* `-h, --help`:
  * show this help message and exit
* `--min_margin`
  * Limits results to those where the buy/sell margin is > value
* `--max_item_purchase_price`
  * Limits results to those where each item can be purchased for < value
* `--min_potential_revenue`
  * Limits results to opportunities where the total potential revenue from thr arbitrage is > value
* `--min_system_sec_rating`
  * Limits results to those where both the buy and sell systems have security statuses >= value
* `--single_cargo`
  * Default True. If True, requires cargo_capacity param to be > 0. If True, limits results to those where >= min_potential_revenue can be made from one cargo hold of the given item in the opportunity
* `--cargo_capacity`
  * The cargo capacity to limit each opportunity to
* `--get_routes`
  * WARNING: Can vastly increase run time. Routes will be saved however. First run time might be slow. If True, finds the route between the buy/sell system and adds the # of jumps to the results
* `--get_new_orders`
  * If True, downloads new orders and saves them to the filesystem prior to finding arbitrage opportunities. Can take ~1h
* `--get_new_lookups`
  * If True, downloads new region/system/item names. Only set to True if you know new systems/regions/item names may have been added to the game. Rare.
* `--safe_regions`
  * Default True. Used in conjunction with get_new_orders. If True, only downloads results from regions in Cal/Gal/Min/Amarr space. See code for list.

## Caveats/Gotchas:
- You'll need to be connected to the internet!
- `safe_regions=True` limits it to only look at the following regions:
  "The Forge",
  "Lonetrek",
  "Black Rise",
  "The Citidel",
  "Placid",
  "Essence",
  "Verge Vendor",
  "Solitude",
  "Everyshore",
  "Sinq Laison",
  "Aridia",
  "Kor-Azor",
  "Khanid",
  "Tash-Murkon",
  "Domain",
  "Devoid",
  "The Bleak Lands",
  "Derelik",
  "Heimatar",
  "Molden Heath"
  "Metropolis"
- Each order download takes between 45 mins `--safe_regions=True` and 60 mins `--safe_regions=False`. Note: this means results will be 45-60 mins behind real-time. I've lost a couple items to that so it's worth checking EVEA still reflects the reality ingame.
- After downloading orders, you can run with `--get_new_orders=False` to quickly iterate with different parameters and find different arbitrage opportunities without re-downloading the orders
- EVEA tries to save what it can after downloading things to save re-downloading them in future (unless you force it to with `--get_new_orders=True` or `--get_new_lookups=True`. After finding an arbitrage opportunity, the program tries to find further info about the item involved (primarily the packaged volume) and the route between the two systems. If your params return thousands of items and thousands of routes, this can take a long time. It'll save the item details and route info for future though, and won't re-download them.
- You can stop it from finding the route info if you don't care about it with `--get_routes=False`
- It finds routes optimising for safety, not speed

## Quickstart

Here's a decent parameter set to start with:

`python get_pure_arbitrage.py --min_margin 30 --min_potential_revenue 5000000  --max_item_purchase_price 20000000 --min_system_sec_rating 0.5  --single_cargo=True --cargo_capacity 6000 --safe_regions=False --get_new_orders=True --get_routes=True`

Remember to set `--get_new_orders=False` if you want to iterate on different parameters without re-downloading orders.

The results will be written to a csv in `evea/output/pure_arbitrage.csv`. You'll want to open that in Excel or Libre or something to slice and dice the opportunities.
