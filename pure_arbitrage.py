import json
import requests
import csv
import pandas as pd
import sys
import utils as u
import argparse

SAFE_REGIONS = [
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
]


def get_name_lookup(type, paged=False, force=False):

    print("\nGetting " + type + " ids")
    url = "https://esi.evetech.net/latest/universe/" + type + "/?datasource=tranquility"
    ids = u.get_data(
        url=url,
        fileloc="./data/" + type + "/" + type + ".json",
        paged=paged,
        force=force
    )

    print("\nGetting " + type + " names")
    url = "https://esi.evetech.net/latest/universe/names/?datasource=tranquility"
    names = u.get_data(
        url=url,
        fileloc="./data/" + type + "/" + type + "_names.json",
        request_type="post",
        post_data=ids,
        post_in_batches=True,
        batch_size=1000,
        force=force
    )

    names_by_ids = {}
    for n in names:
        names_by_ids[str(n["id"])] = n["name"].replace(",", "-").replace("/", "-")

    return names_by_ids


def get_name_lookups(force=False):
    print("\n------------- Getting lookups -------------")
    region_name_by_region = get_name_lookup("regions", force=force)
    system_name_by_system = get_name_lookup("systems", force=force)
    type_name_by_type = get_name_lookup("types", force=force, paged=True)
    print("")
    return {
        "regions": region_name_by_region,
        "systems": system_name_by_system,
        "types": type_name_by_type
    }


def get_and_save_orders(force=False, force_lookups=False, safe_regions=True):

    lookups = get_name_lookups(force_lookups)
    region_name_by_region = lookups["regions"]
    system_name_by_system = lookups["systems"]
    type_name_by_type = lookups["types"]

    print("\n------------- Getting Orders -------------\n")
    orders = []
    num_regions = len(region_name_by_region.keys())
    for i, region in enumerate(region_name_by_region.keys()):
        if safe_regions and region_name_by_region[region] not in SAFE_REGIONS:
            continue
        u.overwrite_print("---> Working on region: " + region_name_by_region[region] + ". " + str(i + 1) + "/" + str(num_regions))
        url = "https://esi.evetech.net/latest/markets/" + region + "/orders/?datasource=tranquility&order_type=all"
        orders_for_region = u.get_data(
            url=url,
            fileloc="./data/orders/" + region_name_by_region[region] + ".json",
            force=force,
            paged=True
        )
        orders_for_region[:] = [o for o in orders_for_region if o != u'error']
        for j, order in enumerate(orders_for_region):
            orders_for_region[j]["region"] = region
            orders_for_region[j]["region_name"] = region_name_by_region[region]
            orders_for_region[j]["system_name"] = system_name_by_system[str(orders_for_region[j]["system_id"])]
            orders_for_region[j]["type_name"] = type_name_by_type[str(orders_for_region[j]["type_id"])]

        orders += orders_for_region

    # Encode everything to ensure we can write to csv
    print("\nEncoding to utf-8")
    for i, order in enumerate(orders):
        orders[i] = {k: unicode(v).encode("utf-8") for k,v in orders[i].iteritems()}

    u.write_to_csv(
        [
            "region","region_name","duration","is_buy_order","issued","location_id",
            "min_volume","order_id","price","range","system_id","system_name",
            "type_id","type_name","volume_remain","volume_total"
        ],
        orders,
        "./data/orders/orders.csv",
        d=True
    )

    return


def get_type_details(type_name_by_type, type_ids):

    num_types = len(type_ids)
    print("\n\nWarning! Getting details for " + str(num_types) + " items.")
    print("This could take roughly: " + str(num_types*2/60) + " minutes if they're not already saved")
    type_details = {}
    for i, type_id in enumerate(type_name_by_type):
        if type_id not in type_ids:
            continue
        u.overwrite_print("--> Getting type: " + type_name_by_type[type_id] + "." + str(i) + "/" + str(num_types))
        url = "https://esi.evetech.net/latest/universe/types/" + type_id + "/?datasource=tranquility&language=en-us"

        type_details[type_name_by_type[type_id]] = u.get_data(
            url=url,
            fileloc="./data/types/" + type_name_by_type[type_id] + ".json"
        )
    print("")
    return type_details


