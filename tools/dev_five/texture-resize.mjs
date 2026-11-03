import {WebIO} from '@gltf-transform/core';
export async function resizeColorTextures(bytes,maxSize=128){
 const io=new WebIO(),doc=await io.readBinary(bytes),root=doc.getRoot(),color=new Set(),data=new Set();
 for(const m of root.listMaterials()){
  if(m.getBaseColorTexture())color.add(m.getBaseColorTexture());if(m.getEmissiveTexture())color.add(m.getEmissiveTexture());
  for(const get of ['getNormalTexture','getMetallicRoughnessTexture','getOcclusionTexture'])if(m[get]())data.add(m[get]());
 }
 let resized=0;
 for(const t of color){
  if(data.has(t)||!['image/png','image/jpeg'].includes(t.getMimeType()))continue;
  const image=await createImageBitmap(new Blob([t.getImage()],{type:t.getMimeType()}));
  if(Math.max(image.width,image.height)<=maxSize){image.close();continue;}
  const scale=maxSize/Math.max(image.width,image.height),canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(image.width*scale));canvas.height=Math.max(1,Math.round(image.height*scale));canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);image.close();
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('浏览器未能生成PNG贴图');t.setImage(new Uint8Array(await blob.arrayBuffer())).setMimeType('image/png');resized++;
 }
 return{bytes:await io.writeBinary(doc),resized};
}
