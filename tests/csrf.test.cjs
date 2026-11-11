const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('static/csrf.js', 'utf8');
function client() {
  const calls=[];
  const window={fetch:async(input,options)=>{calls.push({input,options});return {ok:true}}};
  vm.runInNewContext(source,{window,Request,Headers,URL,
    location:{href:'http://localhost:5001/',origin:'http://localhost:5001'},
    document:{querySelector:()=>({content:'session-token'})}});
  return {window,calls};
}
test('POST JSON include CSRF conservando content-type e body',async()=>{
  const {window,calls}=client();
  await window.fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  assert.equal(calls[0].options.headers.get('X-CSRFToken'),'session-token');
  assert.equal(calls[0].options.headers.get('Content-Type'),'application/json');
  assert.equal(calls[0].options.body,'{}');
});
test('token mai inviato a un altro sito o porta',async()=>{
  const {window,calls}=client();
  await window.fetch('https://example.test/',{method:'POST'});
  await window.fetch('http://localhost:5000/',{method:'POST'});
  assert.equal(calls[0].options.headers,undefined);
  assert.equal(calls[1].options.headers,undefined);
});
test('supporta Request e metodi DELETE',async()=>{
  const {window,calls}=client();
  await window.fetch(new Request('http://localhost:5001/evento_data/1',{method:'DELETE'}));
  assert.equal(calls[0].options.headers.get('X-CSRFToken'),'session-token');
});
test('GET non modifica le intestazioni',async()=>{
  const {window,calls}=client();
  await window.fetch('/eventi_list');
  assert.equal(calls[0].options.headers,undefined);
});
