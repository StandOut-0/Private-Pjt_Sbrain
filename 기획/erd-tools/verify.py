"""Independently compare visible SVG rows and edge endpoints to the DBML text."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

directory = Path(__file__).resolve().parents[1]
source = (directory / '2. 초기 DB 설계, DBML(dbdiagram.io).txt').read_bytes()
dbml = source.decode('utf-8')
dbml = dbml[re.search(r'^Table USER\s*\{', dbml, re.M).start():]
svg = ET.parse(directory / 'erd.svg').getroot()
ns = {'s': 'http://www.w3.org/2000/svg'}
meta = json.loads(svg.find('s:metadata', ns).text)
assert meta['sourceSha256'] == hashlib.sha256(source).hexdigest()
nodes = {g.attrib['id'][6:]: g for g in svg.findall('.//s:g[@class="node"]', ns)}
edges = svg.findall('.//s:g[@class="edge"]', ns)
blocks = re.findall(r'^Table\s+(\w+)\s*\{(.*?)^\}', dbml, re.M | re.S)
assert set(nodes) == {name for name, _ in blocks}
relations = set()
count = 0
boxes = {}
row_positions = {}
for name, body in blocks:
    node = nodes[name]
    texts = node.findall('.//s:text', ns)
    points = [tuple(map(float, point.split(',')))
              for polygon in node.findall('.//s:polygon', ns)
              for point in polygon.attrib['points'].split()]
    boxes[name] = (min(x for x, y in points), min(y for x, y in points),
                   max(x for x, y in points), max(y for x, y in points))
    raw_fields = re.findall(r'^  (\w+)\s+(\w+(?:\([^\n]*?\))?)(?:\s+\[([^\n]*)\])?\s*$', body, re.M)
    manifest = next(table for table in meta['tables'] if table['name'] == name)
    assert len(raw_fields) == len(manifest['fields'])
    assert len(texts) == 5 + 4 * len(raw_fields) + len(manifest['indexes']), name
    assert texts[0].text == name
    for index, (field, datatype, settings) in enumerate(raw_fields):
        visible = [text.text for text in texts[5 + 4 * index:9 + 4 * index]]
        pk = bool(re.search(r'(^|,\s*)pk(\s*,|$)', settings))
        unique = bool(re.search(r'(^|,\s*)unique(\s*,|$)', settings))
        required = pk or bool(re.search(r'(^|,\s*)not null(\s*,|$)', settings))
        fk = re.search(r'ref:\s*>\s*(\w+)\.(\w+)', settings)
        keys = ' '.join(flag for flag, enabled in [('PK', pk), ('FK', fk), ('UQ', unique)] if enabled) or '-'
        default = re.search(r"default:\s*('[^']*'|[^,\]]+)", settings)
        rendered_type = datatype + (' = ' + default[1].strip() if default else '')
        assert visible == [keys, field, rendered_type, '*' if required else '?'], (name, field, visible)
        y = float(texts[6 + 4 * index].attrib['y'])
        row_positions[name, field] = y
        xmin, ymin, xmax, ymax = boxes[name]
        assert ymin < y < ymax
        if fk:
            relations.add((name, field, fk[1], fk[2]))
        count += 1
    visible_indexes = [text.text for text in texts[5 + 4 * len(raw_fields):]]
    raw_indexes = re.findall(r'^    \(([^)]+)\)(?:\s+\[([^\n]*)\])?', body, re.M)
    expected_indexes = [('UQ' if 'unique' in settings else 'INDEX') + ' (' + ', '.join(c.strip() for c in columns.split(',')) + ')'
                        for columns, settings in raw_indexes]
    assert visible_indexes == expected_indexes, name

seen = set()
for edge in edges:
    link = edge.find('.//s:a', ns)
    tooltip = link.attrib['{http://www.w3.org/1999/xlink}title']
    match = re.fullmatch(r'(\w+)\.(\w+) -> (\w+)\.(\w+)', tooltip)
    assert match, tooltip
    child, child_field, parent, parent_field = match.groups()
    relation = (child, child_field, parent, parent_field)
    assert relation not in seen
    seen.add(relation)
    path = edge.find('.//s:path', ns).attrib['d']
    start = re.match(r'M(-?[\d.]+),(-?[\d.]+)', path)
    x, y = map(float, start.groups())
    assert abs(y - row_positions[child, child_field]) < 6, relation
    assert abs(x - boxes[child][0]) < 4, relation
    arrow = edge.find('.//s:polygon', ns)
    arrow_points = [tuple(map(float, p.split(','))) for p in arrow.attrib['points'].split()]
    tipx, tipy = arrow_points[1]
    assert abs(tipy - row_positions[parent, parent_field]) < 6, relation
    expected_x = boxes[parent][0] if child == parent else boxes[parent][2]
    assert abs(tipx - expected_x) < 4, relation

assert relations == seen
assert len(edges) == len(relations) == meta['foreignKeyCount']
assert count == meta['fieldCount']
assert len(nodes) == meta['tableCount']
for a, box_a in boxes.items():
    for b, box_b in boxes.items():
        if a >= b:
            continue
        intersection_x = min(box_a[2], box_b[2]) - max(box_a[0], box_b[0])
        intersection_y = min(box_a[3], box_b[3]) - max(box_a[1], box_b[1])
        assert intersection_x <= 0 or intersection_y <= 0, ('overlapping tables', a, b)
audit_path = directory / 'erd-tools/validation.json'
audit = json.loads(audit_path.read_text(encoding='utf-8'))
assert audit['sourceSha256'] == meta['sourceSha256']
audit['svgChecks'] = {
    'visibleTableCount': len(nodes), 'visibleFieldCount': count, 'visibleForeignKeyCount': len(edges),
    'fieldsTypesDefaultsKeysNullabilityAndIndexesMatchSource': True,
    'allEdgeEndpointsMatchReferencedFieldRows': True,
    'noOverlappingTables': True,
    'sourceHashMatches': True,
}
audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'PASS: {len(nodes)} tables, {count} visible field rows, {len(edges)} FK edges, defaults, nullable flags, unique indexes, exact field-row endpoints, no table overlap, source hash.')
