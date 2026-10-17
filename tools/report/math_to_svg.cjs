// Formula export only. Written with OpenAI Codex; TeX source stays unchanged.
const fs = require('fs');
const path = require('path');
const {createRequire} = require('module');
const modules = path.resolve(process.argv[2]);
const request = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const localRequire = createRequire(path.join(modules, 'mathjax-full', 'package.json'));
const {mathjax} = localRequire('./js/mathjax.js');
const {TeX} = localRequire('./js/input/tex.js');
const {SVG} = localRequire('./js/output/svg.js');
const {liteAdaptor} = localRequire('./js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = localRequire('./js/handlers/html.js');
const {AllPackages} = localRequire('./js/input/tex/AllPackages.js');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const document = mathjax.document('', {
  InputJax: new TeX({packages: AllPackages}),
  OutputJax: new SVG({fontCache: 'none'}),
});
for (const entry of request) {
  const result = document.convert(entry.tex, {display: entry.display, em: 16, ex: 8, containerWidth: 800});
  const svg = adaptor.firstChild(result);
  const output = adaptor.outerHTML(svg);
  if (output.includes('data-mjx-error')) throw new Error(`Invalid TeX: ${entry.tex}`);
  fs.writeFileSync(entry.path, output, 'utf8');
}
