import datetime
import json
import math
import time
from webhook_utils import *
import requests
from woocommerce import API

from logger import printl
from models import Item, Category, ShopCategory, ChildCategory
from secret_utils import read_secret

ckey = read_secret("woocomm_consumer_key")
skey = read_secret("woocomm_secret_key")
# --- ПОМЕНЯТЬ ДАННЫЕ ДЛЯ ПРОДА! --- OK
wcapi = API(
    url="http://51.250.10.82",
    consumer_key=ckey,
    consumer_secret=skey,
    version="wc/v3",
    timeout=100
)


# --------------------------------------------- CATEGORY UTILITY FUNCTIONS ---------------------------------------------
def get_base_bulk_categories(bdata):
    bshops = set()
    bcategories = set()
    bchilds = set()
    for item in bdata:
        shop = ShopCategory({"name": str(item.shop)})
        category = Category({"name": str(item.category), "parent": shop})
        child = ChildCategory({"name": str(item.child), "parent": category})

        bshops.add(shop)
        bcategories.add(category)
        bchilds.add(child)
    return bshops, bcategories, bchilds


def get_cslug_list(data):
    cslugs = set()
    for category in data:
        cslugs.add(str(category.slug))
    return cslugs


def get_slug_id_associated(quantity):
    base_category_ids_to_slug = {}
    base_category_slug_to_ids = {}
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] == 0:
                    shop = ShopCategory(item)
                    base_category_ids_to_slug[str(shop.id)] = shop.slug
                    base_category_slug_to_ids[str(shop.slug)] = str(shop.id)
                else:
                    category = Category(item)
                    base_category_ids_to_slug[str(category.id)] = category.slug
                    base_category_slug_to_ids[str(category.slug)] = str(category.id)
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)
    return base_category_ids_to_slug, base_category_slug_to_ids


def get_shop_associate(quantity):
    shop_by_id = {}
    shop_by_name = {}
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] == 0:
                    shop = ShopCategory(item)
                    shop_by_id[str(shop.id)] = shop
                    shop_by_name[str(shop.name)] = shop
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)
    return shop_by_id, shop_by_name


def get_category_associate(quantity, sbi):
    category_by_id = {}
    category_by_name = {}
    cshop_ids = set()
    ccategories = set()
    res = set()
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] == 0:
                    cshop_ids.add(ShopCategory(item).id)
                else:
                    if str(item["parent"]) in sbi:
                        item["parent"] = sbi[str(item["parent"])]
                        cat = Category(item)
                        ccategories.add(cat)
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)
    for item in ccategories:
        if item.parent.id in cshop_ids:
            res.add(item)
    for item in res:
        category_by_id[str(item.id)] = item
        category_by_name[str(item.slug)] = item
    return category_by_id, category_by_name


def category_contains(data, item):
    for c in data:
        if str(item.slug) == str(c.slug):
            return c
    return None


# --------------------------------------------------- SHOP FUNCTIONS ---------------------------------------------------
def get_curr_shops(quantity):
    cshops = set()
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] == 0:
                    shop = ShopCategory(item)
                    cshops.add(shop)
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)
    return cshops


def formation_shop(shop_bdata, shop_cdata):
    tdl = set()
    shop_bdata_slugs = get_cslug_list(shop_bdata)
    for shop in shop_cdata:
        if shop.slug not in shop_bdata_slugs:
            tdl.add(shop)
    return tdl


def addition_shop(shop_bdata, shop_cdata):
    tad = set()
    shop_cdata_slugs = get_cslug_list(shop_cdata)
    for shop in shop_bdata:
        if shop.slug not in shop_cdata_slugs:
            tad.add(shop)
    return tad


def to_delete_shops(tdl):
    for shop in tdl:
        if shop.id != -1:
            try:
                printl(wcapi.delete(f"products/categories/{shop.id}", params={"force": True}).json())
            except json.decoder.JSONDecodeError:
                print(wcapi.delete(f"products/categories/{shop.id}", params={"force": True}).content)


