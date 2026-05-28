const fs = require('fs');
const path = require('path');

const RES_DIR = 'C:\\Programmieren\\wizardrytranslation\\extracted\\packdata_resources';
const CLASS_FILE = 'C:\\Programmieren\\wizardrytranslation\\dumps\\resource_classification.json';
const OUT_TXT = 'C:\\Programmieren\\wizardrytranslation\\dumps\\msg_frequency_analysis.txt';
const OUT_JSON = 'C:\\Programmieren\\wizardrytranslation\\dumps\\glyph_frequency.json';
const FINDINGS = 'C:\\Programmieren\\wizardrytranslation\\runs\\CLAUDE-RUNS\\RUN-20260522-1932-initial-recon\\subagents\\recon22-msg-freq\\FINDINGS.md';

const classification = JSON.parse(fs.readFileSync(CLASS_FILE, 'utf-8'));
const msgIndices = classification.msg_resource_indices;
console.log(`MSG resource indices count: ${msgIndices.length}`);

// Build file list once
const allFiles = fs.readdirSync(RES_DIR);
function findResourceFile(idx) {
    const prefix = String(idx).padStart(4, '0') + '_';
    for (const fn of allFiles) {
        if (fn.startsWith(prefix) && fn.endsWith('.bin')) {
            return path.join(RES_DIR, fn);
        }
    }
    return null;
}

function parseMsgResource(filepath) {
    const buf = fs.readFileSync(filepath);
    const len = Math.floor(buf.length / 2);
    const values = [];
    for (let i = 0; i < len; i++) {
        values.push(buf.readUInt16BE(i * 2));
    }
    return values;
}

// Global counters
const glyphFreq = new Map();
const controlCodes = new Map();
const CC_SET = new Set([0xFFFF, 0xFFFE, 0xFFD2, 0xFFD3, 0xFFE0, 0xFFE1]);
for (const c of CC_SET) controlCodes.set(c, 0);

let totalMessages = 0;
let totalGlyphs = 0;
const uniqueGlyphs = new Set();
const messagesPerResource = new Map();
const allMessageLengths = []; // {len, resIdx, msgIdx}
let speakerTagCount = 0;
let resourcesProcessed = 0;
const resourceStats = [];

for (const ri of msgIndices) {
    const fp = findResourceFile(ri);
    if (!fp) {
        console.log(`  WARNING: No file for index ${ri}`);
        continue;
    }
    const vals = parseMsgResource(fp);

    // Count control codes
    for (const v of vals) {
        if (CC_SET.has(v)) {
            controlCodes.set(v, (controlCodes.get(v) || 0) + 1);
        }
    }

    // Split on 0xFFFF
    const messages = [];
    let cur = [];
    for (const v of vals) {
        if (v === 0xFFFF) {
            if (cur.length > 0) messages.push(cur);
            cur = [];
        } else {
            cur.push(v);
        }
    }
    if (cur.length > 0) messages.push(cur);

    const mc = messages.length;
    totalMessages += mc;
    messagesPerResource.set(ri, mc);
    resourcesProcessed++;

    const resUnique = new Set();
    let resGlyphs = 0;

    for (let mi = 0; mi < messages.length; mi++) {
        const msg = messages[mi];
        allMessageLengths.push({ len: msg.length, resIdx: ri, msgIdx: mi });

        if (msg.length >= 2 && msg[0] === 0x011e && msg[1] === 0x0247) {
            speakerTagCount++;
        }

        for (const v of msg) {
            if (v < 0xFF00) {
                glyphFreq.set(v, (glyphFreq.get(v) || 0) + 1);
                uniqueGlyphs.add(v);
                resUnique.add(v);
                resGlyphs++;
                totalGlyphs++;
            }
        }
    }
    resourceStats.push({ idx: ri, messages: mc, glyphs: resGlyphs, unique: resUnique.size, file: path.basename(fp) });
}

// Sort message lengths
allMessageLengths.sort((a, b) => b.len - a.len);