def get_routes_by_od_pairs(od_pairs_and_names):
    num_od_pairs = len(od_pairs_and_names)
    print("\n\nWarning! Getting details for " + str(num_od_pairs) + " origin-destination pairs.")
    print("This could take roughly: " + str(num_od_pairs*2/60) + " minutes if they're not already saved")
    route_by_od_pair = {}
    for i, od_pair in enumerate(od_pairs_and_names):
        u.overwrite_print("--> Getting route: " + od_pair[2] + "-->" + od_pair[3] + "." + str(i) + "/" + str(num_od_pairs))
        route_by_od_pair[od_pair] = u.get_data(
            url="https://esi.evetech.net/latest/route/" + str(od_pair[0]) + "/" + str(od_pair[1]) + "/?datasource=tranquility&flag=secure",
            fileloc="./data/routes/" + str(od_pair[2]) + "_to_" + str(od_pair[3]) + ".json",
        )
    print("")

    return route_by_od_pair


def get_system_details(system_name_by_system):

    num_systems = len(system_name_by_system.keys())
    system_details = {}
    print ("\nGetting system details for " + str(num_systems) + " systems")
    for i, system_id in enumerate(system_name_by_system):
        u.overwrite_print("--> Getting system: " + system_name_by_system[system_id] + "." + str(i+1) + "/" + str(num_systems))
        url = "https://esi.evetech.net/latest/universe/systems/" + system_id + "/?datasource=tranquility&language=en-us"
        system_details[system_name_by_system[system_id]] = u.get_data(
            url=url,
            fileloc="./data/systems/" + system_name_by_system[system_id] + ".json"
        )
    print("")
    return system_details


