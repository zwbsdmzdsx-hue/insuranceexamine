#!/usr/bin/env node
const fs = require('fs');
const vm = require('vm');

const home = '/Users/camoufcengjingdemacbook';
const htmlPath = home + '/iiqe-study/index.html';
const jsonPath = home + '/iiqe-study/_extracted_data.json';

// 1. Read original HTML and extract CHAPTER_DATA
const html = fs.readFileSync(htmlPath, 'utf-8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
const fullScript = scriptMatch[1];

// Find just the CHAPTER_DATA assignment
const cdStart = fullScript.indexOf('const CHAPTER_DATA = {');
const cdEnd = (() => {
  const start = fullScript.indexOf('{', cdStart);
  let depth = 0;
  for (let i = start; i < fullScript.length; i++) {
    if (fullScript[i] === '{') depth++;
    else if (fullScript[i] === '}') depth--;
    if (depth === 0) return i + 1;
  }
  return -1;
})();
const cdScript = fullScript.substring(cdStart, cdEnd + 1).replace('const ', 'var ');

// Extract CHAPTER_META too
const cmStart = fullScript.indexOf('const CHAPTER_META = {');
const cmEnd = (() => {
  const start = fullScript.indexOf('{', cmStart);
  let depth = 0;
  for (let i = start; i < fullScript.length; i++) {
    if (fullScript[i] === '{') depth++;
    else if (fullScript[i] === '}') depth--;
    if (depth === 0) return i + 1;
  }
  return -1;
})();
const cmScript = fullScript.substring(cmStart, cmEnd + 1).replace('const ', 'var ');

// Evaluate in sandbox
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(cdScript, sandbox);
vm.runInContext(cmScript, sandbox);
const chData = sandbox.CHAPTER_DATA;
const chMeta = sandbox.CHAPTER_META;

console.log('CHAPTER_DATA keys:', Object.keys(chData).join(', '));

// Convert to JSON format
const allData = {};

for (const ch of Object.keys(chData)) {
  const raw = chData[ch];
  const meta = chMeta[ch] || {};
  
  const chObj = {
    title: meta.title || raw.title || '',
    weight: meta.weight || raw.weight || 0,
    color: meta.color || raw.color || '#0071e3',
    icon: meta.icon || raw.icon || '📖',
    questions: meta.questions || raw.questions || 0,
    sections: []
  };

  // Handle the original Ch1 format (flat keys like '1.1', '1.2')
  // and standard format (sections array)
  let sections = raw.sections || raw._sections || [];
  if (!Array.isArray(sections) || sections.length === 0) {
    // Try flat keys
    const flatKeys = Object.keys(raw).filter(k => /^\d+\.\d+$/.test(k));
    if (flatKeys.length > 0) {
      sections = flatKeys.sort().map(k => ({ id: k, ...raw[k] }));
    }
  }

  for (const sec of sections) {
    const sd = {
      id: sec.id || sec.key || '',
      title: sec.title || '',
      plain_explanation: sec.plain_explanation || sec.explanation || sec.text || '',
      cards: [],
      quiz: [],
      comparisons: [],
      cases: []
    };

    // Cards - handle multiple formats
    const rawCards = sec.cards || [];
    sd.cards = rawCards.map(c => {
      if (c.term) return { term: c.term, definition: c.definition || '', plain: c.plain || '' };
      if (c.title) return { term: c.title, definition: c.content || '', plain: '' };
      return { term: '卡片', definition: String(c.definition || c.content || ''), plain: '' };
    });

    // Quiz
    const rawQuiz = sec.quiz || [];
    sd.quiz = rawQuiz.map(q => {
      if (q.q) return { q: q.q, options: q.options || [], answer: q.answer || 0, explanation: q.explanation || '' };
      if (q.question) {
        const prefixes = 'ABCDEFGH';
        const opts = (q.options || []).map((o, i) => {
          const p = prefixes[i] + '.';
          return String(o).startsWith(p) ? o : p + ' ' + o;
        });
        let ans = q.answer;
        if (ans === undefined) ans = q.correctIndex;
        if (ans === undefined && typeof q.correct === 'string') ans = 'abcdefgh'.indexOf(q.correct.toLowerCase());
        if (ans === undefined && typeof q.correct === 'number') ans = q.correct;
        if (ans === undefined) ans = 0;
        return { q: q.question, options: opts, answer: Number(ans), explanation: q.explanation || q.exclamation || '' };
      }
      return q;
    });

    // Comparisons
    const comps = sec.comparisons || sec.comparison || [];
    sd.comparisons = comps.map(c => ({
      title: c.title || '对比',
      items: (c.items || []).map(it => ({ name: it.name || it.label || '', a: it.a || it.left || '', b: it.b || it.right || '' }))
    }));

    // Cases
    const caseArr = sec.cases || sec.case_study || [];
    sd.cases = caseArr.map(c => {
      if (c.title && c.description) return { title: c.title, description: c.description };
      if (c.title && c.scenario) {
        let d = c.scenario;
        if (c.analysis) d += '\n\n分析：' + c.analysis;
        if (c.key_lesson) d += '\n\n教训：' + c.key_lesson;
        return { title: c.title, description: d };
      }
      return c;
    });

    chObj.sections.push(sd);
  }

  const cnt = { C:0, Q:0, Cp:0, Ca:0 };
  chObj.sections.forEach(s => { cnt.C += s.cards.length; cnt.Q += s.quiz.length; cnt.Cp += s.comparisons.length; cnt.Ca += s.cases.length; });
  console.log(`  Ch${ch}: ${chObj.sections.length} sections, ${cnt.C}C ${cnt.Q}Q ${cnt.Cp}Cp ${cnt.Ca}Ca`);

  allData[ch] = chObj;
}

// 3. Merge with extracted data for Ch2-7 (override with richer content from analysis)
const extracted = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
for (const ch of Object.keys(extracted)) {
  if (extracted[ch] && extracted[ch].sections && extracted[ch].sections.length > 0) {
    console.log(`  Merging Ch${ch} from extracted data (${extracted[ch].sections.length} sections)`);
    // Merge sections by ID
    const existingSections = allData[ch]?.sections || [];
    const existingById = {};
    existingSections.forEach(s => { existingById[s.id] = s; });
    
    for (const newSec of extracted[ch].sections) {
      const id = newSec.id;
      if (existingById[id]) {
        // Merge: prefer new data for cards/quiz/comparisons/cases, keep old for plain_explanation if new is shorter
        const old = existingById[id];
        newSec.cards = newSec.cards.length > 0 ? newSec.cards : old.cards;
        newSec.quiz = newSec.quiz.length > 0 ? newSec.quiz : old.quiz;
        newSec.comparisons = newSec.comparisons.length > 0 ? newSec.comparisons : old.comparisons;
        newSec.cases = newSec.cases.length > 0 ? newSec.cases : old.cases;
        if (!newSec.plain_explanation || newSec.plain_explanation.length < old.plain_explanation.length) {
          newSec.plain_explanation = old.plain_explanation;
        }
      }
    }
    
    // Replace sections with merged data
    const mergedById = {};
    extracted[ch].sections.forEach(s => { mergedById[s.id] = s; });
    // Keep any sections from original that weren't in extracted
    for (const oldSec of existingSections) {
      if (!mergedById[oldSec.id]) {
        extracted[ch].sections.push(oldSec);
      }
    }
    
    allData[ch] = extracted[ch];
  }
}

// 4. Write merged JSON
const outPath = home + '/iiqe-study/_merged_data.json';
fs.writeFileSync(outPath, JSON.stringify(allData, null, 2), 'utf-8');
console.log('\nSaved to _merged_data.json');