// Top 200 glyphs
const sortedGlyphs = [...glyphFreq.entries()].sort((a, b) => b[1] - a[1]);
const top200 = sortedGlyphs.slice(0, 200);
const top100 = sortedGlyphs.slice(0, 100);

// Message count distribution
const msgCountDist = {};
for (const [idx, count] of messagesPerResource) {
    let b;
    if (count === 0) b = '0';
    else if (count <= 5) b = '1-5';
    else if (count <= 10) b = '6-10';
    else if (count <= 20) b = '11-20';
    else if (count <= 50) b = '21-50';
    else if (count <= 100) b = '51-100';
    else if (count <= 200) b = '101-200';
    else if (count <= 500) b = '201-500';
    else b = '500+';
    msgCountDist[b] = (msgCountDist[b] || 0) + 1;
}

const glyphsSorted = [...uniqueGlyphs].sort((a, b) => a - b);
const minGlyph = glyphsSorted.length > 0 ? glyphsSorted[0] : 0;
const maxGlyph = glyphsSorted.length > 0 ? glyphsSorted[glyphsSorted.length - 1] : 0;

function hex4(n) { return '0x' + n.toString(16).toUpperCase().padStart(4, '0'); }
function padR(s, n) { return String(s).padStart(n); }

// Build output
const L = [];
L.push('='.repeat(70));
L.push('MSG FREQUENCY ANALYSIS - BUSIN 0: Wizardry Alternative Neo');
L.push('='.repeat(70));
L.push('');
L.push(`Resources processed: ${resourcesProcessed} / ${msgIndices.length} expected`);
L.push(`Total messages across all resources: ${totalMessages}`);
L.push(`Total glyph tokens (non-control): ${totalGlyphs}`);
L.push(`Unique glyph indices used: ${uniqueGlyphs.size}`);
L.push(`Glyph index range: ${hex4(minGlyph)} - ${hex4(maxGlyph)}`);
L.push('');
L.push('-'.repeat(70));
L.push('CONTROL CODE COUNTS');
L.push('-'.repeat(70));
const ccNames = { 0xFFFF: '(message delimiter)', 0xFFFE: '(line/page break)', 0xFFD2: '', 0xFFD3: '', 0xFFE0: '', 0xFFE1: '' };
for (const code of [0xFFFF, 0xFFFE, 0xFFE1, 0xFFE0, 0xFFD3, 0xFFD2]) {
    L.push(`  ${hex4(code)} ${ccNames[code] || ''}: ${controlCodes.get(code) || 0}`);
}
L.push('');
L.push('-'.repeat(70));
L.push('SPEAKER TAG ANALYSIS');
L.push('-'.repeat(70));
L.push(`Messages starting with 011E 0247 (speaker tag): ${speakerTagCount}`);
if (totalMessages > 0) {
    L.push(`Percentage of all messages: ${(speakerTagCount / totalMessages * 100).toFixed(1)}%`);
}
L.push('');
L.push('-'.repeat(70));
L.push('MESSAGE LENGTH STATISTICS');
L.push('-'.repeat(70));
if (allMessageLengths.length > 0) {
    const lens = allMessageLengths.map(x => x.len);
    const avg = lens.reduce((a, b) => a + b, 0) / lens.length;
    const sorted = [...lens].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    L.push(`Average message length (uint16 tokens): ${avg.toFixed(1)}`);
    L.push(`Median message length: ${median}`);
    const lg = allMessageLengths[0];
    L.push(`Longest message: ${lg.len} tokens (resource ${lg.resIdx}, msg #${lg.msgIdx})`);
    const sh = allMessageLengths[allMessageLengths.length - 1];
    L.push(`Shortest message: ${sh.len} tokens (resource ${sh.resIdx}, msg #${sh.msgIdx})`);
    L.push('');
    L.push('Top 10 longest messages:');
    for (let i = 0; i < Math.min(10, allMessageLengths.length); i++) {
        const m = allMessageLengths[i];
        L.push(`  ${m.len} tokens - resource ${m.resIdx}, message #${m.msgIdx}`);
    }
}
L.push('');
L.push('-'.repeat(70));
L.push('MESSAGE COUNT PER RESOURCE DISTRIBUTION');
L.push('-'.repeat(70));
for (const b of ['0', '1-5', '6-10', '11-20', '21-50', '51-100', '101-200', '201-500', '500+']) {
    if (msgCountDist[b]) {
        L.push(`  ${b.padStart(8)} messages: ${String(msgCountDist[b]).padStart(4)} resources`);
    }
}
L.push('');
const rss = [...resourceStats].sort((a, b) => b.messages - a.messages);
L.push('Top 10 resources by message count:');
for (let i = 0; i < Math.min(10, rss.length); i++) {
    const r = rss[i];
    L.push(`  Resource ${String(r.idx).padStart(4, '0')} (${r.file}): ${r.messages} messages, ${r.unique} unique glyphs`);
}
L.push('');
L.push('-'.repeat(70));
L.push('TOP 100 MOST FREQUENT GLYPHS');
L.push('-'.repeat(70));
L.push(`${padR('Rank', 4)}  ${padR('Index', 6)}  ${padR('Hex', 6)}  ${padR('Count', 8)}  ${padR('%', 6)}`);
for (let i = 0; i < top100.length; i++) {
    const [gl, cnt] = top100[i];
    const pct = (cnt / totalGlyphs * 100).toFixed(2);
    L.push(`${padR(i + 1, 4)}  ${padR(gl, 6)}  ${hex4(gl)}  ${padR(cnt, 8)}  ${padR(pct, 5)}%`);
}
L.push('');
L.push('-'.repeat(70));
L.push('GLYPH MAPPING HYPOTHESES');
L.push('-'.repeat(70));
L.push('Most common Japanese text characters (typical frequency order):');
L.push('  Hiragana: no ha i wo ta te ni ga ru de shi to na ka tsu');
L.push('  Katakana: - n ru su a to ku ri i ra');
L.push('  Kanji: jin dai nichi chuu nen shutsu ue sei ko hon');
L.push('  Punctuation: . , ! ? brackets');
L.push('');

