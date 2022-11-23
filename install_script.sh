#!/bin/bash

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--consumerkey)
      CKEY="$2"
      shift
      shift
      ;;
    -s|--secretkey)
      SKEY="$2"
      shift
      shift
      ;;
    -t|--bulktoken)
      TOKEN="$2"
      shift
      shift
      ;;
    -k|--ctoken)
      CTOKEN="$2"
      shift
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") #
      shift
      ;;
  esac
done

echo "installation script started"

apt install docker.io docker-compose -y
docker swarm init

echo "Packages installed"

mkdir /var/log/woocommsync

echo "Directories created"

echo "${CKEY}" | docker secret create woocomm_consumer_key -

echo "${SKEY}" | docker secret create woocomm_secret_key -

echo "${TOKEN}" | docker secret create bulk_token -

echo "${CTOKEN}" | docker secret create ctoken -

docker stack deploy --compose-file stack.yml woocomm_product_sync
