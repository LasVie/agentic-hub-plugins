import {Document,NodeIO} from '@gltf-transform/core';
import {dedup,prune,weld} from '@gltf-transform/functions';
import {deflateSync} from 'node:zlib';
const io=new NodeIO();
function guard(bytes){
 if(bytes.length<20||bytes.length>25*1024*1024||Buffer.from(bytes).toString('ascii',0,4)!=='glTF')throw Error('只接受25 MiB以内的GLB文件');
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),len=view.getUint32(12,true);
 if(view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length||len>bytes.length-20||view.getUint32(16,true)!==0x4E4F534A)throw Error('GLB结构无效');
 const json=JSON.parse(Buffer.from(bytes.subarray(20,20+len)).toString('utf8'));
 if((json.buffers||[]).some(x=>x.uri)||(json.images||[]).some(x=>x.uri))throw Error('首版仅处理资源完全内嵌的GLB，不加载外部地址');
 if(json.extensionsRequired?.length)throw Error('首版不处理需要额外解码器的扩展：'+json.extensionsRequired.join(','));
 if((json.nodes||[]).length>5000||(json.accessors||[]).some(a=>a.count>1000000))throw Error('模型超出有界处理范围');
}
export function describe(doc,bytes){const r=doc.getRoot();return{bytes,meshes:r.listMeshes().length,nodes:r.listNodes().length,materials:r.listMaterials().length,textures:r.listTextures().length,textureBytes:r.listTextures().reduce((n,t)=>n+(t.getImage()?.length||0),0),textureDimensions:r.listTextures().map(t=>t.getSize()),accessors:r.listAccessors().length,animations:r.listAnimations().length};}
export async function inspect(bytes){guard(bytes);return describe(await io.readBinary(bytes),bytes.length);}
export async function optimize(bytes){guard(bytes);const doc=await io.readBinary(bytes),before=describe(doc,bytes.length);await doc.transform(dedup(),weld(),prune({keepAttributes:true,keepIndices:true,keepLeaves:true}));const out=await io.writeBinary(doc);return{bytes:out,before,after:describe(doc,out.length)};}
export async function fixture(){
 const d=new Document(),buf=d.createBuffer(),scene=d.createScene('网页展品阵列');
 function crc(bytes){let n=0xffffffff;for(const b of bytes){n^=b;for(let j=0;j<8;j++)n=(n>>>1)^((n&1)?0xedb88320:0);}return(n^0xffffffff)>>>0;}
 function chunk(type,bytes){const t=Buffer.from(type),header=Buffer.alloc(4),tail=Buffer.alloc(4);header.writeUInt32BE(bytes.length);tail.writeUInt32BE(crc(Buffer.concat([t,bytes])));return Buffer.concat([header,t,bytes,tail]);}
 const pixels=Buffer.alloc(512*(512*4+1));for(let y=0;y<512;y++)for(let x=0;x<512;x++){const offset=y*(512*4+1)+1+x*4;pixels[offset]=(x*3+y)%256;pixels[offset+1]=(x+y*2)%256;pixels[offset+2]=180+((x>>5)+(y>>5))%2*65;pixels[offset+3]=255;}
 const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(512,0);ihdr.writeUInt32BE(512,4);ihdr[8]=8;ihdr[9]=6;
 const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),chunk('IDAT',deflateSync(pixels)),chunk('IEND',Buffer.alloc(0))]);
 const positions=new Float32Array([-1,-1,-1,1,-1,-1,1,1,-1,-1,1,-1,-1,-1,1,1,-1,1,1,1,1,-1,1,1]);
 const indices=new Uint16Array([0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,2,3,7,2,7,6,1,2,6,1,6,5,3,0,4,3,4,7]);
 for(let i=0;i<16;i++){const p=d.createAccessor().setType('VEC3').setArray(positions.slice()).setBuffer(buf),idx=d.createAccessor().setType('SCALAR').setArray(indices.slice()).setBuffer(buf),uv=d.createAccessor().setType('VEC2').setArray(new Float32Array([0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1])).setBuffer(buf),tex=d.createTexture('彩色贴图'+i).setImage(png.slice()).setMimeType('image/png'),mat=d.createMaterial('重复材质').setBaseColorTexture(tex).setMetallicFactor(.15).setRoughnessFactor(.45),prim=d.createPrimitive().setAttribute('POSITION',p).setAttribute('TEXCOORD_0',uv).setIndices(idx).setMaterial(mat),mesh=d.createMesh('展品'+i).addPrimitive(prim),node=d.createNode('展品'+i).setMesh(mesh).setTranslation([(i%4-1.5)*2.6,0,(Math.floor(i/4)-1.5)*2.6]);scene.addChild(node);}
 return io.writeBinary(d);
}
