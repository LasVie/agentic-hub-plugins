// 离线光学实验室：只读stdin/stdout桥接；不访问文件、网络或模型。
import {run,VERSION} from './core.mjs';
let size=0;const chunks=[];
for await(const chunk of process.stdin){size+=chunk.length;if(size>131072){process.stdout.write(JSON.stringify({ok:false,version:VERSION,error:{code:'input_too_large',message:'输入超过128 KiB。'}}));process.exit(0);}chunks.push(chunk);}
try{process.stdout.write(JSON.stringify(run(JSON.parse(Buffer.concat(chunks).toString('utf8')))));}
catch{process.stdout.write(JSON.stringify({ok:false,version:VERSION,error:{code:'invalid_json',message:'输入不是有效的JSON。'}}));}
