/* Synthetic-only acceptance: no browser stores or production media are read. */
"use strict";
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto'), assert = require('assert');
const out = process.argv[2];
if (!out || !out.toLowerCase().includes('synthetic')) throw Error('Explicit synthetic output directory required');
fs.mkdirSync(out, {recursive:true});
const templatePath = path.join(__dirname,'review_template.html');
const html = fs.readFileSync(templatePath,'utf8');
const script = id => { const m = html.match(new RegExp('<script id="'+id+'">([\\s\\S]*?)</script>')); assert(m); return m[1]; };
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const fixture = {schema:'r15_q3qc86_public_v1',batch_id:'Q3_SYNTHETIC_ACCEPTANCE',protocol_sha256:['a'.repeat(64)],orders:{Q3A:['Q3-AAAAAAAAAA','Q3-BBBBBBBBBB','Q3-CCCCCCCCCC'],Q3B:['Q3-CCCCCCCCCC','Q3-BBBBBBBBBB','Q3-AAAAAAAAAA']},items:[
 {id:'Q3-AAAAAAAAAA',task:'target',clips:[{id:'main',src:'main.mp4',width:640,height:360,fps:25,framecount:100},{id:'extended',src:'extended.mp4',width:640,height:360,fps:25,framecount:250}],seed_hint:{src:'seed.png',width:640,height:360,clip_id:'extended',frame:30},target_not_locatable:false,direction_labels:{a_to_b:'Region A -> Region B',b_to_a:'Region B -> Region A'}},
 {id:'Q3-BBBBBBBBBB',task:'search_window',clips:[{id:'main',src:'main.mp4',width:640,height:360,fps:25,framecount:100}],seed_hint:null,direction_labels:{a_to_b:'Region A -> Region B',b_to_a:'Region B -> Region A'}},
 {id:'Q3-CCCCCCCCCC',task:'target',clips:[{id:'main',src:'main.mp4',width:640,height:360,fps:25,framecount:100}],seed_hint:null,target_not_locatable:true,direction_labels:{a_to_b:'Region A -> Region B',b_to_a:'Region B -> Region A'}}
]};
const raw = JSON.stringify(fixture), digest = sha(raw), t0 = 2000000000000;
const coreCtx = vm.createContext({console}); vm.runInContext(script('qc86-core'),coreCtx); const C = coreCtx.QC86Core;
const clone = x => JSON.parse(JSON.stringify(x));
const results=[];
function check(name, fn){ fn(); results.push({name,status:'PASS'}); }
function rejects(fn){ assert.throws(fn); }
function answered(){const e=C.newEntry(t0);e.main_completed=true;e.prior_seen='no';e.events.push({kind:'hint_loaded',utc:new Date(t0+5000).toISOString()});e.answers={crossing:'support',direction:'a_to_b',identity:'support',time_support:'determinable'};return e;}

