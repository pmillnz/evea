import json
import requests
import csv
import pandas as pd
import sys
import utils as u
import argparse
import pure_arbitrage as pa

def get_best_item_price(item_name, side="Buy", quantity=1, safe_regions=True, get_new_orders=True):

    if side == "Buy":
        is_buy_order = True
    elif side == "Sell":
        is_buy_order = False
    else:
        print "Unrecognised side. Please select 'Buy' or 'Sell'"
        return

    if get_new_orders:
        pa.get_and_save_orders(force=True, force_lookups=False, safe_regions=safe_regions)
        df = pd.read_csv("./data/orders/orders.csv", quotechar="|")
    else:
        try:
            print "Loading orders CSV... This might take a minute"
            df = pd.read_csv("./data/orders/orders.csv", quotechar="|")
        except IOError:
            print("No order data saved, but 'get_new_orders' parameter was set to False. Downloading anyway")
            pa.get_and_save_orders(force=True, force_lookups=False, safe_regions=safe_regions)
            df = pd.read_csv("./data/orders/orders.csv", quotechar="|")

    print "Getting best " + side + " price for " + item_name

    if safe_regions:
        df = df[df["region_name"].isin(pa.SAFE_REGIONS)]

    orders = df[
        (df["type_name"] == item_name) &
        (df["is_buy_order"] == is_buy_order) &
        (df["volume_remain"] >= quantity)
    ]

    if orders.empty:
        print "No orders matching that item name, side and quantity combination"
        return

    if side == "Buy":
        print orders.ix[orders["price"].idxmax()]
    else:
        print orders.ix[orders["price"].idxmin()]

    return

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--item_name', type=str, help='Item name')
    parser.add_argument('--side', default="Buy", type=str, help='"Buy" or "Sell"')
    parser.add_argument('--quantity', default=1, type=int, help='Amount that needs to be available to consider the price')
    parser.add_argument('--get_new_orders', type=u.str2bool, nargs="?", const=False, default=False, help='If True, downloads new orders and saves them to the filesystem prior to finding arbitrage opportunities. Can take ~1h')
    parser.add_argument('--safe_regions', type=u.str2bool, nargs="?", const=True, default=True, help='Default True. Used in conjunction with get_new_orders. If True, only downloads results from regions in Cal/Gal/Min/Amarr space. See code for list.')
    args = parser.parse_args()

    get_best_item_price(item_name=args.item_name, side=args.side, quantity=args.quantity, get_new_orders=args.get_new_orders, safe_regions=args.safe_regions)
