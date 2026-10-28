#!/usr/bin/env python3
"""Archify architecture IR built from the path model RTMon already has.

Pure functions over plain dicts: no filesystem, no subprocess, no Grafana. The
side effects live in RTMonLibs/Archify.py, which is what makes this half
testable against the manifest fixtures in test/ without a deployment.

The input is the model the Mermaid walk leaves behind - self.orderlist, the
ordered Host/Switch chain findorder() produced - not the manifest. findorder()
consumes manifest["Ports"] as it walks, so there is only one walk to be had and
both diagrams have to share it.

Where this differs from the Mermaid graph, deliberately:

  Mermaid draws a node per switch *port*, plus a node per VLAN, per IP and per
  BGP peer. That is complete, and on a multi-domain path it is also unreadable.
  Here a component is a *device*, ports and VLANs become connection labels, and
  the addressing detail moves into cards. The two panels are shown together, so
  the detail Mermaid carries is never actually lost - it is just not in this
  picture.
"""

# Card items and diagnostic strings are prose the operator reads. Wrapping them
# to 120 columns splits sentences across lines without making either half
# easier to follow, so the same allowance the other RTMon modules take applies.
# pylint: disable=line-too-long
from RTMonLibs.GeneralLibs import _processName

# Geometry. Free placement (explicit pos) rather than layout.mode "grid",
# because grid caps at 12 columns and a long multi-domain path can exceed that.
# The cell maths is the same either way; doing it here removes the ceiling.
CELL_W = 190
CELL_H = 68
# Wide enough for a 14 character connection label (max(30, units * 4.8 + 10),
# so ~77px) to sit in the corridor between two columns with room to spare.
GAP_X = 100
GAP_Y = 80
ORIGIN_X = 48
ORIGIN_Y = 96
# Room under the lowest row for the legend rail and the cards.
BOTTOM_PAD = 150
# architecture.schema.json floors meta.viewBox at these. A single-column path
# is narrower than the floor, so the canvas is clamped up rather than rejected.
VIEWBOX_MIN_W = 320
VIEWBOX_MIN_H = 240

# Rows. The spine of switches runs along the middle; each switch's hosts sit
# directly above and below it, so every edge is one straight segment between
# grid-adjacent cells and none of them route across a third component.
ROW_HOST_UP = 0
ROW_SPINE = 1
ROW_HOST_DOWN = 2
MAX_HOSTS_PER_SWITCH = 2

# Character budgets, derived from the renderer's own fitting maths so this side
# truncates before validation has to reject. The line numbers are in the
# renderer, which lives in the sidecar and not in this repository, so they are
# anchored to the Archify version they were read from and will drift on a bump:
#   archify 2.17.0
#   label    render-architecture.mjs:366  textUnits(label) * 6.6 <= width + 8
#   sublabel/tag  text-fit.mjs:42         units * minimum(6) * 0.6 <= width - 8
#   connection label  render-architecture.mjs:571  max(30, units * 4.8 + 10),
#       which has to stay inside the GAP_X corridor it is centred in.
# Held a little under each true ceiling so a one-character estimate error is not
# the difference between a diagram and a warning. Nothing reads these numbers at
# runtime: a drifted comment costs accuracy in review, never a dashboard.
LABEL_MAX = 26
SUBLABEL_MAX = 44
CONN_LABEL_MAX = 14

# Manifest placeholders. SENSE-O fills these in where it has no value, so they
# are absence, not data.
PLACEHOLDERS = ("?ipv4?", "?ipv6?", "?port_ipv4?", "?port_ipv6?", "?mac?", "?port_mac?", "?peer?", "?port_name?")


def _real(value):
    """True when the manifest gave an actual value rather than a placeholder."""
    return bool(value) and value not in PLACEHOLDERS


def _fit(text, limit):
    """Truncate to the renderer's character budget, marking that it was cut."""
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)] + "…"


