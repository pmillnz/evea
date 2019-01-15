import json
import sys
import requests
import csv
import os
import argparse

def write_to_json(data, file):
    overwrite_print("<< Writing " + file + " to JSON\n")
    with open(file, 'w') as f:
        json.dump(data, f)


def write_to_csv(header, rows, file, d=True):
    overwrite_print("<< Writing " + file + " to CSV")

    with open(file, "w") as f:
        if d:
            cw = csv.DictWriter(f,header,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            cw.writeheader()
        else:
            cw = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            cw.writerow(header)
        cw.writerows(rows)


def overwrite_print(s):
    ERASE_LINE = '\x1b[2K'
    sys.stdout.write(ERASE_LINE)
    sys.stdout.write('\r'+str(s))
    sys.stdout.flush(),


def load_data(fileloc):
    overwrite_print(">> Loading " + fileloc)
    try:
        with open(fileloc) as f:
            return json.load(f)
    except IOError:
        print(" - No such file")
        return {}


def download_data(url, request_type="get", post_data=None, paged=False, post_in_batches=False, batch_size=None):
    print("\n<< Downloading from: " + url)
    data = []
    if request_type == "get":
        if paged:
            for page in [i + 1 for i in range(999999)]:
                overwrite_print("------> Working on page " + str(page))
                page_url = url + "&page=" + str(page)
                r = requests.get(page_url)
                try:
                    page_data = r.json()
                    if len(page_data) > 0:
                        data += page_data
                    else:
                        break
                except ValueError:
                    print("Error! ValueError when trying to extract JSON")
                    print("Here's the response: " + r.text)
                    continue
        else:
            r = requests.get(url)
            try:
                data = r.json()
            except ValueError:
                print("Error! ValueError when trying to extract JSON")
                print("Here's the response: " + r.text)
    elif request_type == "post":
        if post_in_batches:
            post_data_length = len(post_data)
            data = []
            print("------> Iterating over " + str(post_data_length) + " rows of post data")

            for iteration in range(post_data_length / batch_size):
                overwrite_print("\t---> Batch is: " + str(iteration*batch_size) + " to " + str(((iteration+1)*batch_size)-1))
                r = requests.post(url, data=json.dumps(post_data[iteration*batch_size: (iteration+1)*batch_size]))
                try:
                    iteration_data = r.json()
                    if len(iteration_data) > 0:
                        data += iteration_data
                    else:
                        continue
                except ValueError:
                    print("Error! ValueError when trying to extract JSON")
                    print("Here's the response: " + r.text)
                    continue

            if post_data_length % batch_size > 0:
                overwrite_print("---> Batch is: " + str(batch_size*(post_data_length / batch_size)) + " to " + str((batch_size*(post_data_length / batch_size) + (post_data_length % batch_size))-1))
                r = requests.post(url, data=json.dumps(post_data[batch_size*(post_data_length / batch_size): batch_size*(post_data_length / batch_size) + (post_data_length % batch_size)]))
                try:
                    iteration_data = r.json()
                    if len(iteration_data) > 0:
                        data += iteration_data
                except ValueError:
                    print("Error! ValueError when trying to extract JSON")
                    print("Here's the response: " + r.text)
        else:
            r = requests.post(url, data=json.dumps(post_data))
            try:
                data = r.json()
            except ValueError:
                print("Error! ValueError when trying to extract JSON")
                print("Here's the response: " + r.text)
    else:
        print("Incorrect request type")

    return data


def get_data(url, fileloc, request_type="get", post_data=None, paged=False, post_in_batches=False, batch_size=None, force=False):
    if force == False:
        try:
            data = load_data(fileloc)
            if len(data) > 0:
                return data
        except IOError:
            pass

    # Force = True or no data at fileloc
    data = download_data(
        url, request_type, post_data, paged, post_in_batches, batch_size
    )
    write_to_json(data, fileloc)
    return data


def directories_exist():
    level_1 = ["data", "output"]
    level_2_data = ["orders", "regions", "routes", "systems", "types"]
    for l1 in level_1:
        if os.path.isdir("./" + l1) == False:
            return False
            if l1 == "data":
                for l2 in level_2_data:
                    if os.path.isdir("./" + l1 + "/" + l2) == False:
                        return False
    return True


def create_folder_structure():
    print "Creating file structure"
    level_1 = ["data", "output"]
    level_2_data = ["orders", "regions", "routes", "systems", "types"]
    for l1 in level_1:
        if os.path.isdir("./" + l1) == False:
            os.mkdir("./" + l1, 0777)
            if l1 == "data":
                for l2 in level_2_data:
                    if os.path.isdir("./" + l1 + "/" + l2) == False:
                        os.mkdir("./" + l1 + "/" + l2, 0777)


    print "Done. Created:"
    for l1 in level_1:
        print "./" + l1
        if l1 == "data":
            for l2 in level_2_data:
                print "--> ./" + l1 + "/" + l2


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
