"""rm-draw.py <out.rm> <layout.json>
Draws boxes, arrows and single-stroke (Hershey) text as real pen strokes into a
reMarkable v6 page. Layout coords: x in [-700, 700] (0 = page centre), y in [0, 1870].
layout.json: {"items": [{"t":"text","x":..,"y":..,"s":size,"text":".."},
                        {"t":"box","x":..,"y":..,"w":..,"h":..},
                        {"t":"line","pts":[[x,y],...]},
                        {"t":"arrow","x1":..,"y1":..,"x2":..,"y2":..}]}
"""
import json, math, sys
from uuid import uuid4
from HersheyFonts import HersheyFonts
from rmscene import scene_items as si
from rmscene.crdt_sequence import CrdtSequenceItem
from rmscene.tagged_block_common import CrdtId, LwwValue
from rmscene.scene_stream import (AuthorIdsBlock, MigrationInfoBlock, PageInfoBlock,
    SceneTreeBlock, TreeNodeBlock, SceneGroupItemBlock, SceneLineItemBlock, write_blocks)

font = HersheyFonts(); font.load_default_font("futural")
ASCII = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss", "–": "-", "→": "->"})

def text_strokes(text, x, y, size):
    font.normalize_rendering(size)  # cap height ~ size, y grows upwards in Hershey
    for stroke in font.strokes_for_text(text.translate(ASCII)):
        yield [(x + px, y - py) for px, py in stroke]

def strokes(item):
    t = item["t"]
    if t == "text":
        yield from text_strokes(item["text"], item["x"], item["y"], item.get("s", 22))
    elif t == "box":
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        yield [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    elif t == "line":
        yield [tuple(p) for p in item["pts"]]
    elif t == "arrow":
        x1, y1, x2, y2 = item["x1"], item["y1"], item["x2"], item["y2"]
        yield [(x1, y1), (x2, y2)]
        a = math.atan2(y2 - y1, x2 - x1)
        for d in (2.6, -2.6):
            yield [(x2 + 18 * math.cos(a + d), y2 + 18 * math.sin(a + d)), (x2, y2)]

def densify(pts, step=4.0):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(1, n + 1)]
    return out

def blocks(layout):
    yield AuthorIdsBlock(author_uuids={1: uuid4()})
    yield MigrationInfoBlock(migration_id=CrdtId(1, 1), is_device=True)
    yield PageInfoBlock(loads_count=1, merges_count=0, text_chars_count=0, text_lines_count=0)
    yield SceneTreeBlock(tree_id=CrdtId(0, 11), node_id=CrdtId(0, 0), is_update=True, parent_id=CrdtId(0, 1))
    yield TreeNodeBlock(si.Group(node_id=CrdtId(0, 1)))
    yield TreeNodeBlock(si.Group(node_id=CrdtId(0, 11), label=LwwValue(timestamp=CrdtId(0, 12), value="Layer 1")))
    yield SceneGroupItemBlock(parent_id=CrdtId(0, 1), item=CrdtSequenceItem(
        item_id=CrdtId(0, 13), left_id=CrdtId(0, 0), right_id=CrdtId(0, 0), deleted_length=0, value=CrdtId(0, 11)))
    left, n = CrdtId(0, 0), 0
    for item in layout["items"]:
        for pts in strokes(item):
            if len(pts) < 2:
                continue
            n += 1
            line = si.Line(color=si.PenColor.BLACK, tool=si.Pen.FINELINER_2,
                           points=[si.Point(x=px, y=py, speed=0, direction=0, width=item.get("wd", 3), pressure=100)
                                   for px, py in densify(pts)],
                           thickness_scale=item.get("th", 2.0), starting_length=0.0)
            iid = CrdtId(2, 100 + n)
            yield SceneLineItemBlock(parent_id=CrdtId(0, 11), item=CrdtSequenceItem(
                item_id=iid, left_id=left, right_id=CrdtId(0, 0), deleted_length=0, value=line))
            left = iid
    print(f"strokes={n}", file=sys.stderr)

if __name__ == "__main__":
    out, layout = sys.argv[1], json.load(open(sys.argv[2]))
    with open(out, "wb") as f:
        write_blocks(f, blocks(layout))
