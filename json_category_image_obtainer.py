from woocommerce import API

ckey = "ck_cfd77a2fa56e6b11525613ac736875301f00bf2e"
skey = "cs_43f1c730767747fc192c26bf59d446633718f9b3"
# --- ПОМЕНЯТЬ ДАННЫЕ ДЛЯ ПРОДА! --- OK
wcapi = API(
    url="https://xn--l1a1ba.xn--p1ai",
    consumer_key=ckey,
    consumer_secret=skey,
    version="wc/v3",
    timeout=100
)
content = []
for page in range(1, 3):
    for item in wcapi.get("products/categories", params={"per_page": 100, "page": page}).json():
        content.append(item)
print("data obtained.")
result = {}
for item in content:
    if item["image"] is not None:
        result[item["name"]] = item["image"]["src"]
    
with open("category_list.json", "a") as f:
    f.write("{\n")
    count = 0
    for name in result:
        if count != len(result)-1:
            f.write('    "' + str(name) + '": ' + '"' + str(result[name]) + '",\n')
        else:
            f.write('    "' + str(name) + '": ' + '"' + str(result[name]) + '"\n')
        count += 1
    f.write("}")
print("finished.")