def _shortname(value):
    """The device half of a 'site:device' name, or the whole thing if unsplit."""
    parts = str(value or "").split(":")
    return parts[1] if len(parts) > 1 else parts[0]


def _sitename(value):
    """The site half of a 'site:device' name, or the whole thing if unsplit."""
    return str(value or "").split(":", maxsplit=1)[0]


def _hostlabel(name):
    """A host's short name, without the domain.

    'k8s-gen5-02.sdsc.optiputer.net' is 30 characters, which the renderer will
    not fit in a component and truncation turns into
    'k8s-gen5-02.sdsc.optipute…' - longer and no more informative than
    'k8s-gen5-02'. The fully qualified name is still carried, on the Endpoints
    card, where it has room to be read.
    """
    return _shortname(name).split(".")[0] or _shortname(name)


def _deviceKey(item):
    """Identity of the device an orderlist entry belongs to.

    A switch appears once per port in the path, so the key is the node, not the
    port - collapsing those repeats into one component is the whole point of
    this diagram.
    """
    if item.get("Type") == "Host":
        return item.get("Name", "")
    return item.get("Node", "")


def _componentId(key, used):
    """A stable, archify-legal id for a device key.

    _processName is reused rather than reimplemented: it already produces the
    identifier shape archify's schema wants, and using the same function means
    a device carries the same id in both panels.
    """
    base = _processName(key) or "node"
    if base not in used:
        used[base] = key
        return base
    if used[base] == key:
        return base
    # Two different device keys normalised to the same identifier. Rare, but a
    # collision here would silently merge two devices into one component.
    suffix = 2
    while f"{base}_{suffix}" in used and used[f"{base}_{suffix}"] != key:
        suffix += 1
    used[f"{base}_{suffix}"] = key
    return f"{base}_{suffix}"


