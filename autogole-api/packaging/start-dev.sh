docker run \
  -dit --name rtmon \
  -v $(pwd)/../:/opt/devrtmon/:rw \
  -v $(pwd)/files/etc/rtmon.yaml:/etc/rtmon.yaml:ro \
  -v $(pwd)/files/etc/sense-o-auth.yaml:/etc/sense-o-auth.yaml:ro \
  -v $(pwd)/files/etc/sense-o-auth-prod.yaml:/etc/sense-o-auth-prod.yaml:ro \
  --restart always \
  --net=host \
  rtmon



#  -v /Users/jbalcas/work/sdn-sense/sense-o-py-client:/opt/devsenseclient/:rw \
