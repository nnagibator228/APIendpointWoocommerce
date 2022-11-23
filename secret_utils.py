# read docker secret
def read_secret(secret_name):
    try:
        with open('/run/secrets/{0}'.format(secret_name), 'r') as secret_file:
            return str(secret_file.readline()).rstrip().strip()
    except IOError:
        print("error reading config secret '", secret_name, "'!")
        return None