class DeviceModel:
    """Devices, their ports and the links between them, from one orderlist.

    Built in a single pass so the ordering findorder() established survives:
    the order devices are first seen in is the order they are laid out in, and
    that is the only thing keeping sites contiguous on the canvas.
    """

    def __init__(self, orderlist):
        self.devices = {}  # key -> device dict
        self.order = []  # device keys, first-seen order
        self.portindex = {}  # port URN -> device key
        self.links = {}  # (keyA, keyB) sorted tuple -> link dict
        self._build(orderlist or [])

    def _device(self, key, dtype):
        if key not in self.devices:
            self.devices[key] = {
                "key": key,
                "type": dtype,
                "site": _sitename(key),
                "name": _shortname(key),
                "ports": [],
                "vlans": [],
                "ips": [],
                "macs": [],
                "joint": None,
            }
            self.order.append(key)
        return self.devices[key]

    @staticmethod
    def _note(device, item):
        """Fold one orderlist entry's detail into its device."""
        vlan = item.get("Vlan")
        if vlan and vlan not in device["vlans"]:
            device["vlans"].append(vlan)
        mac = item.get("Mac")
        if _real(mac) and mac not in device["macs"]:
            device["macs"].append(mac)
        for ipkey in ("IPv4", "IPv6"):
            addr = item.get(ipkey)
            if _real(addr) and addr not in device["ips"]:
                device["ips"].append(addr)
        if item.get("JointNetwork"):
            device["joint"] = item["JointNetwork"]

    def _build(self, orderlist):
        for item in orderlist:
            key = _deviceKey(item)
            if not key:
                continue
            if item.get("Type") == "Host":
                device = self._device(key, "Host")
                port = item.get("Interface")
                if port and port not in device["ports"]:
                    device["ports"].append(port)
                self._note(device, item)
                continue
            device = self._device(key, "Switch")
            port = item.get("Name")
            if port and port not in device["ports"]:
                device["ports"].append(port)
            self._note(device, item)
            if item.get("Port"):
                self.portindex[item["Port"]] = key
        # Links need the full port index, so they are a second pass.
        for item in orderlist:
            self._linksFor(item, orderlist)

    def _addLink(self, keya, keyb, port, vlan):
        """Record an undirected device link. Self-links are dropped.

        A switch with two ports in the same path produces a link from a device
        to itself, which archify rejects outright (a connection needs two
        distinct endpoints and at least 24px between them).
        """
        if not keya or not keyb or keya == keyb:
            return
        if keya not in self.devices or keyb not in self.devices:
            return
        pair = tuple(sorted((keya, keyb)))
        link = self.links.setdefault(pair, {"ports": [], "vlans": []})
        if port and port not in link["ports"]:
            link["ports"].append(port)
        if vlan and vlan not in link["vlans"]:
            link["vlans"].append(vlan)

    def _linksFor(self, item, orderlist):
        """Every link one orderlist entry establishes."""
        if item.get("Type") == "Host":
            # The host names the switch port it is wired to, in the same
            # normalised form _m_addHost uses for the Mermaid edge.
            #
            # No port is contributed from this side. The host's own interface is
            # already its sublabel, and the switch entry for the same link
            # supplies the switch port - which is the half that identifies the
            # link rather than the endpoint. Passing both put two names in one
            # label and truncation ate whichever came second.
            self._addLink(_deviceKey(item), self._switchForLink(item.get("Link"), orderlist), None, item.get("Vlan"))
            return
        node = item.get("Node", "")
        # PeerHost names the host on the far end of this port.
        if item.get("PeerHost"):
            self._addLink(node, item["PeerHost"], item.get("Name"), item.get("Vlan"))
        # Peer names a port URN; the device owning that port is the far end.
        peer = item.get("Peer")
        if _real(peer) and peer in self.portindex:
            self._addLink(node, self.portindex[peer], item.get("Name"), item.get("Vlan"))

    @staticmethod
    def _switchForLink(link, orderlist):
        """Resolve a host's Link back to the switch device that owns it.

        Link is _processName(f'{Node}_{Name}'), so it is matched by rebuilding
        the same string per switch entry rather than by parsing it apart - the
        normalisation is lossy and not reversible.
        """
        if not link:
            return ""
        for other in orderlist:
            if other.get("Type") != "Switch":
                continue
            if _processName(f'{other.get("Node", "")}_{other.get("Name", "")}') == link:
                return other.get("Node", "")
        return ""

    def neighbours(self, key):
        """Device keys linked to this one."""
        out = []
        for keya, keyb in self.links:
            if keya == key:
                out.append(keyb)
            elif keyb == key:
                out.append(keya)
        return out

    def hostsOf(self, key):
        """Hosts attached to this switch, in first-seen order."""
        linked = set(self.neighbours(key))
        return [k for k in self.order if k in linked and self.devices[k]["type"] == "Host"]

    def switches(self):
        """Switch device keys, in first-seen order."""
        return [k for k in self.order if self.devices[k]["type"] == "Switch"]


def _spineSegments(model):
    """Switches ordered into left-to-right runs, one run per connected piece.

    A manifest is not always one connected chain. A path crossing a domain that
    does not expose its internals - ESnet is the usual one - arrives as two
    runs with no link between them, because the hop joining them was never in
    the manifest to begin with. They are laid out as separate runs with a blank
    column between, rather than joined by an edge nothing reported.
    """
    switches = model.switches()
    remaining = list(switches)
    segments = []
    while remaining:
        # Seed on a run end where there is one, so a chain is walked along its
        # length instead of outward from the middle.
        seed = remaining[0]
        for key in remaining:
            degree = len([n for n in model.neighbours(key) if model.devices[n]["type"] == "Switch"])
            if degree <= 1:
                seed = key
                break
        segment = []
        stack = [seed]
        seen = set()
        while stack:
            key = stack.pop()
            if key in seen or key not in remaining:
                continue
            seen.add(key)
            segment.append(key)
            # First-seen order among the neighbours, reversed so the stack pops
            # them back in that order.
            nbrs = [n for n in switches if n in model.neighbours(key) and model.devices[n]["type"] == "Switch"]
            stack.extend(reversed([n for n in nbrs if n not in seen]))
        segments.append(segment)
        remaining = [k for k in remaining if k not in seen]
    return _orientSegments(model, segments)


