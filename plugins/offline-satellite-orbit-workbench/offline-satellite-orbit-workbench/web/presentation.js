// 轨道结果的纯展示与导出；不执行轨道传播。
const SVG_NS = 'http://www.w3.org/2000/svg';
const FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif';

export function numberText(value, digits = 3) {
  if (!Number.isFinite(value)) return '—';
  const fixed = value.toFixed(digits);
  return fixed.includes('.') ? fixed.replace(/0+$/, '').replace(/\.$/, '') : fixed;
}

export function utcText(value) {
  return typeof value === 'string' ? value.replace('T', ' ').replace(/Z$/, ' Z') : '—';
}

export function splitGroundTrack(samples) {
  const segments = [];
  let segment = [];
  for (const sample of samples) {
    const point = { longitudeDeg: sample.longitudeDeg, latitudeDeg: sample.latitudeDeg };
    if (segment.length) {
      const previous = segment[segment.length - 1];
      const delta = point.longitudeDeg - previous.longitudeDeg;
      if (Math.abs(delta) > 180) {
        const adjusted = point.longitudeDeg + (delta > 0 ? -360 : 360);
        const edge = delta > 0 ? -180 : 180;
        const fraction = (edge - previous.longitudeDeg) / (adjusted - previous.longitudeDeg);
        const latitude = previous.latitudeDeg + fraction * (point.latitudeDeg - previous.latitudeDeg);
        segment.push({ longitudeDeg: edge, latitudeDeg: latitude });
        segments.push(segment);
        segment = [{ longitudeDeg: -edge, latitudeDeg: latitude }];
      }
    }
    segment.push(point);
  }
  if (segment.length) segments.push(segment);
  return segments;
}

function element(tag, attributes = {}, text) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function label(x, y, text, attributes = {}) {
  return element('text', { x, y, fill: '#77909a', 'font-size': 11, 'font-family': FONT, ...attributes }, text);
}

function makeSvg(width, height, description) {
  const svg = element('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': description });
  svg.append(element('title', {}, description));
  svg.append(element('rect', { width, height, fill: '#fff' }));
  return svg;
}

function pathData(points, project) {
  return points.map((point, index) => `${index ? 'L' : 'M'}${project(point).map(v => v.toFixed(3)).join(',')}`).join(' ');
}