def to_add_shops(tad):
    for shop in tad:
        data = {
            "name": shop.name,
            "slug": shop.slug,
            "display": "subcategories"
        }
        if shop.image is not None:
            data["image"] = {"src": shop.image}
        printl(wcapi.post("products/categories", data).json())


# ------------------------------------------------- CATEGORY FUNCTIONS -------------------------------------------------
def get_curr_categories(quantity, sbi):
    cshop_ids = set()
    ccategories = set()
    res = set()
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] == 0:
                    cshop_ids.add(ShopCategory(item).id)
                else:
                    if str(item["parent"]) in sbi:
                        item["parent"] = sbi[str(item["parent"])]
                        cat = Category(item)
                        ccategories.add(cat)
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)
    for item in ccategories:
        if item.parent.id in cshop_ids:
            res.add(item)
    return res


def formation_categories(category_bdata, category_cdata, sbn):
    tdl = set()
    tud = set()
    for category in category_cdata:
        ccon = category_contains(category_bdata, category)
        if ccon is None:
            tdl.add(category)
        else:
            if category.slug != ccon.slug:
                tud.add((category, ccon.parent))
    return tdl, tud


def addition_categories(category_bdata, category_cdata, sbn):
    tad = set()
    for category in category_bdata:
        ccon = category_contains(category_cdata, category)
        if ccon is None:
            category.parent = sbn[str(category.parent.name)]
            tad.add(category)
    return tad


def to_delete_categories(tdl):
    for category in tdl:
        if category.id != -1:
            try:
                printl(wcapi.delete(f"products/categories/{category.id}", params={"force": True}).json())
            except json.decoder.JSONDecodeError:
                print(wcapi.delete(f"products/categories/{category.id}", params={"force": True}).content)


def to_add_categories(tad):
    for category in tad:
        data = {
            "name": category.name,
            "parent": category.parent.id,
            "display": "subcategories"
        }
        if category.image is not None:
            data["image"] = {"src": category.image}
        printl(wcapi.post("products/categories", data).json())


def to_update_categories(tud):
    for category in tud:
        data = {
            "parent": category[1].id
        }
        if category[0].image is not None:
            data["image"] = {"src": category[0].image}
        printl(wcapi.put("products/categories/" + str(category[0].id), data).json())


# -------------------------------------------------- CHILD FUNCTIONS ---------------------------------------------------
def get_curr_childs(quantity, cbi):
    res = set()
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
                if item["parent"] != 0:
                    if str(item["parent"]) in cbi:
                        item["parent"] = cbi[str(item["parent"])]
                        res.add(ChildCategory(item))
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products/categories", params={"per_page": 100}).content)

    return res


def formation_childs(child_bdata, child_cdata):
    tdl = set()
    tud = set()
    for child in child_cdata:
        print(child.slug, " - ", )
        ccon = category_contains(child_bdata, child)
        if ccon is None:
            tdl.add(child)
        else:
            if child.slug != ccon.slug:
                tud.add((child, ccon.parent))
    return tdl, tud


def addition_childs(child_bdata, child_cdata, cbn):
    tad = set()
    for category in child_bdata:
        ccon = category_contains(child_cdata, category)
        if ccon is None:
            category.parent = cbn[str(category.parent.slug)]
            tad.add(category)
    return tad


def to_delete_childs(tdl):
    for child in tdl:
        if child.id != -1:
            try:
                printl(wcapi.delete(f"products/categories/{child.id}", params={"force": True}).json())
            except json.decoder.JSONDecodeError:
                print(wcapi.delete(f"products/categories/{child.id}", params={"force": True}).content)


def to_add_childs(tad):
    for child in tad:
        data = {
            "name": child.name,
            "parent": child.parent.id
        }
        if child.image is not None:
            data["image"] = {"src": child.image}
        printl(wcapi.post("products/categories", data).json())


