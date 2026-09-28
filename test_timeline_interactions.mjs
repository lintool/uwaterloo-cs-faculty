import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('./index.html',import.meta.url),'utf8');
const payload=html.match(/<script id="faculty-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
class Element {
 constructor(){this.attrs={};this.style={};this.events={};this.children=[];this.value='';this.textContent='';this.disabled=false;this.clientWidth=1440;this.clientHeight=650;this.scrollLeft=0;this.scrollTop=0;this.classes=new Set();this.classList={add:c=>this.classes.add(c),remove:c=>this.classes.delete(c),toggle:(c,on)=>on?this.classes.add(c):this.classes.delete(c)};}
 matches(){return this.keyboardFocus===true;}setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}append(c){this.children.push(c);}addEventListener(k,f){this.events[k]=f;}dispatchEvent(e){this.events[e.type]?.(e);}scrollTo(x,y){this.scrollLeft=x;this.scrollTop=y;}
}
const ids=Object.fromEntries([...html.matchAll(/\bid="([^" ]+)"/g)].map(m=>[m[1],new Element()]));
ids['faculty-data'].textContent=payload;
let resize;
const ctx=vm.createContext({document:{getElementById:id=>{assert.ok(ids[id],id);return ids[id]},createElementNS:()=>new Element()},ResizeObserver:class{constructor(callback){resize=callback;}observe(){}},Event:class{constructor(type){this.type=type}}});
vm.runInContext(script,ctx);
assert.equal(ids.overlay.children.length,249);
const input=q=>{ids.search.value=q;ids.search.dispatchEvent({type:'input'})};
const click=id=>ids[id].dispatchEvent({type:'click'});
input('Michael Liu');assert.equal(ids.count.textContent,'1 match');click('next');assert.equal(ids.person.textContent,'Michael Liu');assert.equal(ids.details.hidden,false);assert.match(ids.periods.textContent,/2010–2017 · grey \/ 2023–present \(2026\) · grey/);assert.notEqual(ids.scale.textContent,'100%');
input('Anna Lubiw');click('next');assert.match(ids.periods.textContent,/2021–present \(2026\) · light purple/);
input('Eric Schost');assert.equal(ids.count.textContent,'1 match');click('next');assert.equal(ids.person.textContent,'Éric Schost');
input('zzzzzz');assert.equal(ids.count.textContent,'0 matches');assert.equal(ids.next.disabled,true);
input('Cowan');assert.equal(ids.count.textContent,'2 matches');click('next');const first=ids.person.textContent;click('next');assert.notEqual(ids.person.textContent,first);click('previous');assert.equal(ids.person.textContent,first);
click('fit');assert.equal(ids.scale.textContent,'100%');assert.equal(ids.search.value,'');assert.equal(ids.person.textContent,'');assert.equal(ids.details.hidden,true);assert.equal(ids.viewport.scrollLeft,0);
assert.ok(!/<(?:script|link)[^>]+(?:src|href)=/i.test(html));
console.log('PASS: 249 accessible faculty regions; zoom, reset, accented search, no matches, result cycling, split appointments, and lighter extension details.');

// Pointer focus must not navigate before click, nor may the details resize pan.
click('in');ids.viewport.scrollLeft=240;ids.viewport.scrollTop=130;
const target=ids.overlay.children[100];
let prevented=false;
target.dispatchEvent({type:'mousedown',button:0,preventDefault(){prevented=true;}});
assert.equal(prevented,true,'primary mouse selection must suppress native focus scrolling');
target.dispatchEvent({type:'focus'});
assert.equal(ids.viewport.scrollLeft,240,'pointer focus must not pan horizontally');
assert.equal(ids.viewport.scrollTop,130,'pointer focus must not pan vertically');
target.dispatchEvent({type:'click'});
const width=ids.stage.style.width;ids.viewport.clientHeight=200;resize();
assert.equal(ids.viewport.scrollLeft,240,'details resize must not recenter');
assert.equal(ids.viewport.scrollTop,130,'details resize must not jump');
assert.equal(ids.stage.style.width,width,'details resize must preserve zoomed scale');
target.keyboardFocus=true;target.dispatchEvent({type:'focus'});
assert.notEqual(ids.viewport.scrollLeft,240,'keyboard focus must still reveal the bar');
console.log('PASS: pointer selection stays stationary; details resize preserves scale and scroll; keyboard navigation still reveals faculty.');

// Direct bar activation exits search mode, but search result navigation does not.
input('Cowan');click('next');assert.equal(ids.search.value,'Cowan');
const priorZoom=ids.scale.textContent;
target.dispatchEvent({type:'click'});
assert.equal(ids.search.value,'');
assert.equal(ids.previous.disabled,true);assert.equal(ids.next.disabled,true);
assert.equal(ids.count.textContent,'249 faculty');
assert.ok(ids.overlay.children.every(node=>!node.classes.has('match')));
assert.ok(target.classes.has('selected'));
assert.equal(ids.scale.textContent,priorZoom);
input('Cowan');
target.dispatchEvent({type:'keydown',key:'Enter',preventDefault(){}});
assert.equal(ids.search.value,'');
assert.ok(ids.overlay.children.every(node=>!node.classes.has('match')));
console.log('PASS: bar click and keyboard activation clear search text, highlights, and result navigation without changing zoom.');
