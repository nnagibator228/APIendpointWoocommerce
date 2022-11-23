# category entity class
class BaseCategory:
    def __init__(self, category):
        self.id = int(category["id"]) if 'id' in category else -1
        self.name = category["name"]
        self.image = category["image"] if 'image' in category else None
        self.slug = str(self.name)

    def __hash__(self):
        return hash(self.slug + str(self.id))

    def __eq__(self, other):
        return self.slug == other.slug

    # get json-formatted category entity fields
    def get_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "display": "default"
        }
        return data


class ShopCategory(BaseCategory):

    def get_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "display": "subcategories"
        }
        return data


class Category(BaseCategory):
    def __init__(self, category):
        super().__init__(category)
        self.parent = category["parent"]
        self.slug = str(self.parent.slug) + "/" + str(self.name) if type(self.parent) == ShopCategory or type(
            self.parent) == Category else str(self.parent) + "/" + str(self.name)

    def get_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.id,
            "display": "subcategories"
        }
        return data

    def compare_with(self, category):
        if self.slug != category.slug:
            return self.id, category.parent
        else:
            return None


class ChildCategory(Category):
    def get_json(self):
        data = {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.id,
            "display": "default"
        }
        return data


# item entity class
class Item:
    def __init__(self, item):
        self.id = int(item["id"]) if 'id' in item else -1
        self.sku = item["sku"]
        self.name = item["name"]
        self.description = item["description"].replace("<p>", "").replace("</p>", "").replace("<br />",
                                                                                              "").rstrip().strip().replace(
            "\n", "").replace("&amp;", "&")
        if "oldPrice" in item:
            self.shop = str(item["shop"])
            self.child = str(item["child"])
            self.category = str(item["category"])
            self.regular_price = str(item["oldPrice"])
            self.sale_price = str(item["price"])
            self.slug = str(self.shop) + "/" + str(self.category) + "/" + str(self.child)
            self.stock_quantity = int(item["stock"]) if item["stock"] != "" and item["stock"] is not None else 0
            self.categories = [{"name": str(self.slug)}]
            if item["images"] != "":
                self.images = [{"src": str(i).strip().rstrip()} for i in item["images"].split("\n")]
            else:
                self.images = []
        else:
            self.regular_price = str(item["regular_price"])
            self.sale_price = str(item["sale_price"])
            self.stock_quantity = int(item["stock_quantity"]) if item["stock_quantity"] != "" and item[
                "stock_quantity"] is not None else 0
            self.images = item["images"]
            self.slug = item["categories"][0]["name"]
            self.categories = [{"name": self.slug, "id": item["categories"][0]["id"]}]

    # compares item entity with another and returns differences
    def compare_with(self, item):
        diffs = {}
        if str(self.categories[0]["id"]) != str(item.categories[0]["id"]):
            diffs["categories"] = item.categories
        if self.description != item.description:
            diffs["description"] = item.description
        if self.name != item.name:
            diffs["name"] = item.name
        if self.regular_price != str(item.regular_price):
            diffs["regular_price"] = str(item.regular_price)
        if self.sale_price != str(item.sale_price):
            diffs["sale_price"] = str(item.sale_price)
        if self.stock_quantity != item.stock_quantity:
            diffs["stock_quantity"] = int(item.stock_quantity)
        if len(diffs) == 0:
            return None
        else:
            return self.id, diffs

    # get json-formatted item entity fields
    def get_json(self):
        data = {
            "name": self.name,
            "regular_price": self.regular_price,
            "sale_price": self.sale_price,
            "sku": self.sku,
            "manage_stock": True,
            "stock_quantity": self.stock_quantity,
            "categories": self.categories,
            "description": self.description
        }
        if self.id != -1:
            data["id"] = self.id
        if self.images is not None:
            data["images"] = self.images

        return data
