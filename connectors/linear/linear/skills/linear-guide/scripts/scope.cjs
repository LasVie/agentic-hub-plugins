/* Independently authored Linear tool restrictions. */
'use strict';
const DESCRIPTIONS = {
  list_teams: '列出当前授权工作区中的团队。',
  get_team: '读取指定团队的信息。',
  list_issues: '按关键词、团队和状态查询 Issue，支持分页。',
  list_issue_statuses: '列出指定团队可用的 Issue 状态。',
  get_issue: '读取指定 Issue 的详情。',
  create_issue: '在指定团队创建一个新 Issue，不修改已有 Issue。',
  save_issue: '在指定团队创建一个新 Issue，不接受 id 或更新参数。',
  list_comments: '分页读取指定 Issue 的评论。',
  create_comment: '向指定 Issue 添加一条新评论，不修改已有评论。',
  save_comment: '向指定 Issue 添加一条新评论，不接受 id 或其他对象作为目标。',
};
const ISSUE_FIELDS = new Set(['team', 'title', 'description']);
const COMMENT_FIELDS = new Set(['issueId', 'body']);
const COMMENT_READ_FIELDS = new Set(['issueId', 'cursor', 'limit', 'orderBy']);
const ALLOWED = new Set(Object.keys(DESCRIPTIONS));

function argumentError(name, args) {
  if (!ALLOWED.has(name)) return '本连接器不提供该工具。';
  if (!args || typeof args !== 'object' || Array.isArray(args)) return '工具参数必须是 JSON 对象。';
  const fields = name === 'save_issue' || name === 'create_issue' ? ISSUE_FIELDS
    : name === 'save_comment' || name === 'create_comment' ? COMMENT_FIELDS
      : name === 'list_comments' ? COMMENT_READ_FIELDS : null;
  if (fields && Object.keys(args).some(key => !fields.has(key))) return '本连接器仅支持新建 Issue 或 Issue 评论；该参数超出允许范围。';
  if ((name === 'save_issue' || name === 'create_issue') &&
      !['team', 'title'].every(key => typeof args[key] === 'string' && args[key].trim())) return '新建 Issue 必须提供 team 和 title。';
  if ((name === 'save_comment' || name === 'create_comment') &&
      !['issueId', 'body'].every(key => typeof args[key] === 'string' && args[key].trim())) return '添加评论必须提供 issueId 和 body。';
  if (name === 'list_comments' && !(typeof args.issueId === 'string' && args.issueId.trim())) return '读取评论必须提供 issueId。';
  return null;
}

function chineseSchema(schema) {
  if (Array.isArray(schema)) return schema.map(chineseSchema);
  if (!schema || typeof schema !== 'object') return schema;
  const output = {};
  for (const [key, value] of Object.entries(schema)) {
    if (key === 'properties' || key === '$defs' || key === 'definitions') {
      output[key] = Object.fromEntries(Object.entries(value).map(([name, item]) => [name, chineseSchema(item)]));
    } else if (key !== 'description' && key !== 'title' && key !== 'examples') output[key] = chineseSchema(value);
  }
  return output;
}

function visibleTool(tool) {
  const schema = chineseSchema(tool.inputSchema || {type: 'object'});
  const fields = tool.name === 'save_issue' || tool.name === 'create_issue' ? ISSUE_FIELDS
    : tool.name === 'save_comment' || tool.name === 'create_comment' ? COMMENT_FIELDS
      : tool.name === 'list_comments' ? COMMENT_READ_FIELDS : null;
  if (fields) {
    schema.properties = Object.fromEntries(Object.entries(schema.properties || {}).filter(([key]) => fields.has(key)));
    schema.additionalProperties = false;
    schema.required = tool.name === 'list_comments' ? ['issueId']
      : fields === ISSUE_FIELDS ? ['team', 'title'] : ['issueId', 'body'];
  }
  return {name: tool.name, description: DESCRIPTIONS[tool.name], inputSchema: schema};
}

module.exports={argumentError,visibleTool,ALLOWED};