export function groundTrackSvg(result, selectedIndex = 0) {
  const svg = makeSvg(1000, 450, '星下点经纬度地面轨迹；橙色菱形为观测点，深色圆点为所选采样时刻。');
  const box = { x: 58, y: 27, width: 914, height: 366 };
  const project = point => [box.x + (point.longitudeDeg + 180) / 360 * box.width, box.y + (90 - point.latitudeDeg) / 180 * box.height];
  svg.append(element('rect', { ...box, fill: '#f8fbfc', stroke: '#e0eaed' }));
  for (let longitude = -180; longitude <= 180; longitude += 30) {
    const x = project({ longitudeDeg: longitude, latitudeDeg: 0 })[0];
    svg.append(element('line', { x1: x, y1: box.y, x2: x, y2: box.y + box.height, stroke: longitude === 0 ? '#cfdee2' : '#e6eef0' }));
    if (longitude % 60 === 0) svg.append(label(x, 414, `${longitude}°`, { 'text-anchor': 'middle' }));
  }
  for (let latitude = -90; latitude <= 90; latitude += 30) {
    const y = project({ longitudeDeg: 0, latitudeDeg: latitude })[1];
    svg.append(element('line', { x1: box.x, y1: y, x2: box.x + box.width, y2: y, stroke: latitude === 0 ? '#cfdee2' : '#e6eef0' }));
    svg.append(label(48, y + 4, `${latitude}°`, { 'text-anchor': 'end' }));
  }
  for (const points of splitGroundTrack(result.samples)) {
    svg.append(element('path', { d: pathData(points, project), fill: 'none', stroke: '#25868a', 'stroke-width': 1.7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
  }
  const observer = project(result.observer);
  svg.append(element('path', { d: `M${observer[0]},${observer[1] - 6}l6,6 -6,6 -6,-6Z`, fill: '#b9753a', stroke: '#fff', 'stroke-width': 1.3 }));
  svg.append(label(Math.min(observer[0] + 10, 910), Math.max(observer[1] - 9, 42), '观测点', { fill: '#99632f' }));
  const start = project(result.samples[0]);
  svg.append(element('circle', { cx: start[0], cy: start[1], r: 4, fill: '#fff', stroke: '#25868a', 'stroke-width': 1.7 }));
  const selected = result.samples[selectedIndex];
  const xy = project(selected);
  svg.append(element('circle', { cx: xy[0], cy: xy[1], r: 6, fill: '#154e5e', stroke: '#fff', 'stroke-width': 2 }));
  svg.append(label(58, 440, `所选星下点：纬度 ${numberText(selected.latitudeDeg)}° · 经度 ${numberText(selected.longitudeDeg)}°`, { fill: '#406b78' }));
  svg.append(label(972, 440, '经度 →', { 'text-anchor': 'end' }));
  return svg;
}

export function elevationSvg(result, selectedIndex = 0) {
  const svg = makeSvg(1000, 300, '观测点仰角时间曲线；虚线为最低仰角阈值，淡绿色区域为采样中发现的几何区间。');
  const box = { x: 58, y: 22, width: 914, height: 218 };
  const times = result.samples.map(sample => Date.parse(sample.utc));
  const beginning = times[0];
  const duration = times[times.length - 1] - beginning;
  const x = utc => box.x + (Date.parse(utc) - beginning) / duration * box.width;
  const y = degrees => box.y + (90 - degrees) / 180 * box.height;
  svg.append(element('rect', { ...box, fill: '#fbfdfd', stroke: '#e1ebee' }));
  for (const interval of result.intervals) {
    svg.append(element('rect', { x: x(interval.startUtc), y: box.y, width: Math.max(.2, x(interval.endUtc) - x(interval.startUtc)), height: box.height, fill: '#e6f3ed' }));
  }
  for (let elevation = -90; elevation <= 90; elevation += 30) {
    svg.append(element('line', { x1: box.x, y1: y(elevation), x2: box.x + box.width, y2: y(elevation), stroke: elevation === 0 ? '#bacfd6' : '#e4edef', 'stroke-width': elevation === 0 ? 1.3 : 1 }));
    svg.append(label(48, y(elevation) + 4, `${elevation}°`, { 'text-anchor': 'end' }));
  }
  for (let tick = 0; tick <= 4; tick += 1) {
    const position = box.x + tick / 4 * box.width;
    svg.append(element('line', { x1: position, y1: box.y, x2: position, y2: box.y + box.height, stroke: '#e7eff1' }));
    const date = new Date(beginning + duration * tick / 4).toISOString();
    svg.append(label(position, 260, `${date.slice(11, 16)} Z`, { 'text-anchor': 'middle' }));
    svg.append(label(position, 275, date.slice(5, 10), { 'text-anchor': 'middle', 'font-size': 9 }));
  }
  const threshold = y(result.minimumElevationDeg);
  svg.append(element('line', { x1: box.x, y1: threshold, x2: box.x + box.width, y2: threshold, stroke: '#ba864e', 'stroke-dasharray': '5 4', 'stroke-width': 1.2 }));
  svg.append(label(967, Math.max(15, threshold - 5), `阈值 ${numberText(result.minimumElevationDeg)}°`, { 'text-anchor': 'end', fill: '#a7743b' }));
  svg.append(element('path', { d: pathData(result.samples, sample => [x(sample.utc), y(sample.elevationDeg)]), fill: 'none', stroke: '#1c7b83', 'stroke-width': 1.8, 'stroke-linejoin': 'round' }));
  const selected = result.samples[selectedIndex];
  svg.append(element('line', { x1: x(selected.utc), y1: box.y, x2: x(selected.utc), y2: box.y + box.height, stroke: '#4c7986', 'stroke-dasharray': '3 4', 'stroke-width': 1 }));
  svg.append(element('circle', { cx: x(selected.utc), cy: y(selected.elevationDeg), r: 4.5, fill: '#154e5e', stroke: '#fff', 'stroke-width': 1.6 }));
  return svg;
}

export function exportSvg(result, selectedIndex = 0) {
  const svg = makeSvg(1040, 990, '离线卫星轨道工作台：地面轨迹与观测仰角计算结果');
  svg.append(label(30, 35, '离线卫星轨道工作台', { 'font-size': 22, fill: '#183c48', 'font-weight': 650 }));
  svg.append(label(30, 61, `插件 ${result.version} · Satellite.js ${result.engineVersion} · 卫星 ${result.element.catalogId}`, { 'font-size': 11 }));
  svg.append(label(30, 83, `${result.startUtc} — ${result.endUtc}`, { 'font-size': 11 }));
  const ground = groundTrackSvg(result, selectedIndex);
  ground.setAttribute('x', '20'); ground.setAttribute('y', '106'); ground.setAttribute('width', '1000'); ground.setAttribute('height', '450');
  svg.append(ground);
  svg.append(label(30, 594, `观测点：纬度 ${result.observer.latitudeDeg}°，经度 ${result.observer.longitudeDeg}°，椭球高 ${result.observer.heightM} m`, { fill: '#406b78', 'font-size': 12 }));
  const elevation = elevationSvg(result, selectedIndex);
  elevation.setAttribute('x', '20'); elevation.setAttribute('y', '611'); elevation.setAttribute('width', '1000'); elevation.setAttribute('height', '300');
  svg.append(elevation);
  svg.append(label(30, 947, '仅为所给根数的几何推算；地平线上方不代表实际可见。采样可能漏掉短暂过境。', { 'font-size': 11 }));
  svg.append(label(30, 969, '轨迹为无底图经纬度示意；不用于导航、碰撞预警或任务安全认证。', { 'font-size': 11 }));
  return new XMLSerializer().serializeToString(svg);
}

function csvCell(value) {
  let string = String(value ?? '');
  if (typeof value === 'string' && /^[=+\-@\t\r]/.test(string)) string = `'${string}`;
  return `"${string.replace(/"/g, '""')}"`;
}

export function exportCsv(result) {
  const headers = ['UTC', '纬度（°）', '经度（°）', '椭球高（km）', '方位角（°）', '仰角（°）', '观测点距离（km）', 'TEME位置x（km）', 'TEME位置y（km）', 'TEME位置z（km）', 'TEME速度x（km/s）', 'TEME速度y（km/s）', 'TEME速度z（km/s）', '卫星编号', '插件版本', '引擎版本'];
  const lines = [headers.map(csvCell).join(',')];
  for (const sample of result.samples) {
    lines.push([sample.utc, sample.latitudeDeg, sample.longitudeDeg, sample.heightKm, sample.azimuthDeg, sample.elevationDeg, sample.rangeKm, sample.temePositionKm.x, sample.temePositionKm.y, sample.temePositionKm.z, sample.temeVelocityKmS.x, sample.temeVelocityKmS.y, sample.temeVelocityKmS.z, result.element.catalogId, result.version, result.engineVersion].map(csvCell).join(','));
  }
  return `\uFEFF${lines.join('\r\n')}\r\n`;
}