def to_update_childs(tud):
    for child in tud:
        data = {
            "parent": child[1].id
        }
        if child[0].image is not None:
            data["image"] = {"src": child[0].image}
        printl(wcapi.put("products/categories/" + str(child[0].id), data).json())


# ------------------------------------------------- UTILITY  FUNCTIONS -------------------------------------------------
# obtain all sku set from item set
def get_sku_list(data):
    skl = set()
    for item in data:
        skl.add(item.sku)
    return skl


# search item by sku
def search_by_sku(data, sku_filter):
    for item in data:
        if item.sku == sku_filter:
            return item
    return None


def set_categories_id(data, cdict):
    for item in data:
        item.categories[0]["id"] = cdict[str(item.categories[0]["name"])]
    return data


# ------------------------ ФУНКЦИЯ ДЛЯ ХАРДКОДА!!! УБРАТЬ НА ПРОДЕ -----------
def change_fonari(data):
    for item in data:
        # ПОМЕНЯТЬ НА ПРОДЕ НА ЗНАЧЕНИЕ, КОТОРОЕ БАГАЕТСЯ ТАМ -- OK
        if str(item.categories[0]["name"]) == 'Рыбалка/Спортивный товар/Фонари спортивные':
            item.categories[0]["name"] = 'Рыбалка/Электроника/Элементы питания'
    return data


# ------------------------------------------------- INITIAL  FUNCTIONS -------------------------------------------------

# get currently imported items
def get_current_data(quantity):
    items = set()
    try:
        for page in range(1, math.ceil(quantity / 100) + 1):
            for item in wcapi.get("products", params={"per_page": 100, "page": page}).json():
                items.add(Item(item))

        return items
    except requests.exceptions.JSONDecodeError:
        print(wcapi.get("products"))


# get items from API gateway
def get_bulk_data():
    items = set()
    url = "https://script.google.com/macros/s/AKfycbxC8Z6Dop31UwQAzwJ7G93HQiuF4Jj8w2yUP4noE_IG3E4zwv7hINmXwRhf_PMafQVZ/exec"
    btoken = read_secret("bulk_token")
    payload = {'token': btoken,
               'method': 'getCatalog'}
    files = [

    ]
    headers = {}
    content = requests.request("POST", url, headers=headers, data=payload, files=files).json()
    str_imgs = send_init_webhook().decode()
    print(str_imgs)
    curr_images = str_imgs.split(" ")
    print(len(curr_images))
    for item in content:
        add_item = Item(item)
        for image in add_item.images:
            img_url = image["src"]
            img_name = str(img_url).split("/")[-1]
            webp_img_name = img_name.split(".")[0] + ".webp"
            if webp_img_name not in curr_images:
                print(webp_img_name)
                send_webhook(img_url)
            image["src"] = "http://89.108.103.13:8080/" + webp_img_name
        items.add(add_item)

    return items


# --------------------------------------------------- MAIN FUNCTIONS ---------------------------------------------------

# format items to_delete and to_update setsцы
def formation(bdata, cdata):
    tdl = set()
    tud = []
    bulk_sku_list = get_sku_list(bdata)
    for item in cdata:
        if item.sku not in bulk_sku_list:
            tdl.add(item)
        else:
            paired = search_by_sku(bdata, item.sku)
            diffs = item.compare_with(paired)
            if diffs is not None:
                tud.append(diffs)
    return tdl, tud


# format items to_add set
def addition(bdata, cdata):
    tad = set()
    curr_data_sku = get_sku_list(cdata)
    for item in bdata:
        if item.sku not in curr_data_sku:
            tad.add(item)
    return tad


# run items add requests
def to_add_products(tad, cdict):
    for item in tad:
        data = item.get_json()
        for i in data["categories"]:
            # УБРАТЬ ХАРДКОД - БАГ НА СПОРТИВНЫЕ ФОНАРИ
            i["id"] = cdict[i["name"]]
        printl(str(datetime.datetime.now()) + " | ++ " + str(data))
        try:
            printl(wcapi.post("products", data).json())
        except requests.exceptions.JSONDecodeError:
            time.sleep(0.1)
            printl(wcapi.post("products", data).json())
        except json.decoder.JSONDecodeError:
            time.sleep(0.1)
            printl(wcapi.post("products", data).json())