def _orientSegments(model, segments):
    """Order and flip runs so a site split across a gap stays in one place.

    The ESnet case is why this exists. A path entering ESnet at one router and
    leaving at another arrives as two runs, each ending on an ESnet device,
    with no link between them because the transit hop was never in the
    manifest. Laid out in discovery order the two ESnet routers can land at
    opposite ends of the canvas, and the region wrapping them then stretches
    across every site in between. Flipping the next run so its ESnet end faces
    the previous one puts them side by side, which is both where they belong
    and what keeps the region a single tight box.

    The first run has to be oriented too, which is less obvious. Each run is
    walked from an end, and which end is whichever the seed search reached
    first - so the shared site can just as easily come out at the head of run
    one as at its tail. Then no later run faces it, every flip below falls
    through to the default, and the two routers sit at opposite ends with a
    long edge between them that the renderer rejects outright for crossing the
    devices in between. The real SDSC-to-FNAL reservations are this shape:
    reversed, run one ends on ESnet, the FNAL run faces it, and the pair
    becomes the adjacent-with-a-gap case everything downstream expects.
    """
    if len(segments) < 2:
        return segments
    first = segments[0]
    # Only flip to gain a neighbour that was not already there: if the tail
    # site is matched by some other run, the orientation is already the one
    # that pairs up, and reversing it would just read the path backwards.
    if len(first) > 1:
        endsites = {model.devices[seg[0]]["site"] for seg in segments[1:]} | {model.devices[seg[-1]]["site"] for seg in segments[1:]}
        if model.devices[first[-1]]["site"] not in endsites and model.devices[first[0]]["site"] in endsites:
            first = list(reversed(first))
    ordered = [first]
    pool = list(segments[1:])
    while pool:
        tailsite = model.devices[ordered[-1][-1]]["site"]
        choice, flip = pool[0], False
        for segment in pool:
            if model.devices[segment[0]]["site"] == tailsite:
                choice, flip = segment, False
                break
            if model.devices[segment[-1]]["site"] == tailsite:
                choice, flip = segment, True
                break
        pool.remove(choice)
        ordered.append(list(reversed(choice)) if flip else choice)
    return ordered


def placeDevices(model):
    """Assign every device a (row, col) cell.

    Returns (placement, dropped): placement maps device key -> (row, col),
    dropped lists host keys that did not fit. A switch gets at most
    MAX_HOSTS_PER_SWITCH vertical neighbours, because a third host has nowhere
    to go that is still adjacent to it, and an edge that is not between
    adjacent cells routes across whatever sits in between. Dropped hosts are
    reported to the caller and named in a dashboard warning - the Mermaid panel
    beside this one still shows every one of them.
    """
    placement = {}
    dropped = []
    col = 0
    for segment in _spineSegments(model):
        for key in segment:
            placement[key] = (ROW_SPINE, col)
            hosts = model.hostsOf(key)
            for index, hostkey in enumerate(hosts):
                if hostkey in placement:
                    continue
                if index >= MAX_HOSTS_PER_SWITCH:
                    dropped.append(hostkey)
                    continue
                placement[hostkey] = (ROW_HOST_UP if index == 0 else ROW_HOST_DOWN, col)
            col += 1
        # Blank column between runs, so a break in the manifest reads as a
        # break rather than as two devices that happen not to be joined.
        col += 1
    # Hosts attached to nothing still belong on the canvas.
    for key in model.order:
        if key in placement or key in dropped:
            continue
        placement[key] = (ROW_SPINE, col)
        col += 1
    return _compactRows(placement), dropped


