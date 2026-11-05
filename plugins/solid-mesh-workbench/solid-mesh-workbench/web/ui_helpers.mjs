/** UI formatting and serialization of engine-validated geometry. */
const MAX_PROJECT_BYTES = 2 * 1024 * 1024;

export function formatMetric(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  if (value === 0) return '0';
  const magnitude = Math.abs(value);
  return new Intl.NumberFormat('zh-CN', {
    maximumSignificantDigits: 7,
    notation: magnitude < 1e-4 || magnitude >= 1e9 ? 'scientific' : 'standard',
  }).format(value);
}

/** No indentation or trailing newline: the saved bytes obey the import limit. */
export function serializeProject(project) {
  let text;
  try {
    text = JSON.stringify(project, (_key, value) => {
      if (typeof value === 'number' && !Number.isFinite(value)) throw new Error();
      return value;
    });
    if (typeof text !== 'string') throw new Error();
  } catch {
    throw new Error('项目无法序列化为有效 JSON；请重新计算后保存。');
  }
  if (new TextEncoder().encode(text).byteLength > MAX_PROJECT_BYTES) {
    throw new Error('项目超过 2 MiB 限制；请减少网格复杂度后重新计算。');
  }
  return text;
}

/** Fit only the visible meshes supplied by the caller; positions are flat XYZ. */
export function meshFrame(meshes) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  let count = 0;
  for (const mesh of meshes) {
    const positions = mesh.positions;
    if ((!Array.isArray(positions) && !ArrayBuffer.isView(positions)) || positions.length % 3 !== 0) {
      throw new Error('预览网格的坐标格式无效。');
    }
    for (let i = 0; i < positions.length; i++) {
      const value = positions[i];
      if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('预览网格含有无效坐标。');
      const axis = i % 3;
      min[axis] = Math.min(min[axis], value);
      max[axis] = Math.max(max[axis], value);
      count++;
    }
  }
  if (count === 0) return { center: [0, 0, 0], radius: 1 };
  const halfSize = max.map((value, i) => (value - min[i]) / 2);
  return {
    center: min.map((value, i) => value + halfSize[i]),
    radius: Math.hypot(...halfSize) || Number.EPSILON,
  };
}