# run items delete requests
def to_delete_products(tdl):
    for item in tdl:
        id = item.id
        if id != -1:
            printl(str(datetime.datetime.now()) + " | -- " + str(item.get_json()))
            printl(wcapi.delete(f"products/{str(id)}", params={"force": True}).json())


# run items update requests
def to_update_products(tud, cdict):
    for item in tud:
        data = item[1]
        if "categories" in data:
            for i in data["categories"]:
                i["id"] = cdict[i["name"]]
        printl(str(datetime.datetime.now()) + " | >> " + str(data))
        printl(wcapi.put("products/" + str(item[0]), data).json())


# -------------------------------------------------------- RUN --------------------------------------------------------

# main sync function with log output
def sync():
    # obtain main data
    start = time.time()
    printl(datetime.datetime.today().strftime(f'%H:%M:%S | sync started.'))
    bulk_data = change_fonari(get_bulk_data())
    print("bulk data obtained. ")
    bulk_shops, bulk_categories, bulk_childs = get_base_bulk_categories(bulk_data)
    cat_quantity = len(bulk_shops) + len(bulk_categories) + len(bulk_childs)
    quantity = len(bulk_data)
    curr_data = get_current_data(quantity)
    print("current data obtained. ")
    printl("current bulk product quantity: " + str(quantity))
    printl("current woocomm product quantity: " + str(len(curr_data)) + str("\n"))

    # working with categories
    curr_shops = get_curr_shops(cat_quantity)
    to_delete_shop = formation_shop(bulk_shops, curr_shops)
    to_add_shop = addition_shop(bulk_shops, curr_shops)
    to_add_shops(to_add_shop)
    shop_by_id, shop_by_name = get_shop_associate(cat_quantity)
    curr_categories = get_curr_categories(cat_quantity, shop_by_id)
    to_delete_category, to_update_category = formation_categories(bulk_categories, curr_categories, shop_by_name)
    to_add_category = addition_categories(bulk_categories, curr_categories, shop_by_name)
    to_add_categories(to_add_category)
    to_update_categories(to_update_category)
    category_by_id, category_by_name = get_category_associate(cat_quantity, shop_by_id)
    curr_childs = get_curr_childs(cat_quantity, category_by_id)
    to_delete_child, to_update_child = formation_childs(bulk_childs, curr_childs)
    to_add_child = addition_childs(bulk_childs, curr_childs, category_by_name)
    to_add_childs(to_add_child)
    to_update_childs(to_update_child)
    # ------- порядок удаления реверсивный -------
    to_delete_childs(to_delete_child)
    to_delete_categories(to_delete_category)
    to_delete_shops(to_delete_shop)
    printl("----------- categories synchronized. -----------")
    # working with items
    category_dict = dict()
    curr_childs_for_products = get_curr_childs(cat_quantity, category_by_id)
    for i in curr_childs_for_products:
        category_dict[i.slug] = i.id
    print(category_dict)
    bulk_data = set_categories_id(bulk_data, category_dict)
    to_delete, to_update = formation(bulk_data, curr_data)
    to_add = addition(bulk_data, curr_data)
    printl("\nto update:")
    for i in to_update:
        printl(str(i[0]) + " - " + str(i[1]))
    printl("\nto delete:")
    for i in to_delete:
        printl(str(i.get_json()))
    printl("\nto add:")
    for i in to_add:
        printl(str(i.get_json()))
    printl("\n -------------------------------------------------------------------------------------------------------")
    to_update_products(to_update, category_dict)
    to_delete_products(to_delete)
    to_add_products(to_add, category_dict)
    printl("products synchronized for: " + str(time.time() - start) + "secs. \n")