// The mock exercises the exact production UI script, including boot -> start -> show.
async function domHarness(initial={}, opts={}) {
 let clock=t0, nextTimer=1, writeFail=false;const all=[], els={}, reads=[], writes=[], intervals=[];
 class El {
  constructor(tag='DIV'){this.tagName=tag.toUpperCase();this.children=[];this.dataset={};this.style={};this.attributes={};this.listeners={};this.value='';this.textContent='';this.hidden=false;this.disabled=false;this.checked=false;this.files=[];this.paused=true;this.currentTime=0;this._ranges=[];this.duration=4;this.videoWidth=640;this.videoHeight=360;this.playbackRate=1;this.classList={toggle(){}};all.push(this);}
  append(...xs){this.children.push(...xs)} replaceChildren(...xs){this.children=[...xs]} setAttribute(k,v){this.attributes[k]=String(v)} removeAttribute(k){delete this.attributes[k];if(k==='src')delete this.src} remove(){} setPointerCapture(){}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn)} async emit(k, e={}){if(typeof this['on'+k]==='function')await this['on'+k](e);for(const fn of this.listeners[k]||[])await fn(e)}
  click(){if(!this.disabled&&this.onclick)return this.onclick({target:this,preventDefault(){}})}
  pause(){this.paused=true;void this.emit('pause')} play(){this.paused=false;void this.emit('play');return Promise.resolve()} load(){this.currentTime=0;this._ranges=[]}
  get played(){const a=this._ranges;return {length:a.length,start:i=>a[i][0],end:i=>a[i][1]};}
 }
 for(const m of html.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"[^>]*>/g)){els[m[2]]=new El(m[1]);els[m[2]].id=m[2];}
 els['public-items'].textContent=raw;els.rate.value='1';els.technicalReason.value='media_load';
 const qs=[];for(const q of Object.keys(C.ANS)){const e=new El();e.dataset={q,title:q};qs.push(e);}
 function select(s){if(s==='[data-q]')return qs;if(s==='[data-issue]')return all.filter(x=>x.dataset.issue);if(s==='[data-issue]:checked')return all.filter(x=>x.dataset.issue&&x.checked);const n=s.match(/^input\[name="(.+)"\]$/);if(n)return all.filter(x=>x.name===n[1]);return [];}
 const document={getElementById:id=>els[id],querySelectorAll:select,querySelector:s=>{const m=s.match(/^\[data-direction="(.+)"\]$/);return m?all.find(x=>x.dataset.direction===m[1]):null},createElement:t=>new El(t),createTextNode:t=>({textContent:t}),body:new El('body'),addEventListener(k,fn){this['on'+k]=fn}};
 const mem=new Map(Object.entries(initial));const storage={getItem(k){reads.push(k);return mem.get(k)??null},setItem(k,v){if(writeFail)throw Error('SYNTHETIC_QUOTA');writes.push(k);mem.set(k,String(v))},key:i=>[...mem.keys()][i],get length(){return mem.size}};
 class Clock extends Date {constructor(...a){super(...(a.length?a:[clock]))}static now(){return clock}}
 const ctx=vm.createContext({console,Date:Clock,TextEncoder,Uint8Array,crypto:{subtle:{digest:async(_,bytes)=>crypto.createHash('sha256').update(bytes).digest()}},document,localStorage:storage,window:{addEventListener(){}},URL:{createObjectURL:()=> 'blob:synthetic',revokeObjectURL(){}},Blob:class{},setTimeout:()=>nextTimer++,setInterval:fn=>{intervals.push(fn);return nextTimer++},alert(){},confirm:()=>true,prompt:()=>null});
 vm.runInContext(script('qc86-core'),ctx);vm.runInContext(script('qc86-ui'),ctx);await new Promise(r=>setImmediate(r));
 const key='q3qc86:'+fixture.batch_id+':Q3A:answers';
 return {els,all,document,mem,reads,writes,ctx,get state(){return JSON.parse(mem.get(key))},setTime:t=>clock=t,tick:()=>intervals.forEach(f=>f()),failWrites:()=>writeFail=true,async start(code='Q3A'){els.reviewer.value=code;els.exposure.value='none';await els.start.click();},async naturalMain(){els.video.currentTime=0;await els.play.click();els.video._ranges=[[0,4]];els.video.currentTime=4;await els.video.emit('ended');},async hint(){await els.hint.click();await els.hintImage.emit('load');}};
}
(async()=>{try{
 check('public whitelist and opaque identifiers',()=>{C.data(fixture);const b=clone(fixture);b.items[0].confirmed=true;rejects(()=>C.data(b));});
 check('orders identical set, missing/duplicate rejected',()=>{const b=clone(fixture);b.orders.Q3B[0]=b.orders.Q3B[1];rejects(()=>C.data(b));});
 check('fps and external URL rejected',()=>{const b=clone(fixture);b.items[0].clips[0].fps=30;rejects(()=>C.data(b));b.items[0].clips[0].fps=25;b.items[0].clips[0].src='https://invalid.example/a.mp4';rejects(()=>C.data(b));});
 check('missing target explicitly administrative',()=>{const b=clone(fixture);b.items[0].seed_hint=null;rejects(()=>C.data(b));b.items[0].target_not_locatable=true;C.data(b);});
 check('new entry no visual defaults',()=>{const e=C.newEntry(t0);assert.equal(Object.keys(e.answers).length,0);assert.equal(e.search,undefined);assert.equal(C.canSubmit(e,fixture.items[0]),false);});
 check('timeout preserves partial answers without imputation',()=>{const e=C.newEntry(t0);e.answers.crossing='oppose';const n=C.timeout(e,t0+60000);assert.equal(n.status,'incomplete_view');assert.deepEqual(clone(n.answers),{crossing:'oppose'});});
 check('session deadline timestamps actual closure, not future item deadline',()=>{const e=C.newEntry(t0);e.main_completed=true;const n=C.timeout(e,t0+20000,true);assert.equal(n.closed_ms,t0+20000);assert.equal(n.status,'uncertain_time_budget');});
 check('hint must be successfully loaded before target submission',()=>{const e=answered();assert(C.canSubmit(e,fixture.items[0]));e.events=e.events.filter(x=>x.kind!=='hint_loaded');assert(!C.canSubmit(e,fixture.items[0]));});
 check('time/support frames bounds and inversion rejected',()=>{C.interval({clip_id:'main',earliest:0,latest:99},fixture.items[0]);rejects(()=>C.interval({clip_id:'main',earliest:3,latest:2},fixture.items[0]));rejects(()=>C.frameRef({clip_id:'main',frame:100},fixture.items[0]));});
 check('same reviewer/batch/digest imports only',()=>{const s=C.fresh(fixture,'Q3A',digest,'none',t0);C.backup(s,fixture,'Q3A',digest);rejects(()=>C.backup(s,fixture,'Q3B',digest));rejects(()=>C.backup(s,fixture,'Q3A','b'.repeat(64)));assert.notEqual(C.key(fixture,'Q3A'),C.key(fixture,'Q3B'));});
 check('import cannot reset timers or alter locked entry',()=>{const s=C.fresh(fixture,'Q3A',digest,'none',t0);s.entries[fixture.items[0].id]=answered();const n=clone(s);n.started_ms++;rejects(()=>C.immutableImport(s,n));const n2=clone(s);n2.entries[fixture.items[0].id].opened_ms++;rejects(()=>C.immutableImport(s,n2));s.entries[fixture.items[0].id].status='submitted';s.entries[fixture.items[0].id].closed_ms=t0+10000;const n3=clone(s);n3.entries[fixture.items[0].id].answers.crossing='oppose';rejects(()=>C.immutableImport(s,n3));});
 check('malformed claimed submission rejected',()=>{const e=C.newEntry(t0);e.status='submitted';e.closed_ms=t0+10000;rejects(()=>C.entry(e,fixture.items[0]));});
 check('search window has no automatic negative or target answers',()=>{const e=C.newEntry(t0);e.main_completed=true;e.prior_seen='no';assert(!C.canSubmit(e,fixture.items[1]));e.search='cannot_exhaust';assert(C.canSubmit(e,fixture.items[1]));e.answers.crossing='oppose';rejects(()=>C.entry(e,fixture.items[1]));});
 check('candidate null interval rejected before rendering',()=>{const e=C.newEntry(t0);e.candidates=[{interval:null,direction:'uncertain',location:'synthetic',note:''}];rejects(()=>C.entry(e,fixture.items[1]));});
 const h=await domHarness();await h.start();check('exact DOM first-start chain creates first entry safely',()=>{assert(h.state.entries['Q3-AAAAAAAAAA']);assert.equal(h.els.workspace.hidden,false);assert(!h.els.fatal.textContent);});
 check('read only chosen reviewer storage key',()=>assert.deepEqual(h.reads,['q3qc86:'+fixture.batch_id+':Q3A:answers']));
 const deadline=h.state.entries['Q3-AAAAAAAAAA'].deadline_ms;check('first view target hint blocked and not preloaded',()=>{assert(h.els.hint.disabled);assert.equal(h.els.hintImage.src,undefined);});
 await h.naturalMain();await h.hint();check('natural complete main then manual hint, deadline unchanged',()=>{const e=h.state.entries['Q3-AAAAAAAAAA'];assert(e.main_completed);assert(e.events.some(x=>x.kind==='hint_loaded'));assert.equal(e.deadline_ms,deadline);assert.equal(h.els.hintImage.src,'seed.png');});
 h.els.video.currentTime=1;await h.els.nextFrame.click();check('native frame step advances one 25fps frame',()=>assert.equal(Math.floor(h.els.video.currentTime*25),26));
 h.els.note.value='SYNTHETIC typed before deadline';await h.els.note.emit('input');check('note persisted while typing before blur/deadline',()=>assert.equal(h.state.entries['Q3-AAAAAAAAAA'].note,h.els.note.value));
 h.setTime(t0+60000);h.tick();check('deadline administrative only and locked',()=>{const e=h.state.entries['Q3-AAAAAAAAAA'];assert.equal(e.status,'uncertain_time_budget');assert.equal(Object.keys(e.answers).length,0);assert(h.els.answers.disabled);});
 h.setTime(t0+7200000);await h.els.next.click();check('session end navigation cannot select missing entry',()=>{assert(!h.state.entries['Q3-BBBBBBBBBB']);assert.equal(h.els.itemTitle.textContent,'Item Q3-AAAAAAAAAA');});
 const h2=await domHarness();await h2.start();h2.failWrites();h2.els.note.value='SYNTHETIC pending';await h2.els.note.emit('input');check('save failure preserves storage and blocks further answers',()=>{assert(h2.els.answers.disabled);assert(h2.els.saveStatus.textContent.includes('Save failed'));assert.equal(h2.state.entries['Q3-AAAAAAAAAA'].note,'');});
 const h3=await domHarness();await h3.start('Q3B');check('missing reference target does not fill visual answer',()=>{const k='q3qc86:'+fixture.batch_id+':Q3B:answers';const e=JSON.parse(h3.mem.get(k)).entries['Q3-CCCCCCCCCC'];assert.equal(e.status,'reference_target_not_locatable');assert.equal(Object.keys(e.answers).length,0);});
 const h4=await domHarness();await h4.start();await h4.els.technical.click();check('technical failure does not become visual no',()=>{const e=h4.state.entries['Q3-AAAAAAAAAA'];assert.equal(e.status,'technical_failure');assert.equal(Object.keys(e.answers).length,0);});
 const old=C.fresh(fixture,'Q3A',digest,'none',t0-10000);old.entries['Q3-AAAAAAAAAA']=C.newEntry(t0-10000);const hr=await domHarness();hr.els.reviewer.value='Q3A';hr.els.restoreFile.files=[{size:2000,text:async()=>JSON.stringify(old)}];await hr.els.restoreFile.emit('change');check('restore before start preserves original session/item clock',()=>{assert.equal(hr.state.started_ms,t0-10000);assert.equal(hr.state.entries['Q3-AAAAAAAAAA'].opened_ms,t0-10000);assert.equal(hr.state.entries['Q3-AAAAAAAAAA'].deadline_ms,t0+50000);});
 const hi=await domHarness();await hi.start();await hi.naturalMain();await hi.hint();for(const [name,value]of Object.entries(answered().answers)){const el=hi.all.find(x=>x.name===name&&x.value===value);el.checked=true;await el.emit('change');}hi.els.priorSeen.value='no';await hi.els.priorSeen.emit('change');hi.els.earliest.value='10';hi.els.latest.value='5';await hi.els.submit.click();check('invalid visible interval blocks final submission',()=>assert.equal(hi.state.entries['Q3-AAAAAAAAAA'].status,'in_progress'));hi.els.latest.value='15';await hi.els.submit.click();check('valid visible interval included atomically in submission',()=>{assert.equal(hi.state.entries['Q3-AAAAAAAAAA'].status,'submitted');assert.deepEqual(hi.state.entries['Q3-AAAAAAAAAA'].interval,{clip_id:'main',earliest:10,latest:15});});
 check('template has one injection token and no remote executable dependency',()=>{assert.equal(html.split('__PUBLIC_ITEMS_JSON__').length-1,1);assert(!/<script[^>]+src=/i.test(html));assert(!/<link[^>]+href=/i.test(html));assert(html.includes('first enters the region on the other side'));assert(!html.includes('R01'));});
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({schema:'q3qc86_synthetic_acceptance_v1',synthetic:true,status:'PASS',tests:results,script_sha256:sha(fs.readFileSync(__filename)),template_sha256:sha(html),fixture_sha256:digest,node:process.version,limits:{cpu_seconds:60,output_mib:30},scope:'exact embedded core plus mock DOM runtime; browser media decoding not tested; no production stores or answers read'},null,2));
 console.log(JSON.stringify({status:'PASS',tests:results.length,out}));
}catch(e){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({synthetic:true,status:'FAIL',passed:results,error:e.stack,template_sha256:sha(html),script_sha256:sha(fs.readFileSync(__filename))},null,2));console.error(e);process.exitCode=1;}})();
