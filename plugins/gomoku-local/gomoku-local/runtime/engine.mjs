import fs from 'node:fs';import{winsAt,hasEmpty}from'../vendor/game.mjs';
const q=JSON.parse(fs.readFileSync(0,'utf8'));const b=q.board;
if(!Array.isArray(b)||b.length!==225||!b.every(x=>Number.isInteger(x)&&x>=0&&x<=2)||!Number.isInteger(q.row)||!Number.isInteger(q.col)||q.row<0||q.row>14||q.col<0||q.col>14)throw Error('棋盘或坐标无效');
console.log(JSON.stringify({win:winsAt(b,q.row,q.col),has_empty:hasEmpty(b)}));
