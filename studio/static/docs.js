'use strict';
let timer;
function message(text){const t=document.getElementById('toast');t.textContent=text;t.hidden=false;clearTimeout(timer);timer=setTimeout(()=>t.hidden=true,3500)}
async function copy(text){try{await navigator.clipboard.writeText(text);message('Copied to clipboard')}catch{message('Clipboard unavailable. Select the text and copy it manually.')}}
document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=()=>copy(document.getElementById(b.dataset.copy).textContent));
document.getElementById('copy-setup').onclick=async()=>{try{const r=await fetch('/static/setup.sql');if(!r.ok)throw Error();await copy(await r.text())}catch{message('Could not load setup SQL. Use the download link.')}};