def _compactRows(placement):
    """Close up rows nothing was placed in.

    The three rows are reserved before it is known whether they are needed, and
    an all-switch path - every BGP reservation is one - uses only the spine.
    Left as-is that renders a band of empty canvas above and below the diagram,
    which in a Grafana panel is height the topology does not get to use.
    """
    used = sorted({row for row, _col in placement.values()})
    remap = {row: index for index, row in enumerate(used)}
    return {key: (remap[row], col) for key, (row, col) in placement.items()}


def _pos(row, col):
    """Top-left corner of a cell, in diagram units."""
    return [ORIGIN_X + col * (CELL_W + GAP_X), ORIGIN_Y + row * (CELL_H + GAP_Y)]


def _viewBox(placement):
    """A canvas that contains every placed cell, with room for the cards."""
    maxcol = max((col for _row, col in placement.values()), default=0)
    maxrow = max((row for row, _col in placement.values()), default=0)
    width = ORIGIN_X + maxcol * (CELL_W + GAP_X) + CELL_W + ORIGIN_X
    height = ORIGIN_Y + maxrow * (CELL_H + GAP_Y) + CELL_H + BOTTOM_PAD
    return [max(width, VIEWBOX_MIN_W), max(height, VIEWBOX_MIN_H)]


def _components(model, placement, ids, budget):
    """One component per placed device.

    Hosts are the ends of the transfer and switches are what it crosses, so
    they take archify's "external" and "cloud" types respectively - the same
    distinction the topology recipe draws between endpoints and transit.
    """
    out = []
    for key in model.order:
        if key not in placement:
            continue
        device = model.devices[key]
        row, col = placement[key]
        if device["joint"]:
            label = device["joint"].split("|")[0]
        elif device["type"] == "Host":
            label = _hostlabel(key)
        else:
            label = device["name"]
        component = {
            "id": ids[key],
            "type": "external" if device["type"] == "Host" else "cloud",
            "label": _fit(label, budget["label"]),
            "pos": _pos(row, col),
            "size": [CELL_W, CELL_H],
        }
        if device["ports"]:
            component["sublabel"] = _fit(", ".join(device["ports"]), budget["sublabel"])
        if device["vlans"]:
            component["tag"] = _fit("VLAN " + ", ".join(device["vlans"]), budget["sublabel"])
        out.append(component)
    return out


def _routeHints(cella, cellb):
    """Endpoint sides and a label anchor for one edge, from the two cells.

    Only grid-adjacent cells get hints. Everything else is left to automatic
    routing, because a truthful side is one the geometry actually supports and
    asserting "right to left" across an intervening column would send the route
    straight through whatever sits there.

    Returned sides are stated from a's point of view; the caller emits them in
    whichever direction it writes the connection.
    """
    (rowa, cola), (rowb, colb) = cella, cellb
    if cola == colb and abs(rowa - rowb) == 1:
        top, bottom = (rowa, rowb) if rowa < rowb else (rowb, rowa)
        anchor = [
            ORIGIN_X + cola * (CELL_W + GAP_X) + CELL_W / 2,
            ORIGIN_Y + top * (CELL_H + GAP_Y) + CELL_H + GAP_Y / 2,
        ]
        sides = ("bottom", "top") if rowa < rowb else ("top", "bottom")
        return sides, anchor, bottom
    if rowa == rowb and abs(cola - colb) == 1:
        left = min(cola, colb)
        anchor = [
            ORIGIN_X + left * (CELL_W + GAP_X) + CELL_W + GAP_X / 2,
            ORIGIN_Y + rowa * (CELL_H + GAP_Y) + CELL_H / 2,
        ]
        sides = ("right", "left") if cola < colb else ("left", "right")
        return sides, anchor, left
    return None, None, None


def _orientLink(model, placement, pair):
    """Which end of a link the arrow should start from.

    A reservation is bidirectional and archify draws every connection as an
    arrow, so the direction is going to say something whether or not it is
    meant to. Left as the sorted pair it said something arbitrary - an arrow
    pointing whichever way the device names happened to sort. These two rules
    at least make it consistent: traffic enters the network at a host, and the
    path then reads left to right.
    """
    keya, keyb = pair
    types = (model.devices[keya]["type"], model.devices[keyb]["type"])
    if types == ("Switch", "Host"):
        return keyb, keya
    if types == ("Host", "Switch"):
        return keya, keyb
    return (keya, keyb) if placement[keya][1] <= placement[keyb][1] else (keyb, keya)


