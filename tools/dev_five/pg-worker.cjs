const fs=require('node:fs'),path=require('node:path');
const {PGlite}=require('../vendor/pglite/dist/index.cjs');
process.once('message',async p=>{
 let db;
 try{
  const dir=path.join(p.dataDir,'db-'+p.project);
  if(fs.existsSync(dir)&&fs.lstatSync(dir).isSymbolicLink())throw Error('数据库目录不能是符号链接');
  db=new PGlite(dir);await db.waitReady;
  let result;
  if(p.op==='sample'){
   await db.exec("CREATE TABLE IF NOT EXISTS demo_products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price NUMERIC(10,2), metadata JSONB); INSERT INTO demo_products VALUES (1,'机械键盘',299,'{\"stock\":12}'),(2,'桌面音箱',459,'{\"stock\":8}'),(3,'显示器支架',189,'{\"stock\":25}') ON CONFLICT(id) DO NOTHING;");
   result=await db.query('SELECT id,name,price,metadata FROM demo_products ORDER BY id');
  }else if(p.op==='query'){
   if(typeof p.sql!=='string'||!p.sql.trim()||p.sql.length>50000)throw Error('SQL不能为空且不得超过50000字符');
   result=await db.query(p.sql);
  }else if(p.op==='export'){
   const blob=await db.dumpDataDir('gzip');const bytes=Buffer.from(await blob.arrayBuffer());if(bytes.length>25*1024*1024)throw Error('快照超过25 MiB限制');
   const filename='database-'+p.project+'.tar.gz';fs.writeFileSync(path.join(p.dataDir,filename),bytes,{mode:0o600});result={filename,bytes:bytes.length};
  }else if(p.op==='schema'){result=await db.query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name");}
  else throw Error('数据库操作不受支持');
  await db.close();db=null;
  if(result.rows){result.totalReturned=result.rows.length;result.truncated=result.rows.length>300;result.rows=result.rows.slice(0,300);}
  process.send({ok:true,result});
 }catch(e){try{await db?.close();}catch{}process.send({ok:false,error:'PostgreSQL执行失败：'+e.message});}
 finally{process.disconnect();}
});
