import fs from 'node:fs/promises';
import {importRuntimeModule} from 'file:///C:/Users/Steven/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/container_tools/runtime_helpers.mjs';
const {FileBlob, PresentationFile}=await importRuntimeModule('@oai/artifact-tool');
const source='C:/Users/Steven/Desktop/一笔成章 · 中期汇报 v1.1.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const info=await p.inspect({kind:'slide,textbox,shape,image,table,layout',maxChars:1000000});
await fs.writeFile('../source-inspect.ndjson',info.ndjson);
for (let i=0;i<p.slides.items.length;i++) {
 const s=p.slides.items[i];
 await fs.writeFile(`../source-renders/slide-${i+1}.layout.json`,await (await s.export({format:'layout'})).text());
}
const s=p.slides.items[0];
console.log('COLLECTION',Object.getOwnPropertyNames(Object.getPrototypeOf(s.shapes)));
console.log('SHAPE',Object.getOwnPropertyNames(Object.getPrototypeOf(s.shapes.items[0])));
console.log('SLIDES',p.slides.items.length,'MASTERS',p.masters.items.length);
console.log('TEXTSTYLE',s.shapes.items.find(x=>x.text?.toString())?.text?.style);