def get_pure_arbitrage(min_margin, max_item_purchase_price, min_potential_revenue, min_system_sec_rating, single_cargo=True, cargo_capacity=0, get_routes=True, get_new_orders=False, get_new_lookups=False, safe_regions=True):

    if single_cargo and cargo_capacity == 0:
        print("Please provide a cargo capacity")
        return

    # can't force another download of the lookups. Assumes they've been saved in get_and_save_orders()
    lookups = get_name_lookups(force=get_new_lookups)
    region_name_by_region = lookups["regions"]
    system_name_by_system = lookups["systems"]
    type_name_by_type = lookups["types"]

    if get_new_orders:
        get_and_save_orders(force=True, force_lookups=False, safe_regions=safe_regions)
        df = pd.read_csv("./data/orders/orders.csv", quotechar="|")
        print("\nGetting interim dictionary. This may take a minute..")
        df_grouped = df.groupby("type_name")
        df_dict = df_grouped.apply(
            lambda group: {
                "buy": {col: group[group["is_buy_order"] == True][col].tolist() for col in group.columns},
                "sell": {col: group[group["is_buy_order"] == False][col].tolist() for col in group.columns}
            }
        ).to_dict()
        u.write_to_json(df_dict, "./data/orders/orders_by_item.csv")
    else:
        print("\nLoading saved order dictionary at: ./data/orders/orders_by_item.csv")
        df_dict = u.load_data("./data/orders/orders_by_item.csv")
        if len(df_dict) == 0:
            print("No order data saved, but 'get_new_orders' parameter was set to False. Downloading anyway")
            get_and_save_orders(force=True, force_lookups=False, safe_regions=safe_regions)
            df = pd.read_csv("./data/orders/orders.csv", quotechar="|")
            print("\nGetting interim dictionary. This may take a minute..")
            df_grouped = df.groupby("type_name")
            df_dict = df_grouped.apply(
                lambda group: {
                    "buy": {col: group[group["is_buy_order"] == True][col].tolist() for col in group.columns},
                    "sell": {col: group[group["is_buy_order"] == False][col].tolist() for col in group.columns}
                }
            ).to_dict()
            u.write_to_json(df_dict, "./data/orders/orders_by_item.csv")

    rows = []
    item_count = 0
    artbitrage_count = 0
    system_details = get_system_details(system_name_by_system)
    for item in df_dict.keys():
        item_count += 1
        u.overwrite_print("Processing item: " + str(item_count) + "/" + str(len(df_dict.keys())) + ". " + str(artbitrage_count) + " opportunities found so far")
        for i in range(len(df_dict[item]["buy"]["price"])):
            if system_details[df_dict[item]["buy"]["system_name"][i]]["security_status"] < min_system_sec_rating:
                continue
            for j in range(len(df_dict[item]["sell"]["price"])):
                if df_dict[item]["sell"]["price"][j] > max_item_purchase_price or system_details[df_dict[item]["sell"]["system_name"][j]]["security_status"] < min_system_sec_rating:
                    continue
                if df_dict[item]["buy"]["price"][i] > df_dict[item]["sell"]["price"][j]:
                    margin = ((df_dict[item]["buy"]["price"][i] / df_dict[item]["sell"]["price"][j]) - 1)*100
                    if margin >= min_margin:
                        max_items_could_be_transacted = min(df_dict[item]["sell"]["volume_remain"][j], df_dict[item]["buy"]["volume_remain"][i])
                        potential_revenue = (max_items_could_be_transacted*df_dict[item]["buy"]["price"][i]) - (max_items_could_be_transacted*df_dict[item]["sell"]["price"][j])
                        if potential_revenue >= min_potential_revenue:
                            artbitrage_count += 1
                            row = {
                                "item_id": df_dict[item]["sell"]["type_id"][j],
                                "item": item.replace(",", "-"),
                                "buy_in_region": df_dict[item]["sell"]["region_name"][j],
                                "buy_in_system_name": df_dict[item]["sell"]["system_name"][j],
                                "buy_in_location_id": df_dict[item]["sell"]["location_id"][j],
                                "sell_in_region": df_dict[item]["buy"]["region_name"][i],
                                "sell_in_system_name": df_dict[item]["buy"]["system_name"][i],
                                "sell_in_location_id": df_dict[item]["buy"]["location_id"][i],
                                "buy_price": df_dict[item]["sell"]["price"][j],
                                "sell_price": df_dict[item]["buy"]["price"][i],
                                "buy_min_volume": df_dict[item]["sell"]["min_volume"][j],
                                "sell_min_volume": df_dict[item]["buy"]["min_volume"][i],
                                "amount_available_to_buy": df_dict[item]["sell"]["volume_remain"][j],
                                "amount_able_to_be_sold": df_dict[item]["buy"]["volume_remain"][i],
                                "margin": margin,
                                "potential_revenue": potential_revenue,
                                "_buy_system": df_dict[item]["sell"]["system_id"][j],
                                "_sell_system": df_dict[item]["buy"]["system_id"][i],
                                "buy_system_sec": system_details[df_dict[item]["sell"]["system_name"][j]]["security_status"],
                                "sell_system_sec": system_details[df_dict[item]["buy"]["system_name"][i]]["security_status"]
                            }
                            rows.append(row)

    # Get type details only for items with arbitrage opportunities. Saves pulling down 35k items 1 by 1
    type_ids = list(set([str(row["item_id"]) for row in rows]))
    type_details = get_type_details(type_name_by_type, type_ids)
    header = [
        "item_id", "item", "buy_in_region", "buy_in_system_name", "buy_in_location_id",
        "sell_in_region", "sell_in_system_name", "sell_in_location_id",
        "buy_price", "sell_price", "buy_min_volume", "sell_min_volume", "amount_available_to_buy",
        "amount_able_to_be_sold", "margin", "potential_revenue", "_buy_system", "_sell_system",
        "buy_system_sec", "sell_system_sec", "item_volume"
    ]
    for row in rows:
        row["item_volume"] = type_details[row["item"]]["packaged_volume"]

    single_cargo_rows = []
    if single_cargo:
        print("\nFiltering to opportunities making > " + str(min_potential_revenue) + " per cargo of " + str(cargo_capacity) + "m3")
        header.append("potential_revenue_per_cargo")
        for i, row in enumerate(rows):
            items_per_single_cargo = cargo_capacity / row["item_volume"]
            potential_revenue_per_item = row["sell_price"] - row["buy_price"]
            potential_revenue_per_cargo = min(
                potential_revenue_per_item*items_per_single_cargo,
                row["potential_revenue"]
            )
            row["potential_revenue_per_cargo"] = potential_revenue_per_cargo
            if potential_revenue_per_cargo > min_potential_revenue:
                single_cargo_rows.append(row)

        rows = single_cargo_rows
        print("\nFiltered to " + str(len(rows)) + " opportunities")


    if get_routes:
        header.append("route")
        header.append("route_jumps")
        od_pairs = list(set([(row["_buy_system"], row["_sell_system"], row["buy_in_system_name"], row["sell_in_system_name"]) for row in rows]))
        route_by_od_pair = get_routes_by_od_pairs(od_pairs)
        for row in rows:
            route = route_by_od_pair[(row["_buy_system"], row["_sell_system"], row["buy_in_system_name"], row["sell_in_system_name"])]
            row["route"] = '-'.join([str(i) for i in route])
            row["route_jumps"] = len(route)

    u.write_to_csv(header,rows,"./output/pure_arbitrage.csv")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--min_margin', default=30, type=float, help='Limits results to those where the buy/sell margin is > value')
    parser.add_argument('--max_item_purchase_price', default=1000000, type=float, help='Limits results to those where each item can be purchased for < value')
    parser.add_argument('--min_potential_revenue', default=5000000, type=float, help=' Limits results to opportunities where the total potential revenue from thr arbitrage is > value')
    parser.add_argument('--min_system_sec_rating', default=0.5, type=float, help='Limits results to those where both the buy and sell systems have security statuses >= value')
    parser.add_argument('--single_cargo', type=u.str2bool, nargs="?", const=True, default=True, help='Default True. If True, requires cargo_capacity param to be > 0. If True, limits results to those where >= min_potential_revenue can be made from one cargo hold of the given item in the opportunity')
    parser.add_argument('--cargo_capacity', default=0, type=float, help='The cargo capacity to limit each opportunity to')
    parser.add_argument('--get_routes', type=u.str2bool, nargs="?", const=True, default=True, help='WARNING: Can vastly increase run time. Routes will be saved however. First run time might be slow. If True, finds the route between the buy/sell system and adds the # of jumps to the results')
    parser.add_argument('--get_new_orders', type=u.str2bool, nargs="?", const=True, default=True, help='If True, downloads new orders and saves them to the filesystem prior to finding arbitrage opportunities. Can take ~1h')
    parser.add_argument('--get_new_lookups', type=u.str2bool, nargs="?", const=False, default=False, help='If True, downloads new region/system/item names. Only set to True if you know new systems/regions/item names may have been added to the game. Rare.')
    parser.add_argument('--safe_regions', type=u.str2bool, nargs="?", const=True, default=True, help='Default True. Used in conjunction with get_new_orders. If True, only downloads results from regions in Cal/Gal/Min/Amarr space. See code for list.')
    args = parser.parse_args()

    if u.directories_exist() == False:
        u.create_folder_structure()

    get_pure_arbitrage(args.min_margin, args.max_item_purchase_price, args.min_potential_revenue, args.min_system_sec_rating, args.single_cargo, args.cargo_capacity, args.get_routes, args.get_new_orders, args.get_new_lookups, args.safe_regions)
