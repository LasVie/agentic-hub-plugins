import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
export async function showModel(container,bytes){
 container.replaceChildren();const scene=new THREE.Scene();scene.background=new THREE.Color('#eef3fc');
 const camera=new THREE.PerspectiveCamera(40,container.clientWidth/container.clientHeight,.01,1000),renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(container.clientWidth,container.clientHeight);container.append(renderer.domElement);
 const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
 scene.add(new THREE.HemisphereLight(0xffffff,0x637393,3));const sun=new THREE.DirectionalLight(0xffffff,3);sun.position.set(5,10,8);scene.add(sun);
 const model=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');scene.add(model.scene);
 const box=new THREE.Box3().setFromObject(model.scene),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()).length();controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(size*.7,size*.55,size*.9));camera.far=Math.max(100,size*15);camera.updateProjectionMatrix();
 let running=true;function draw(){if(!running)return;controls.update();renderer.render(scene,camera);requestAnimationFrame(draw);}draw();
 const observer=new ResizeObserver(()=>{if(!container.clientWidth||!container.clientHeight)return;renderer.setSize(container.clientWidth,container.clientHeight);camera.aspect=container.clientWidth/container.clientHeight;camera.updateProjectionMatrix();});observer.observe(container);
 return()=>{running=false;observer.disconnect();controls.dispose();renderer.dispose();model.scene.traverse(x=>{x.geometry?.dispose();if(x.material)for(const m of Array.isArray(x.material)?x.material:[x.material])m.dispose();});};
}