// Glyph clustering for top 200
const gr2 = {};
for (const [g, c] of top200) {
    const rs2 = Math.floor(g / 0x40) * 0x40;
    gr2[rs2] = (gr2[rs2] || 0) + c;
}
L.push('Glyph index clustering (by 64-glyph blocks, top 200 only):');
for (const rng of Object.keys(gr2).map(Number).sort((a, b) => a - b)) {
    L.push(`  ${hex4(rng)}-${hex4(rng + 0x3F)}: ${padR(gr2[rng], 8)} occurrences`);
}
L.push('');

// Full density
const frc = {};
const fru = {};
for (const [g, c] of glyphFreq) {
    const rs2 = Math.floor(g / 0x40) * 0x40;
    frc[rs2] = (frc[rs2] || 0) + c;
    fru[rs2] = (fru[rs2] || 0) + 1;
}
L.push('Full glyph density (all glyphs, 64-glyph blocks):');
for (const rng of Object.keys(frc).map(Number).sort((a, b) => a - b)) {
    L.push(`  ${hex4(rng)}-${hex4(rng + 0x3F)}: ${padR(frc[rng], 8)} total, ${padR(fru[rng], 3)} unique`);
}

const outputText = L.join('\n');
fs.writeFileSync(OUT_TXT, outputText, 'utf-8');

// JSON output
const glyphJson = {
    metadata: {
        total_resources: resourcesProcessed,
        total_messages: totalMessages,
        total_glyphs: totalGlyphs,
        unique_glyphs: uniqueGlyphs.size,
        glyph_range: `${hex4(minGlyph)}-${hex4(maxGlyph)}`
    },
    control_codes: Object.fromEntries([...controlCodes.entries()].sort((a, b) => b[0] - a[0]).map(([k, v]) => [hex4(k), v])),
    top_200_glyphs: top200.map(([g, c], i) => ({
        rank: i + 1, index: g, hex: hex4(g), count: c,
        pct: Math.round(c / totalGlyphs * 100000) / 1000
    }))
};
fs.writeFileSync(OUT_JSON, JSON.stringify(glyphJson, null, 2), 'utf-8');

