// Pinned MIT Invaders mechanics, browser-save boundaries and deterministic traces.
// Independent Node standard-library tests; no Claude host/framework required.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const payload = process.env.INVADERS_PAYLOAD || path.resolve('plugins/invaders-local/invaders-local');
const {W, newGame, move, fire, step, draw} = await import(pathToFileURL(path.join(payload,'assets/engine.mjs')));
const {validGame, saveText, restoreSave} = await import(pathToFileURL(path.join(payload,'assets/state.mjs')));
const run = (g,n) => { for (let i=0;i<n;i++) g=step(g); return g; };
test('new game and seeded traces are deterministic, with immutable inputs',()=>{
 const trace=()=>{let g=newGame(0,1337);for(let t=0;t<800;t++){const input=g;const prev=structuredClone(g);g=step(t%4===0?fire(t%13===0?move(g,-1):g):g);assert.deepEqual(input,prev);assert(validGame(g),JSON.stringify(g));if(g.over)break;}return g;};
 assert.deepEqual(trace(),trace()); const g=newGame();const before=structuredClone(g);step(fire(move(g,1)));assert.deepEqual(g,before);
});
test('movement respects edges through held keys and gliding',()=>{
 let g=newGame();for(let i=0;i<90;i++)g=step(move(g,-1));assert.equal(g.px,0);
 for(let i=0;i<90;i++)g=step(move(g,1));assert.equal(g.px,W-3);
});
test('tap and held movement differ',()=>{let g=newGame();const x=g.px;g=move(g,-1);assert.equal(g.px,x-2);g=run(g,3);assert.equal(g.px,x-2);g=move(g,-1);assert.equal(run(g,3).px,x-6);});
test('shot hits bottom enemy and scores',()=>{let g=newGame();const target=g.invaders.find(i=>i.row===3);g={...g,px:target.x,seed:1,invaders:[target],shields:[]};g=run(fire(g),g.h);assert(g.score>0);});
test('rapid fire obeys reload and maximum three active projectiles',()=>{let g={...newGame(),invaders:[{x:0,y:2,row:0}],shields:[]};g=fire(g);assert.equal(fire(g).shots.length,1);for(let n=0;n<4;n++)g=fire(run(g,3));assert.equal(g.shots.length,3);});
test('shields block both own shots and bombs, disappear on second hit',()=>{let g=newGame();const b=g.shields.find(b=>b.y===g.h-3);g={...g,invaders:[{x:0,y:2,row:0}],px:b.x-1,seed:1};g=run(fire(g),2);assert.equal(g.shots.length,0);assert.equal(g.shields.find(x=>x.x===b.x&&x.y===b.y).hp,1);g=step({...g,tick:1,bombs:[{x:b.x,y:b.y-1}]});assert.equal(g.bombs.length,0);assert(!g.shields.find(x=>x.x===b.x&&x.y===b.y));});
test('three bomb hits end game; finished state cannot move/fire/tick',()=>{let g=newGame();for(let n=0;n<3;n++)g=step({...g,tick:0,invuln:0,bombs:[{x:g.px+1,y:g.h-1}]});assert(g.over);assert.equal(g.lives,0);assert.strictEqual(step(g),g);assert.strictEqual(move(g,1),g);assert.strictEqual(fire(g),g);assert(validGame(g));});
test('cleared wave creates next formation and renewed shields',()=>{let g=step({...newGame(),invaders:[],shields:[]});assert.equal(g.level,2);assert.equal(g.cleared,30);g=run(g,30);assert.equal(g.invaders.length,24);assert(g.shields.length>0);assert(validGame(g));});
test('UFO awards bonus and disappears',()=>{let g=step({...newGame(),shields:[],tick:1,ufo:{x:10,y:0,dir:1},shots:[{x:12,y:1}]});assert.equal(g.ufo,null);assert(g.score>=50);});
test('1500 points grants extra life, never exceeding five',()=>{for(const lives of [3,5]){let g=newGame();const t=g.invaders.find(i=>i.row===3);g=step({...g,score:1495,lives,invaders:[t],shields:[],shots:[{x:t.x+1,y:t.y+1}]});assert.equal(g.lives,Math.min(5,lives+1));assert.equal(g.nextLife,3000);}});
test('enemy at bottom ends game',()=>{const g=step({...newGame(),invaders:[{x:0,y:15,row:0}]});assert(g.over);assert.equal(g.lives,0);});
test('board always has 16 rows of 33 cells',()=>{for(const g of [newGame(),run(newGame(),50)]){const rows=draw(g);assert.equal(rows.length,16);assert(rows.every(r=>r.map(x=>x.text).join('').length===33));}});
test('save round trip retains exact gameplay, wrong seed/version refused',()=>{const g=run(newGame(0,77),40);const s=saveText(g,77);assert.deepEqual(restoreSave(s,77),g);assert.equal(restoreSave(s,78),null);assert.equal(restoreSave(s.replace('1.0.2','0.9.0'),77),null);});
test('malformed, oversized, shallow and dangerous saved shapes refused',()=>{
 for(const s of ['null','[]','{}','{','x'.repeat(65537),JSON.stringify({schema:1,version:'1.0.2',initialSeed:1,game:{v:2,invaders:[]}})])assert.equal(restoreSave(s,1),null);
 const mutations=[g=>g.h=1e9,g=>g.hi=Infinity,g=>g.score=-1,g=>g.lives=9,g=>g.invaders[0].row=99,g=>g.invaders[0].x=-2,g=>g.shields[0].ch='<script>',g=>g.shots=Array(1000).fill({x:1,y:1}),g=>g.ufo={x:2,y:0,dir:0},g=>g.booms=[{x:0,y:0,t:1,text:'<img>'}],g=>g.over='false',g=>g.unexpected=1];
 for(const mutate of mutations){const g=newGame();mutate(g);assert.equal(validGame(g),false);assert.throws(()=>saveText(g,1),/状态无效/);}
});
test('long actual gameplay remains serializable across random input traces',()=>{for(let seed=0;seed<30;seed++){let g=newGame(0,seed);for(let n=0;n<6000&&!g.over;n++){if(n%3===0)g=fire(g);if(n%7===0)g=move(g,n%14===0?-1:1);g=step(g);assert(validGame(g),JSON.stringify({seed,n,g}));}assert.deepEqual(restoreSave(saveText(g,seed),seed),g);}});
