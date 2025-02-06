#!/bin/sh
echo "Dont forget to update the rtmon.yaml file with the correct parameters"
echo "Dont forget to update the sense-o-auth.yaml file with the correct parameters"
echo "Dont forget to update the sense-o-auth-prod.yaml file with the correct parameters"
echo "Dont forget to update the hostcert and hostkey file with certificates"

docker run \
  -dit --name rtmon \
  -v $(pwd)/../:/opt/devrtmon/:rw \
  -v $(pwd)/../../../sense-o-py-client/:/opt/sense-o-py-client/:rw \
  -v $(pwd)/files/etc/rtmon.yaml:/etc/rtmon.yaml:ro \
  -v $(pwd)/files/etc/sense-o-auth.yaml:/etc/sense-o-auth.yaml:ro \
  -v $(pwd)/files/etc/sense-o-auth-prod.yaml:/etc/sense-o-auth-prod.yaml:ro \
  -v $(pwd)/files/etc/grid-security/hostcert.pem:/etc/grid-security/hostcert.pem:ro \
  -v $(pwd)/files/etc/grid-security/hostcert.pem:/etc/grid-security/hostkey.pem:ro \
  --restart always \
  -p 8000:8000 \
  rtmon
