/* 离线分子结构工作台：浏览器与 Node 共用的有界计算接口。 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.MoleculeCore = api;
})(typeof self !== 'undefined' ? self : globalThis, function () {
  'use strict';
  const VERSION = '1.0.1';
  const LIMITS = Object.freeze({smiles: 1024, smarts: 512, atoms: 256, bonds: 512,
    query_atoms: 128, query_bonds: 256, svg_bytes: 1000000});
  const descriptor_labels = Object.freeze({
    amw: '平均分子量（g/mol）', exactmw: '单同位素精确质量（Da）',
    CrippenClogP: 'Crippen 估算 logP', tpsa: '拓扑极性表面积（Å²）',
    NumHBA: '氢键受体数（RDKit NumHBA 定义）', NumHBD: '氢键供体数（RDKit NumHBD 定义）',
    NumRotatableBonds: '可旋转键数（RDKit 默认定义）', NumRings: '环数（RDKit NumRings 定义）'
  });
  function failure(code, message) { return {ok: false, version: VERSION, error: {code, message}}; }
  function analyze(rdkit, input) {
    let molecule = null, query = null;
    try {
      if (!input || typeof input !== 'object' || Array.isArray(input) ||
          Object.keys(input).some(k => !['smiles', 'smarts'].includes(k)) ||
          typeof input.smiles !== 'string' ||
          (input.smarts !== undefined && typeof input.smarts !== 'string'))
        return failure('invalid_input', '参数只能包含字符串 smiles 和可选的字符串 smarts。');
      const smiles = input.smiles.trim(), smarts = (input.smarts || '').trim();
      if (!smiles) return failure('empty_smiles', '请输入非空 SMILES。');
      if (input.smiles.length > LIMITS.smiles || (input.smarts || '').length > LIMITS.smarts)
        return failure('input_too_large', 'SMILES 最多 1024 个字符，SMARTS 最多 512 个字符。');
      if (!/^[\x21-\x7e]+$/.test(smiles) || (smarts && !/^[\x21-\x7e]+$/.test(smarts)) ||
          /[|>]/.test(smiles) || /[|>]/.test(smarts))
        return failure('unsupported_notation', '仅接受单行 ASCII SMILES / SMARTS；不接受内部空白、名称、CX 扩展或反应表示。');
      if (smiles.includes('*'))
        return failure('unsupported_atom', '分子 SMILES 含未指定元素的虚拟原子 *，不能计算完整分子的描述符；请提供具体原子。SMARTS 查询仍可使用通配符。');
      if (smiles.includes('~'))
        return failure('unsupported_bond', '分子 SMILES 含未指定类型的键 ~，不能计算完整分子的描述符；请提供具体键类型。SMARTS 查询仍可使用任意键 ~。');
      if (!rdkit || typeof rdkit.get_mol !== 'function')
        return failure('engine_unavailable', '本地 RDKit 引擎尚未就绪。');
      molecule = rdkit.get_mol(smiles);
      if (!molecule || !molecule.is_valid()) return failure('invalid_smiles', 'SMILES 无效，未生成分子结果。');
      const atom_count = molecule.get_num_atoms(), bond_count = molecule.get_num_bonds();
      if (atom_count > LIMITS.atoms || bond_count > LIMITS.bonds)
        return failure('molecule_too_large', '分子图最多 256 个显式原子、512 条键；未执行描述符与子结构计算。');
      let atoms = [], bonds = [];
      if (smarts) {
        query = rdkit.get_qmol(smarts);
        if (!query || !query.is_valid()) return failure('invalid_smarts', 'SMARTS 查询无效，未返回旧的匹配结果。');
        if (query.get_num_atoms() > LIMITS.query_atoms || query.get_num_bonds() > LIMITS.query_bonds)
          return failure('query_too_large', 'SMARTS 查询最多 128 个显式原子、256 条键。');
        const hit = JSON.parse(molecule.get_substruct_match(query));
        if (Array.isArray(hit.atoms) && hit.atoms.length) {
          atoms = hit.atoms; bonds = hit.bonds || [];
        }
      }
      const raw = JSON.parse(molecule.get_descriptors()), descriptors = {};
      for (const key of Object.keys(descriptor_labels)) {
        if (typeof raw[key] !== 'number' || !Number.isFinite(raw[key]))
          return failure('descriptor_unavailable', '引擎未返回完整的有限数值描述符；不使用猜测值替代。');
        descriptors[key] = raw[key];
      }
      const svg = molecule.get_svg_with_highlights(JSON.stringify({width: 600, height: 400, atoms, bonds}));
      if (typeof svg !== 'string' || !svg.includes('<svg') || !svg.includes('</svg>') ||
          svg.length > LIMITS.svg_bytes || /<script|<foreignObject|\bon\w+\s*=|(?:href|src)\s*=/i.test(svg))
        return failure('depiction_failed', '引擎未返回符合安全边界的有界 SVG 图像。');
      return {ok: true, version: VERSION, rdkit_version: rdkit.version(),
        input: {smiles, smarts}, canonical_smiles: molecule.get_smiles(), atom_count, bond_count,
        descriptors, descriptor_labels: {...descriptor_labels},
        match: {query_supplied: Boolean(smarts), matched: atoms.length > 0, scope: 'first_match', atoms, bonds,
          message: !smarts ? '未指定 SMARTS，未执行子结构查询。' : atoms.length ?
            '仅展示引擎返回的第一个匹配；原子和键索引从 0 开始，对应 RDKit 规范处理后的分子图，不是 SMILES 字符位置，也不表示全部匹配数。' :
            '当前分子未匹配此 SMARTS；这不表示该结构在其他分子中不存在。'},
        svg, limitations: ['二维结构由输入 SMILES 生成，不是实验测定或三维构象。',
          '描述符是 RDKit 定义下的计算值，不是毒性、药效、合成可行性或安全结论。',
          'RDKit 解析会规范处理结构并移除可省略的普通显式氢；原子数和匹配索引对应处理后的分子图。隐式氢仍参与质量等描述符计算，显式氢 SMARTS 不一定匹配被移除的氢。',
          '查询使用 RDKit 默认匹配参数；未启用额外手性约束，不声称立体选择性验证。']};
    } catch (_) {
      return failure('computation_failed', '本地分子计算失败；请检查输入或缩小结构与查询。没有生成可信的新结果。');
    } finally {
      if (query) query.delete();
      if (molecule) molecule.delete();
    }
  }
  return {VERSION, LIMITS, descriptor_labels, failure, analyze};
});
