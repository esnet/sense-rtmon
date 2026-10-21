# The RTMon Archify render/serve sidecar.
#
# A separate image from sense-rtmon on purpose, even though both are built from
# this repository: this one is a Node runtime plus the vendored Archify render
# tree, and folding that into the RTMon image would put both in every RTMon
# deployment whether or not the operator draws this panel. Built and pushed by
# .github/workflows/archify-image.yaml, and run as a second container in the
# RTMon pod - see the topology section of the README.
FROM node:22-alpine

WORKDIR /app
COPY package.json server.mjs archify-entry.mjs ./
COPY archify-cli ./archify-cli

# Archify needs the version file relative to its own tree and nothing else;
# it has no npm dependencies.
ENV ARCHIFY_DIAGRAM_DIR=/srv/diagrams
RUN mkdir -p "$ARCHIFY_DIAGRAM_DIR"

EXPOSE 8081
USER node

# Gate on health rather than a pidfile: no PID 1 zombie handling needed, and
# node reaps its own children (the archify renderer is spawned and waited).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8081/healthz || exit 1

CMD ["node", "server.mjs"]
