// Rebuild from the DBML source; never maintain a second hand-written schema.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {Parser} = require('@dbml/core');
const {instance} = require('@viz-js/viz');
const sharp = require('sharp');

async function main() {
  const directory = path.resolve(__dirname, '..');
  const sourcePath = path.join(directory, '2. 초기 DB 설계, DBML(dbdiagram.io).txt');
  const source = fs.readFileSync(sourcePath, 'utf8');
  const start = source.search(/^Table USER\s*\{/m);
  assert(start >= 0, 'DBML start not found');
  const dbml = source.slice(start);
  const database = Parser.parse(dbml, 'dbml');
  // Run both DBML compilers to catch syntax / reference errors independently.
  const v2 = Parser.parse(dbml, 'dbmlv2');
  const schema = database.schemas[0];
  const tables = schema.tables.map(table => ({
    name: table.name,
    fields: table.fields.map(field => ({
      name: field.name, type: field.type.type_name,
      pk: !!field.pk, required: !!(field.pk || field.not_null), unique: !!field.unique,
      default: field.dbdefault || null, note: field.note || null,
    })),
    indexes: table.indexes.map(index => ({
      unique: !!index.unique, columns: index.columns.map(column => column.value),
    })),
  }));
  const refs = schema.refs.map((ref, i) => {
    const child = ref.endpoints.find(endpoint => endpoint.relation === '*');
    const parent = ref.endpoints.find(endpoint => endpoint.relation === '1');
    assert(child && parent, 'This renderer expects many-to-one foreign keys');
    assert.equal(child.fieldNames.length, 1);
    assert.equal(parent.fieldNames.length, 1);
    return {id: `R${String(i + 1).padStart(2, '0')}`,
      childTable: child.tableName, childField: child.fieldNames[0],
      parentTable: parent.tableName, parentField: parent.fieldNames[0]};
  });
  const fieldCount = tables.reduce((sum, table) => sum + table.fields.length, 0);
  assert.equal(tables.length, v2.schemas[0].tables.length);
  assert.equal(fieldCount, v2.schemas[0].tables.reduce((n, t) => n + t.fields.length, 0));
  assert.equal(refs.length, v2.schemas[0].refs.length);
  const rawFields = [...dbml.matchAll(/^  (\w+)\s+(\w+(?:\([^\n]*?\))?)(?:\s+\[[^\n]*\])?\s*$/gm)];
  assert.equal(rawFields.length, fieldCount, 'Raw source field count differs');
  assert.equal([...dbml.matchAll(/ref:\s*>/g)].length, refs.length);
  for (const ref of refs) {
    const parent = tables.find(t => t.name === ref.parentTable)?.fields.find(f => f.name === ref.parentField);
    const child = tables.find(t => t.name === ref.childTable)?.fields.find(f => f.name === ref.childField);
    assert(parent && child, `Invalid endpoint: ${ref.id}`);
    assert(parent.pk || parent.unique, `Nonunique FK target: ${ref.id}`);
    assert.equal(child.type, parent.type, `FK type mismatch: ${ref.id}`);
  }

  const xml = text => String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
  const quote = text => JSON.stringify(String(text));
  const palette = {USER:'#0f4c75', PROJECT:'#0f4c75', CHAT_CONVERSATION:'#0f4c75', CHAT_MESSAGE:'#0f4c75',
    PROJECT_RUN:'#315a9c', TASK:'#315a9c', AGENT_EXECUTION:'#315a9c', ARTIFACT:'#315a9c',
    AGENT:'#695093', MODEL_INFO:'#695093', AGENT_MODEL:'#695093', MODEL_USAGE:'#695093', PROMPT_HISTORY:'#695093',
    EXECUTION_EVENT:'#397269', NOTIFICATION:'#397269', INSTRUCTION:'#397269', QUALITY_CRITERION:'#397269', REFLECTION_REPORT:'#397269'};
  let dot = `digraph ERD {
    graph [rankdir=RL, bgcolor="#f5f8fc", pad=0.45, nodesep=0.60, ranksep=1.35,
      splines=spline, outputorder=edgesfirst, fontname="Arial", fontsize=20,
      labelloc=t, labeljust=l, label="Second Brain | Backend target schema\n${tables.length} tables   /   ${fieldCount} fields   /   ${refs.length} foreign keys\n\nPK = primary key     FK = foreign key     UQ = unique     * = NOT NULL (including PK)     ? = nullable\nArrows: FK field -> referenced PK field. Each child has 1 parent (*) or 0..1 parent (?). Each parent has 0..N children.\nIndexes, types and defaults are copied from DBML. Target design only; not a live database migration.\n "];
    node [shape=plain, fontname="Arial", fontsize=12];
    edge [color="#94a3b8", penwidth=1.15, arrowsize=0.65, fontname="Arial", fontsize=10];
  `;
  for (const table of tables) {
    const color = palette[table.name] || '#6c7162';
    let label = `<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7" COLOR="#cbd5e1" BGCOLOR="white">`;
    label += `<TR><TD COLSPAN="4" BGCOLOR="${color}" ALIGN="LEFT"><FONT COLOR="white" POINT-SIZE="16"><B>${xml(table.name)}</B></FONT></TD></TR>`;
    label += '<TR><TD BGCOLOR="#edf2f7">Key</TD><TD BGCOLOR="#edf2f7" ALIGN="LEFT">Field</TD><TD BGCOLOR="#edf2f7" ALIGN="LEFT">Type / Default</TD><TD BGCOLOR="#edf2f7">Null</TD></TR>';
    for (const field of table.fields) {
      const foreign = refs.filter(ref => ref.childTable === table.name && ref.childField === field.name);
      const key = [field.pk && 'PK', foreign.length && 'FK', field.unique && 'UQ'].filter(Boolean).join(' ');
      const def = field.default ? ` = ${field.default.type === 'string' ? `'${field.default.value}'` : field.default.value}` : '';
      label += `<TR><TD PORT="${field.name}_left"><FONT COLOR="${color}">${key || '-'}</FONT></TD><TD ALIGN="LEFT">${xml(field.name)}</TD><TD ALIGN="LEFT"><FONT COLOR="#475569">${xml(field.type + def)}</FONT></TD><TD PORT="${field.name}_right">${field.required ? '*' : '?'}</TD></TR>`;
    }
    for (const index of table.indexes) {
      label += `<TR><TD COLSPAN="4" ALIGN="LEFT" BGCOLOR="#f1f5f9"><FONT POINT-SIZE="11">${index.unique ? 'UQ' : 'INDEX'} (${xml(index.columns.join(', '))})</FONT></TD></TR>`;
    }
    label += '</TABLE>';
    dot += `${quote(table.name)} [id=${quote('table_' + table.name)}, label=<${label}>];\n`;
  }
  for (const ref of refs) {
    const mapping = `${ref.childTable}.${ref.childField} -> ${ref.parentTable}.${ref.parentField}`;
    const self = ref.childTable === ref.parentTable;
    const parentSide = self ? 'w' : 'e';
    const parentPort = ref.parentField + (self ? '_left' : '_right');
    dot += `${quote(ref.childTable)}:${quote(ref.childField + '_left')}:w -> ${quote(ref.parentTable)}:${quote(parentPort)}:${parentSide} [id=${quote('fk_' + ref.id)}, tooltip=${quote(mapping)}];\n`;
  }
  dot += '}';
  fs.writeFileSync(path.join(directory, '../tmp/erd.dot'), dot);
  const viz = await instance();
  const result = viz.render(dot, {format: 'svg', engine: 'dot'});
  assert.equal(result.status, 'success', JSON.stringify(result.errors));
  assert.deepEqual(result.errors, [], 'Graphviz warnings/errors must be resolved');
  const manifest = {source: path.basename(sourcePath),
    sourceSha256: crypto.createHash('sha256').update(source).digest('hex'),
    tableCount: tables.length, fieldCount, foreignKeyCount: refs.length, tables, refs};
  let svg = result.output;
  svg = svg.replace(/(<svg\b[^>]*>)/, `$1\n<metadata id="dbml-source">${xml(JSON.stringify(manifest))}</metadata>`);
  const svgPath = path.join(directory, 'erd.svg');
  fs.writeFileSync(svgPath, svg);
  const audit = path.join(directory, 'erd-tools/validation.json');
  fs.writeFileSync(audit, JSON.stringify({
    sourceSha256: manifest.sourceSha256, tableCount: tables.length, fieldCount,
    foreignKeyCount: refs.length, compilerChecks: ['dbml', 'dbmlv2'],
    graphvizWarnings: result.errors, refs,
  }, null, 2) + '\n');
  // Preview only, deliberately outside the deliverable folder.
  const preview = path.join(directory, '../tmp/erd-preview.png');
  fs.mkdirSync(path.dirname(preview), {recursive: true});
  await sharp(Buffer.from(svg), {limitInputPixels:false}).resize({width:2400, withoutEnlargement:true}).png().toFile(preview);
  fs.writeFileSync(path.join(directory, '../tmp/erd.dot'), dot);
  console.log(JSON.stringify({svg:svgPath, preview, tables:tables.length, fields:fieldCount, foreignKeys:refs.length, bytes:Buffer.byteLength(svg)}));
}
main().catch(error => {console.error(error); process.exitCode = 1;});