def _connections(model, placement, ids, budget):
    """One connection per device link, both endpoints placed.

    Labelled by what tells the two edge kinds apart at a glance: a host to
    switch edge is about which port the host landed on, a switch to switch edge
    is about which VLAN the reservation is riding.

    Sides and label anchors are stated explicitly wherever the two cells are
    adjacent. Left to automatic placement, a switch carrying three edges had
    one of its labels land inside its own box - the renderer rejects that, and
    it is avoidable here because the corridor each edge runs through is known
    exactly.
    """
    out = []
    for pair, link in model.links.items():
        if any(key not in placement for key in pair):
            continue
        keya, keyb = _orientLink(model, placement, pair)
        hosts = [k for k in pair if model.devices[k]["type"] == "Host"]
        if hosts:
            text = ", ".join(link["ports"])
        else:
            text = "VLAN " + ", ".join(link["vlans"]) if link["vlans"] else ""
        conn = {
            "id": f"{ids[keya]}-{ids[keyb]}",
            "from": ids[keya],
            "to": ids[keyb],
            "variant": "default" if hosts else "emphasis",
        }
        label = _fit(text, budget["conn"])
        # An empty string is not a valid label, and a label the renderer would
        # reject is worse than no label at all.
        if label:
            conn["label"] = label
        sides, anchor, _ = _routeHints(placement[keya], placement[keyb])
        if sides:
            conn["fromSide"], conn["toSide"] = sides
            if label:
                conn["labelAt"] = anchor
        out.append(conn)
    return out


def _transitConnections(model, placement, ids, budget):
    """Dashed edges across the gaps a domain's own transit leaves behind.

    A domain that does not expose its internals - ESnet and Internet2 are the
    usual ones - reports the two ports the path enters and leaves on and
    nothing in between, so the spine arrives as two runs with no link joining
    them. Drawing nothing there is accurate about the manifest and misleading
    about the path: the reservation does cross from one of those routers to the
    other, and a reader comparing this with the Mermaid panel sees a circuit
    that appears to stop halfway. Mermaid gets the continuity for free, because
    it emits one subgraph per port and same-named subgraphs merge, so both
    routers end up inside one domain box.

    So the edge is drawn, and marked for what it is: dashed, and labelled
    rather than carrying a VLAN it was never told. Only between two switches of
    the same site that the layout has already placed either side of one gap
    column, which is where _orientSegments puts the facing ends of two runs -
    never between sites, and never where the manifest did report a link.
    """
    out = []
    spine = sorted(
        (key for key in model.switches() if key in placement),
        key=lambda key: placement[key][1],
    )
    # zip over the offset slice, not itertools.pairwise: the image runs
    # python 3.9 and pairwise arrived in 3.10, so ruff's RUF007 suggestion
    # here would be an ImportError in production.
    for keya, keyb in zip(spine, spine[1:]):
        if model.devices[keya]["site"] != model.devices[keyb]["site"]:
            continue
        if tuple(sorted((keya, keyb))) in model.links:
            continue
        # Adjacent cells are a layout the renderer routes cleanly; anything
        # wider means another device sits between them and the edge would run
        # across it.
        if placement[keyb][1] - placement[keya][1] != 2:
            continue
        conn = {
            "id": f"{ids[keya]}-{ids[keyb]}-transit",
            "from": ids[keya],
            "to": ids[keyb],
            "variant": "dashed",
        }
        label = _fit("transit", budget["conn"])
        if label:
            conn["label"] = label
        sides, anchor, _ = _routeHints(placement[keya], placement[keyb])
        if sides:
            conn["fromSide"], conn["toSide"] = sides
            if label:
                conn["labelAt"] = anchor
        out.append(conn)
    return out


