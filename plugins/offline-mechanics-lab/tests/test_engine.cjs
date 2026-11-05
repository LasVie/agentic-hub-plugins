// Independent analytic/physical invariants; run with node --test.
const test = require('node:test'), assert = require('node:assert/strict');
const E = require('../offline-mechanics-lab/assets/engine.js');
const near = (a,b,tol) => assert.ok(Math.abs(a-b)<=tol, `${a} vs ${b}, tolerance ${tol}`);
test('free flight: analytic position and velocity with a declared integration error bound',()=>{
  const s=E.example('fall');s.bodies=s.bodies.slice(0,1);s.duration=1;s.gravity=100;s.bodies[0].vx=25;
  const r=E.simulate(s), b=r.frames.at(-1).bodies[0];
  near(b.x,425,1e-7);near(b.vy,100,1e-6);
  // Semi-implicit fixed stepping: continuous y=150; O(g*t*dt/2)=0.4167.
  near(b.y,150,0.42);assert.ok(b.y>150);assert.equal(r.frames.length,121);
});
test('locked one-dimensional collisions: momentum and restitution 0, .5, 1',()=>{
  for(const e of [0,.5,1]){const s=E.example('collision');s.bodies.forEach(b=>b.restitution=e);
    const r=E.simulate(s),[a,b]=r.frames.at(-1).bodies;
    near(a.vx+b.vx,0,1e-6);near(a.vx,-100*e,1e-6);near(b.vx,100*e,1e-6);
    near(a.y,310,1e-7);near(a.angle,0,1e-7);assert.deepEqual(r.contact_pairs,['A / B']);
  }
});
test('unequal-mass locked elastic collision agrees with momentum formula',()=>{
  const s=E.example('collision');s.bodies[1].mass=2;
  const [a,b]=E.simulate(s).frames.at(-1).bodies;
  near(a.vx,-500/3,1e-6);near(b.vx,100/3,1e-6);near(a.vx+2*b.vx,-100,1e-6);
});
test('resting contact remains bounded and static ground stays fixed',()=>{
  const s=E.example('fall');s.duration=5;s.bodies[0].shape='rectangle';s.bodies[0].restitution=0;
  const r=E.simulate(s),[b,g]=r.frames.at(-1).bodies;
  near(b.y,530,0.06);near(b.vy,0,.01);near(g.y,570,0);near(g.vy,0,0);
});
test('pendulum: bounded length drift and motion about fixed pin',()=>{
  const r=E.simulate(E.example('pendulum'));
  const errors=r.frames.map(f=>Math.abs(Math.hypot(f.bodies[0].x-500,f.bodies[0].y-100)-250));
  assert.ok(Math.max(...errors)<.1,Math.max(...errors));
  assert.ok(Math.min(...r.frames.map(f=>f.bodies[0].x))<400);
});
test('JSON roundtrip and repeat runs reproduce samples, IDs are not engine-global IDs',()=>{
  const s=E.example('pendulum'),r=E.simulate(s);
  assert.deepEqual(E.simulate(JSON.parse(JSON.stringify(s))),r);
  E.simulate(E.example('collision'));assert.deepEqual(E.simulate(s),r);
});
test('CSV consists of actual complete samples with safe identifiers',()=>{
  const r=E.simulate(E.example('collision')), rows=E.csv(r).trim().split('\r\n');
  assert.equal(rows.length,1+r.frames.length*2);
  const last=rows.at(-1).split(',');assert.equal(last[1],'B');near(Number(last[2]),r.frames.at(-1).bodies[1].x,0);
  const bad=E.example('fall');bad.bodies[0].id='=SUM(A1)';assert.throws(()=>E.validate(bad));
});
test('invalid numbers, unsupported fields, dangling constraints and budgets fail closed',()=>{
  const cases=[s=>s.gravity=NaN,s=>s.duration=11,s=>s.duration=.123,s=>s.code='alert(1)',s=>s.bodies[0].mass=0,s=>s.bodies[0].vx=601,
    s=>s.bodies[0].shape='svg',s=>s.bodies[1].id=s.bodies[0].id,s=>s.bodies[1].vx=1,
    s=>s.constraints=[{id:'bad',bodyA:null,bodyB:'absent',x:1,y:1,length:10,stiffness:1}],
    s=>s.bodies=Array.from({length:33},(_,i)=>E.body('b'+i,10,10))];
  for(const mutate of cases){const s=E.example('fall');mutate(s);assert.throws(()=>E.simulate(s),/[\u4e00-\u9fff]/);}
});
test('known upstream multi-contact restitution limitation stays explicit',()=>{
  const s=E.example('collision');s.bodies.forEach(b=>b.rotationLocked=false);
  const [a,b]=E.simulate(s).frames.at(-1).bodies;
  near(a.vx+b.vx,0,1e-6);assert.ok(Math.abs(a.vx)<60); // not a claim of ideal elasticity
});
test('maximum bounded workload returns finite complete data',()=>{
  const s=E.example('fall');s.duration=10;s.gravity=50;s.constraints=[];
  s.bodies=Array.from({length:32},(_,i)=>E.body('b'+i,80+(i%8)*110,70+Math.floor(i/8)*100,{shape:'circle',radius:12}));
  const r=E.simulate(s);assert.equal(r.frames.length,1201);assert.equal(r.frames.at(-1).bodies.length,32);
});
