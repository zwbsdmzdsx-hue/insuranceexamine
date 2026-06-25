#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const home = '/Users/camoufcengjingdemacbook';

const files = {
  2: path.join(home, 'iiqe_ch2_data.js'),
  3: path.join(home, 'iiqe_ch3.js'),
  4: path.join(home, 'iiqe_ch4.js'),
  5: path.join(home, 'iiqe_ch5.js'),
  6: path.join(home, 'iiqe_ch6.js'),
  7: path.join(home, 'iiqe_ch7.js'),
};

const output = {};

for (const [ch, filepath] of Object.entries(files)) {
  console.log(`Processing Ch${ch}...`);
  const code = fs.readFileSync(filepath, 'utf-8').trim();
  
  const sandbox = {};
  const context = vm.createContext(sandbox);
  
  try {
    if (ch === '2') {
      // Ch2_DATA = {...}; just strip the var name
      vm.runInContext(code.replace(/^Ch2_DATA\s*=/, 'this._data ='), context);
    } else {
      // const chX = {...}; strip the declaration AND any export default
      let cleanCode = code.replace(/^(?:const|let|var)\s+\w+\s*=/, 'this._data =');
      cleanCode = cleanCode.replace(/\nexport\s+default\s+\w+;?\s*$/, '');
      vm.runInContext(cleanCode, context);
    }
    
    const data = sandbox._data;
    
    if (data && data.sections && Array.isArray(data.sections)) {
      const sectionData = [];
      for (const sec of data.sections) {
        const sd = { 
          id: sec.id || '', 
          title: sec.title || '', 
          plain_explanation: sec.plain_explanation || sec.explanation || '' 
        };
        
        // Cards: handle {term,definition,plain} and {id,type,title,content} formats
        sd.cards = (sec.cards || []).map(c => {
          if (c.term) return { term: c.term, definition: c.definition || '', plain: c.plain || '' };
          if (c.title) return { term: c.title, definition: c.content || '', plain: '' };
          return { term: '知识卡片', definition: String(c.content || c.definition || ''), plain: '' };
        });
        
        // Quiz
        sd.quiz = (sec.quiz || []).map(q => {
          if (q.q) return q;
          if (q.question) {
            const prefixes = 'ABCDEFGH';
            const opts = (q.options || []).map((o, i) => {
              const p = prefixes[i] + '.';
              return String(o).startsWith(p) ? o : p + ' ' + o;
            });
            let answer = q.answer;
            if (answer === undefined) answer = q.correctIndex;
            if (answer === undefined && typeof q.correct === 'string') answer = 'abcdefgh'.indexOf(q.correct.toLowerCase());
            if (answer === undefined && typeof q.correct === 'number') answer = q.correct;
            if (answer === undefined) answer = 0;
            return { 
              q: q.question, 
              options: opts, 
              answer: Number(answer), 
              explanation: q.explanation || q.exclamation || '' 
            };
          }
          return q;
        });
        
        // Comparisons
        sd.comparisons = [];
        const compSource = sec.comparisons || sec.comparison || sec.compares || [];
        for (const c of compSource) {
          const items = (c.items || []).map(item => ({
            name: item.name || item.label || '',
            a: item.a || item.left || '',
            b: item.b || item.right || ''
          }));
          sd.comparisons.push({ title: c.title || '对比', items });
        }
        
        // Cases
        sd.cases = [];
        const caseSource = sec.cases || sec.case_study || sec.examples || [];
        for (const c of caseSource) {
          if (c.title && c.description) {
            sd.cases.push({ title: c.title, description: c.description });
          } else if (c.title && c.scenario) {
            let desc = c.scenario;
            if (c.analysis) desc += '\n\n分析：' + c.analysis;
            if (c.key_lesson) desc += '\n\n教训：' + c.key_lesson;
            sd.cases.push({ title: c.title, description: desc });
          } else if (c.title && c.ruling) {
            let desc = c.description || '';
            desc += '\n\n裁决：' + c.ruling;
            sd.cases.push({ title: c.title, description: desc });
          }
        }
        
        sectionData.push(sd);
      }
      
      output[ch] = {
        title: data.title || '',
        weight: data.weight || 0,
        color: data.color || '#0071e3',
        icon: data.icon || '📖',
        questions: data.questions || 0,
        sections: sectionData
      };
      
      const cnt = {cards:0, quiz:0, comp:0, cases:0};
      sectionData.forEach(s => { cnt.cards += s.cards.length; cnt.quiz += s.quiz.length; cnt.comp += s.comparisons.length; cnt.cases += s.cases.length; });
      console.log(`  ${sectionData.length} sections, ${cnt.cards}C ${cnt.quiz}Q ${cnt.comp}Cp ${cnt.cases}Ca`);
    } else {
      console.log(`  ERROR: no sections array`);
      output[ch] = null;
    }
  } catch(e) {
    console.log(`  ERROR: ${e.message}`);
    output[ch] = null;
  }
}

// Write JSON
fs.writeFileSync(path.join(home, 'iiqe-study', '_extracted_data.json'), JSON.stringify(output, null, 2), 'utf-8');
console.log('\nSaved to _extracted_data.json');