def _boundaries(model, placement, ids):
    """One region per contiguous run of columns a site owns.

    This is the Mermaid subgraph, kept. Grouped by column run rather than by
    site name, because a region's box is the bounding box of whatever it
    wraps: a site appearing at two separated columns would produce one box
    spanning everything between them, swallowing the sites in the middle.
    Two boxes carrying the same label is the honest rendering of a site the
    path visits twice.
    """
    columns = {}
    for key in model.order:
        if key not in placement:
            continue
        columns.setdefault(placement[key][1], []).append(key)
    out = []
    runsite, runmembers = None, []
    for col in sorted(columns):
        site = model.devices[columns[col][0]]["site"]
        # A column holds a switch and its hosts, which are always the same
        # site, so the first device's site names the whole column.
        if site != runsite:
            if runsite and runmembers:
                out.append({"kind": "region", "label": _fit(runsite, SUBLABEL_MAX), "wraps": runmembers})
            runsite, runmembers = site, []
        runmembers.extend(ids[key] for key in columns[col])
    if runsite and runmembers:
        out.append({"kind": "region", "label": _fit(runsite, SUBLABEL_MAX), "wraps": runmembers})
    return out


def _views(model, placement, ids):
    """Guided focus views: the whole path, then a view per site.

    Capped at the schema's five. Sites are taken in path order, so the four
    that make the cut are the four the transfer reaches first rather than
    whichever four a dict happened to yield.
    """
    placed = [k for k in model.order if k in placement]
    if not placed:
        return []
    views = [
        {
            "id": "full-path",
            "label": "Full path",
            "focus": [ids[k] for k in placed],
            "note": "Every device the reservation crosses, end to end.",
        }
    ]
    seen = []
    for key in placed:
        site = model.devices[key]["site"]
        if site and site not in seen:
            seen.append(site)
    for index, site in enumerate(seen[:4]):
        members = [ids[k] for k in placed if model.devices[k]["site"] == site]
        views.append(
            {
                "id": f"site-{index}",
                "label": _fit(site, 48),
                "focus": members,
                "note": _fit(f"Devices {site} contributes to this path.", 140),
            }
        )
    return views


def _intentConnections(instance):
    """Every connection block across the instance's intents."""
    for intent in (instance or {}).get("intents", []) or []:
        yield from intent.get("json", {}).get("data", {}).get("connections", []) or []


def _reservationCard(instance, model):
    """Bandwidth, service type and VLANs - what was actually asked for."""
    items = []
    for conn in _intentConnections(instance):
        service = conn.get("name") or (instance or {}).get("alias", "")
        capacity = conn.get("bandwidth", {}).get("capacity")
        qos = conn.get("bandwidth", {}).get("qos_class")
        if capacity:
            items.append(_fit(f"{service}: {capacity} Mbps {qos or ''}".strip(), 90))
    servicetype = ""
    for intent in (instance or {}).get("intents", []) or []:
        servicetype = intent.get("json", {}).get("data", {}).get("type", "")
        if servicetype:
            break
    if servicetype:
        items.insert(0, _fit(servicetype, 90))
    vlans = []
    for device in model.devices.values():
        for vlan in device["vlans"]:
            if vlan not in vlans:
                vlans.append(vlan)
    if vlans:
        items.append(_fit("VLAN " + ", ".join(vlans), 90))
    return {"dot": "cyan", "title": "Reservation", "items": items} if items else None


def _endpointCard(model, placement):
    """Per host: interface, addresses and MAC - the L2/L3 detail off the nodes."""
    items = []
    for key in model.order:
        if key not in placement or model.devices[key]["type"] != "Host":
            continue
        device = model.devices[key]
        detail = list(device["ports"]) + list(device["ips"]) + list(device["macs"])
        items.append(_fit(f'{device["name"]}: {" · ".join(detail)}' if detail else device["name"], 90))
    return {"dot": "emerald", "title": "Endpoints", "items": items} if items else None


