#!/bin/bash
docker run --rm -p 2767:2767 --env FLASK_APP=croprows-api --env FLASK_ENV=development --env CRG_MODE=serial --name crg_v2 -v $(pwd)/droneimages:/app/orthomosaics crg_v2:latest
