import assert from 'node:assert/strict';
import {test} from 'node:test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const root=process.env.MWG_TEST_PAYLOAD || path.resolve(import.meta.dirname,'../modern-web-guidance');
const {buildBm25Index,rankBm25,tokenize,reciprocalRankFusion}=await import(pathToFileURL(path.join(root,'runtime/bm25.mjs')));
test('English tokens preserve API names and eliminate stopwords',()=>{
  assert.deepEqual(tokenize('The USER-INVALID and LCP'),['user-invalid','lcp']);
});
test('Chinese phrase is searchable without spaces',()=>{
  assert.deepEqual(tokenize('中文输入法'),['中文','文输','输入','入法']);
});
test('Known equal-length corpus gives hand-calculated BM25 scores',()=>{
  const index=buildBm25Index([{id:'a',text:'alpha beta'},{id:'b',text:'beta gamma'}]);
  const got=rankBm25(index,'alpha');
  assert.equal(got.length,1);assert.equal(got[0].id,'a');
  assert.ok(Math.abs(got[0].score-Math.log(2))<1e-12);
});
test('Repeated IDs are pooled; unknown query and empty tokens have no hits',()=>{
  const index=buildBm25Index([{id:'a',text:'alpha beta'},{id:'a',text:'alpha alpha'}]);
  assert.equal(rankBm25(index,'alpha').length,1);
  assert.deepEqual(rankBm25(index,'omega'),[]);
  assert.deepEqual(rankBm25(index,'the and'),[]);
});
test('Empty corpus rejected; retained RRF preserves expected score',()=>{
  assert.throws(()=>buildBm25Index([]));
  assert.deepEqual(reciprocalRankFusion([['a'],['a']]),[{id:'a',score:2/61}]);
});
