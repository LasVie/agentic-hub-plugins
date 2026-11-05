/* 离线力学实验室：有界场景适配与数值采样；Matter.js 核心保持原样。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./vendor/matter.js'));
  else root.Mechanics = factory(root.Matter);
})(typeof self !== 'undefined' ? self : this, function (M) {
  'use strict';
  const VERSION = '1.0.0', ENGINE_VERSION = '0.20.0', DT = 1000 / 120;
  const fail = message => { throw new Error(message); };
  function keys(value, expected, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        Object.keys(value).sort().join('|') !== expected.split(' ').sort().join('|')) fail(label + '字段不完整或包含不支持的字段。');
  }
  function number(value, lo, hi, label) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < lo || value > hi) fail(label + '须为 ' + lo + ' 至 ' + hi + ' 的有限数值。');
  }
  const idOK = id => typeof id === 'string' && /^[A-Za-z][A-Za-z0-9_-]{0,23}$/.test(id);
  function validate(scene) {
    keys(scene, 'schema_version engine_version title gravity duration bodies constraints', '场景');
    if (scene.schema_version !== 1 || scene.engine_version !== ENGINE_VERSION) fail('场景或引擎版本不匹配；不自动转换。');
    if (typeof scene.title !== 'string' || !scene.title.trim() || scene.title.length > 80) fail('场景名称须为1至80个字符。');
    number(scene.gravity, -1000, 1000, '垂直重力加速度');
    number(scene.duration, 0.1, 10, '时长');
    if (Math.abs(scene.duration * 120 - Math.round(scene.duration * 120)) > 1e-7) fail('时长须为 1/120 秒的整数倍。');
    if (!Array.isArray(scene.bodies) || scene.bodies.length < 1 || scene.bodies.length > 32) fail('物体数量须为1至32。');
    if (!Array.isArray(scene.constraints) || scene.constraints.length > 16) fail('约束数量不能超过16。');
    const ids = new Set();
    for (const b of scene.bodies) {
      keys(b, 'id label shape x y width height radius angle vx vy mass static rotationLocked friction frictionAir restitution', '物体');
      if (!idOK(b.id) || ids.has(b.id)) fail('物体标识须唯一，且以英文字母开头，仅含字母、数字、下划线或短横线（最多24字符）。');
      ids.add(b.id);
      if (typeof b.label !== 'string' || !b.label.trim() || b.label.length > 40) fail('物体名称须为1至40个字符。');
      if (!['rectangle', 'circle'].includes(b.shape) || (typeof b.static !== 'boolean' || typeof b.rotationLocked !== 'boolean')) fail('只支持矩形、近似圆和明确的静止标记。');
      for (const k of ['x', 'y']) number(b[k], 0, 1000, '物体坐标');
      for (const k of ['width', 'height']) number(b[k], 20, 1000, '矩形尺寸');
      number(b.radius, 10, 100, '圆半径'); number(b.angle, -180, 180, '角度');
      for (const k of ['vx', 'vy']) number(b[k], -600, 600, '初速度');
      number(b.mass, 0.1, 100, '质量');
      for (const k of ['friction', 'restitution']) number(b[k], 0, 1, k === 'friction' ? '摩擦系数' : '恢复系数');
      number(b.frictionAir, 0, 0.1, '空气阻尼系数');
      if (b.static && (b.vx !== 0 || b.vy !== 0)) fail('静止物体的初速度必须为零。');
    }
    const jointIds = new Set();
    for (const c of scene.constraints) {
      keys(c, 'id bodyA bodyB x y length stiffness', '约束');
      if (!idOK(c.id) || jointIds.has(c.id)) fail('约束标识无效或重复。');
      jointIds.add(c.id);
      if (!ids.has(c.bodyB) || (c.bodyA !== null && !ids.has(c.bodyA)) || c.bodyA === c.bodyB) fail('约束引用了不存在或相同的物体。');
      for (const k of ['x', 'y']) number(c[k], 0, 1000, '固定点坐标');
      number(c.length, 10, 700, '约束长度'); number(c.stiffness, 0.1, 1, '约束刚度');
    }
    if (JSON.stringify(scene).length > 24000) fail('场景数据过大。');
    return JSON.parse(JSON.stringify(scene));
  }
  function body(id, x, y, extra = {}) {
    return {id, label: id, shape: 'rectangle', x, y, width: 50, height: 50, radius: 24, angle: 0,
      vx: 0, vy: 0, mass: 1, static: false, rotationLocked: false, friction: 0.2, frictionAir: 0, restitution: 0, ...extra};
  }
  function example(name) {
    const scene = {schema_version: 1, engine_version: ENGINE_VERSION, title: '', gravity: 300, duration: 3, bodies: [], constraints: []};
    if (name === 'fall') Object.assign(scene, {title: '自由落体与地面接触', duration: 2, bodies: [
      body('ball', 400, 100, {label: '落体', shape: 'circle', restitution: 0.6}),
      body('floor', 500, 570, {label: '地面', width: 920, height: 30, static: true})]});
    else if (name === 'collision') Object.assign(scene, {title: '一维碰撞 · 等质量 · 锁定转动', gravity: 0, duration: 3, bodies: [
      body('A', 320, 310, {label: '物体甲', rotationLocked: true, vx: 100, restitution: 1, friction: 0}),
      body('B', 680, 310, {label: '物体乙', rotationLocked: true, vx: -100, restitution: 1, friction: 0})]});
    else if (name === 'pendulum') Object.assign(scene, {title: '固定点单摆', duration: 5, bodies: [
      body('bob', 650, 300, {label: '摆球', shape: 'circle', friction: 0})], constraints: [
      {id: 'pin', bodyA: null, bodyB: 'bob', x: 500, y: 100, length: 250, stiffness: 1}]});
    else fail('示例不存在。');
    return scene;
  }
  function simulate(input) {
    const scene = validate(input);
    if (!M || M.version !== ENGINE_VERSION) fail('本地Matter.js引擎缺失或版本不符。');
    const engine = M.Engine.create({positionIterations: 10, velocityIterations: 10, constraintIterations: 4, enableSleeping: false});
    engine.gravity.x = 0; engine.gravity.y = scene.gravity; engine.gravity.scale = 1e-6;
    const bodies = new Map();
    for (const b of scene.bodies) {
      const options = {label: b.id, angle: b.angle * Math.PI / 180, friction: b.friction,
        frictionStatic: 0.5, frictionAir: b.frictionAir, restitution: b.restitution, slop: 0.05};
      const actual = b.shape === 'circle' ? M.Bodies.circle(b.x, b.y, b.radius, options) : M.Bodies.rectangle(b.x, b.y, b.width, b.height, options);
      M.Body.setMass(actual, b.mass);
      if (b.rotationLocked) M.Body.setInertia(actual, Infinity);
      M.Body.setStatic(actual, b.static);
      // Matter velocity is normalised to its 1000/60ms base, not to our update step.
      M.Body.setVelocity(actual, {x: b.vx / 60, y: b.vy / 60});
      bodies.set(b.id, actual); M.Composite.add(engine.world, actual);
    }
    for (const c of scene.constraints) M.Composite.add(engine.world, M.Constraint.create({
      bodyA: c.bodyA === null ? undefined : bodies.get(c.bodyA), bodyB: bodies.get(c.bodyB),
      pointA: c.bodyA === null ? {x: c.x, y: c.y} : {x: 0, y: 0}, pointB: {x: 0, y: 0},
      length: c.length, stiffness: c.stiffness, damping: 0}));
    const frames = [], pairs = new Set(); let outside = false;
    const snapshot = step => {
      const values = scene.bodies.map(b => {
        const actual = bodies.get(b.id), velocity = M.Body.getVelocity(actual);
        const v = {id: b.id, x: actual.position.x, y: actual.position.y, angle: actual.angle,
          vx: velocity.x * 60, vy: velocity.y * 60};
        if (![v.x, v.y, v.angle, v.vx, v.vy].every(Number.isFinite) || Math.max(Math.abs(v.x), Math.abs(v.y), Math.abs(v.vx), Math.abs(v.vy)) > 20000)
          fail('运动超出安全计算边界；未保留部分结果。请降低速度、重力或时长。');
        outside ||= v.x < 0 || v.x > 1000 || v.y < 0 || v.y > 650;
        return v;
      });
      frames.push({time: step / 120, bodies: values});
    };
    try {
      snapshot(0);
      for (let i = 1; i <= Math.round(scene.duration * 120); i++) {
        M.Engine.update(engine, DT);
        for (const pair of engine.pairs.list) if (pair.isActive) pairs.add([pair.bodyA.label, pair.bodyB.label].sort().join(' / '));
        snapshot(i);
      }
      return {ok: true, version: VERSION, engine_version: ENGINE_VERSION, step_ms: DT, scene,
        frames, contact_pairs: [...pairs].sort(), outside_view: outside};
    } finally { M.Composite.clear(engine.world, false); M.Engine.clear(engine); }
  }
  function csv(result) {
    if (!result || !result.ok || result.version !== VERSION) fail('没有可导出的有效结果。');
    const rows = ['时间_秒,物体标识,横坐标,纵坐标,角度_弧度,横向速度_单位每秒,纵向速度_单位每秒'];
    for (const frame of result.frames) for (const b of frame.bodies) rows.push([frame.time, b.id, b.x, b.y, b.angle, b.vx, b.vy].join(','));
    return '\uFEFF' + rows.join('\r\n') + '\r\n';
  }
  return {VERSION, ENGINE_VERSION, DT, validate, body, example, simulate, csv};
});