// FINDINGS.md
const F = [];
F.push('# MSG Frequency Analysis Findings');
F.push('');
F.push('## Overview');
F.push('');
F.push(`- **Resources processed**: ${resourcesProcessed} / ${msgIndices.length}`);
F.push(`- **Total messages**: ${totalMessages}`);
F.push(`- **Total glyph tokens**: ${totalGlyphs}`);
F.push(`- **Unique glyph indices**: ${uniqueGlyphs.size}`);
F.push(`- **Glyph index range**: ${hex4(minGlyph)} - ${hex4(maxGlyph)}`);
F.push('');
F.push('## Control Codes');
F.push('');
for (const code of [0xFFFF, 0xFFFE, 0xFFE1, 0xFFE0, 0xFFD3, 0xFFD2]) {
    F.push(`- ${hex4(code)}: ${controlCodes.get(code) || 0}`);
}
F.push('');
F.push('## Speaker Tags');
F.push('');
if (totalMessages > 0) {
    F.push(`- Messages starting with 0x011E 0x0247: ${speakerTagCount} (${(speakerTagCount / totalMessages * 100).toFixed(1)}% of all messages)`);
}
F.push('');
F.push('## Message Statistics');
F.push('');
if (allMessageLengths.length > 0) {
    const lens = allMessageLengths.map(x => x.len);
    const avg = lens.reduce((a, b) => a + b, 0) / lens.length;
    F.push(`- Average length: ${avg.toFixed(1)} tokens`);
    F.push(`- Longest: ${allMessageLengths[0].len} tokens (resource ${allMessageLengths[0].resIdx})`);
    F.push(`- Shortest: ${allMessageLengths[allMessageLengths.length - 1].len} tokens (resource ${allMessageLengths[allMessageLengths.length - 1].resIdx})`);
}
F.push('');
F.push('## Top 20 Most Frequent Glyphs');
F.push('');
F.push('| Rank | Index | Hex | Count | % |');
F.push('|------|-------|-----|-------|---|');
for (let i = 0; i < Math.min(20, top100.length); i++) {
    const [gl, cnt] = top100[i];
    const pct = (cnt / totalGlyphs * 100).toFixed(2);
    F.push(`| ${i + 1} | ${gl} | ${hex4(gl)} | ${cnt} | ${pct}% |`);
}
F.push('');
F.push('## Glyph Block Density');
F.push('');
F.push('Major populated blocks (64-glyph chunks with >1000 occurrences):');
F.push('');
for (const rng of Object.keys(frc).map(Number).sort((a, b) => a - b)) {
    if (frc[rng] > 1000) {
        F.push(`- ${hex4(rng)}-${hex4(rng + 0x3F)}: ${frc[rng]} total, ${fru[rng]} unique`);
    }
}
F.push('');
F.push('## Key Observations');
F.push('');
F.push('1. Glyph indices likely map to a custom font atlas (see font recon tasks)');
F.push('2. The glyph range suggests a fixed-size character set in the font texture');
F.push('3. Speaker tags (011E 0247) mark dialogue lines with character names');
F.push('4. 0xFFFE serves as line/page break within messages, 0xFFFF as message delimiter');
F.push('');
F.push('## Output Files');
F.push('');
F.push('- dumps/msg_frequency_analysis.txt - Full analysis');
F.push('- dumps/glyph_frequency.json - Top 200 glyph frequencies as JSON');

fs.mkdirSync(path.dirname(FINDINGS), { recursive: true });
fs.writeFileSync(FINDINGS, F.join('\n'), 'utf-8');

console.log(outputText.substring(0, 5000));
console.log('\n... (truncated)');
console.log(`\nFiles written:\n  ${OUT_TXT}\n  ${OUT_JSON}\n  ${FINDINGS}`);