def _pathCard(model, placement):
    """Per switch: the ports this reservation uses on it."""
    items = []
    for key in model.order:
        if key not in placement or model.devices[key]["type"] != "Switch":
            continue
        device = model.devices[key]
        items.append(_fit(f'{device["site"]} {device["name"]}: {", ".join(device["ports"])}' if device["ports"] else f'{device["site"]} {device["name"]}', 90))
    return {"dot": "orange", "title": "Path", "items": items} if items else None


def _bgpCard(instance):
    """Route-map prefixes, where the intent asked for BGP peering.

    Read off the same terminals the Mermaid BGP nodes come from, so the two
    panels cannot disagree about what was requested.
    """
    items = []
    for conn in _intentConnections(instance):
        for terminal in conn.get("terminals", []) or []:
            uri = terminal.get("uri", "")
            for ipkey in ("ipv4_prefix_list", "ipv6_prefix_list"):
                if terminal.get(ipkey):
                    items.append(_fit(f'{uri.split(":")[-1] or uri}: {terminal[ipkey]}', 90))
    return {"dot": "rose", "title": "BGP", "items": items} if items else None


def _cards(instance, model, placement, dropped):
    """The numbers, out of the picture and beside it."""
    out = []
    for card in (_reservationCard(instance, model), _endpointCard(model, placement), _pathCard(model, placement), _bgpCard(instance)):
        if card:
            out.append(card)
    if dropped:
        out.append(
            {
                "dot": "rose",
                "title": "Not shown",
                "items": [_fit(f"{_shortname(key)} - see the Mermaid panel", 90) for key in dropped],
            }
        )
    return out


def buildIR(orderlist, instance, **kwargs):
    """The archify architecture IR for one reservation.

    Returns (ir, report). report carries what the caller has to tell the
    operator about: hosts that did not fit, and the device count, so an empty
    or trivial diagram can be recognised without re-deriving the model.

    labelmax/sublabelmax/connlabelmax tighten the text budgets below the
    defaults. The caller uses them as one rung of its fallback ladder, for the
    case where the renderer rejects a layout on text it cannot shrink far
    enough - so a device with an unusually long name costs its own name rather
    than the whole diagram.
    """
    budget = {
        "label": int(kwargs.get("labelmax", LABEL_MAX)),
        "sublabel": int(kwargs.get("sublabelmax", SUBLABEL_MAX)),
        "conn": int(kwargs.get("connlabelmax", CONN_LABEL_MAX)),
    }
    model = DeviceModel(orderlist)
    placement, dropped = placeDevices(model)
    used = {}
    ids = {key: _componentId(key, used) for key in model.order}
    components = _components(model, placement, ids, budget)
    connections = _connections(model, placement, ids, budget)
    transit = _transitConnections(model, placement, ids, budget)
    connections += transit
    report = {
        "devices": len(components),
        "dropped": [_shortname(key) for key in dropped],
        # Reported apart from the links the manifest actually carried, so a
        # caller can tell a path that was fully described from one this had to
        # bridge.
        "links": len(connections),
        "transit": len(transit),
    }
    if not components:
        return None, report
    ir = {
        "schema_version": 1,
        "diagram_type": "architecture",
        "meta": {
            "title": _fit(kwargs.get("title", "End-to-End Flow Topology"), 90),
            "subtitle": _fit(kwargs.get("subtitle", ""), 120),
            "output": kwargs.get("output", "topology.html"),
            "quality_profile": kwargs.get("quality", "standard"),
            "viewBox": _viewBox(placement),
            "views": _views(model, placement, ids),
        },
        "components": components,
        "boundaries": _boundaries(model, placement, ids),
        "connections": connections,
        "cards": _cards(instance, model, placement, dropped),
    }
    if not ir["meta"]["subtitle"]:
        del ir["meta"]["subtitle"]
    return ir, report
