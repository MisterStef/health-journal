import csv,json,collections,os,gzip,re,shutil
csv.field_size_limit(10**9)
SRC='/mnt/user-data/uploads/opennutrition-dataset-2025.1/opennutrition_foods.tsv'
OUT='/home/claude/health-journal/data/opennutrition'
# app key <- dataset key (per 100 g); order is fixed and shared with the app
KEYS=[('cal','calories'),('protein','protein'),('carbs','carbohydrates'),('fat','total_fat'),('fiber','dietary_fiber'),('sat','saturated_fats'),('trans','trans_fats'),('mono','monounsaturated_fats'),('poly','polyunsaturated_fats'),('omega3','omega_3'),('sugar','total_sugars'),('addedSugar','added_sugars'),('sodium','sodium'),('caffeine','caffeine'),('alcohol','ethyl_alcohol'),('calcium','calcium'),('iron','iron'),('magnesium','magnesium'),('potassium','potassium'),('zinc','zinc'),('vitA','vitamin_a'),('vitC','vitamin_c'),('vitD','vitamin_d'),('vitE','vitamin_e'),('vitK','vitamin_k'),('b12','vitamin_b12'),('folate','folate_dfe'),('b6','vitamin_b6'),('thiamin','thiamin'),('riboflavin','riboflavin'),('niacin','niacin')]
def rnd(v):
    if v is None or v==0: return 0
    a=abs(v)
    if a>=100: return round(v)
    if a>=10: return round(v,1)
    if a>=1: return round(v,2)
    return float('%.2g'%v)
def serving_label(s):
    c=s.get('common') or {}; m=s.get('metric') or {}
    q=c.get('quantity'); u=c.get('unit') or ''
    lab=(f"{q:g} {u}".strip() if q else '')
    if c.get('name') and c['name'] not in ('Standard',): lab=(c['name']+(' · '+lab if lab and c['name'].lower().find(str(u).lower())<0 else '')).strip()
    mq=m.get('quantity'); mu=m.get('unit','g')
    if mq:
        met=f"{mq:g} {mu}"
        lab=met if not lab else (lab if lab.replace('fl oz','').strip()==met or lab==met else lab+f" ({met})")
    return lab or '100 g', (mq or 100)
def record(row):
    try: nu=json.loads(row['nutrition_100g'] or '{}'); s=json.loads(row['serving'] or '{}')
    except Exception: return None
    if not nu.get('calories') and not nu.get('protein'): return None
    lab,g=serving_label(s); f=g/100.0
    vals=[]
    for k,src in KEYS:
        v=nu.get(src) or 0
        try: v=float(v)*f
        except Exception: v=0
        if k=='alcohol': v=v/14.0
        vals.append(rnd(v))
    vals[0]=round(vals[0])
    return lab,vals
TY={'everyday':0,'prepared':1,'restaurant':2}
generic=[]; shards=collections.defaultdict(list); nbar=0
for row in csv.DictReader(open(SRC,encoding='utf-8'),delimiter='\t'):
    rec=record(row)
    if not rec: continue
    lab,vals=rec; name=row['name'].strip()
    if row['type'] in TY:
        try: alts=json.loads(row['alternate_names'] or '[]')
        except Exception: alts=[]
        alt=' | '.join(a for a in alts[:6] if isinstance(a,str))[:220]
        generic.append([name,alt,lab,TY[row['type']]]+vals)
    else:
        code=re.sub(r'\D','',row['ean_13'] or '')
        if len(code)<8: continue
        code=code.zfill(13); nbar+=1
        shards[code[:4]].append([code,name,lab]+vals)
os.makedirs(OUT,exist_ok=True)
meta={'keys':[k for k,_ in KEYS],'version':'2025.1','attribution':'OpenNutrition (https://www.opennutrition.app), incorporating (c) Open Food Facts contributors','license':'ODbL 1.0'}
json.dump({'meta':meta,'foods':generic},open(OUT+'/foods.json','w'),separators=(',',':'),ensure_ascii=False)
bdir=OUT+'/barcodes'; shutil.rmtree(bdir,ignore_errors=True); os.makedirs(bdir)
LIM=350_000; index=[]
def emit(prefix,rows):
    blob=json.dumps(rows,separators=(',',':'),ensure_ascii=False)
    if len(blob)>LIM and len(prefix)<9:
        sub=collections.defaultdict(list)
        for r in rows: sub[r[0][:len(prefix)+1]].append(r)
        for p2,r2 in sub.items(): emit(p2,r2)
        return
    open(f'{bdir}/{prefix}.json','w').write(blob); index.append(prefix)
for p,rows in shards.items(): emit(p,rows)
json.dump(sorted(index),open(bdir+'/index.json','w'),separators=(',',':'))
for lic in ['LICENSE-ODbL.txt','LICENSE-DbCL.txt']:
    shutil.copy('/mnt/user-data/uploads/opennutrition-dataset-2025.1/'+lic if os.path.exists('/mnt/user-data/uploads/opennutrition-dataset-2025.1/'+lic) else '/dev/null',OUT+'/'+lic)
open(OUT+'/README.md','w').write('''# OpenNutrition data used by this app

These files are derived from the OpenNutrition Dataset 2025.1 (https://www.opennutrition.app) and are shared under the Open Database License (ODbL 1.0), the same license as the source. See LICENSE-ODbL.txt and LICENSE-DbCL.txt.

Portions of the OpenNutrition dataset incorporate data from Open Food Facts: (c) Open Food Facts contributors, https://world.openfoodfacts.org

What was changed: nutrition per 100 g was converted to the listed serving size, limited to the nutrients this app tracks, ethyl alcohol was converted to US standard drinks (14 g), and the data was split into foods.json (everyday, prepared and restaurant foods) and barcode files grouped by the first digits of the EAN-13 code. Built by build_on.py in this folder.
''')
shutil.copy('/home/claude/build/build_on.py',OUT+'/build_on.py')
print('generic',len(generic),'barcodes',nbar,'shards',len(shards))
sz=os.path.getsize(OUT+'/foods.json'); print('foods.json MB',sz/1e6,'gz',len(gzip.compress(open(OUT+'/foods.json','rb').read()))/1e6)
tot=sum(os.path.getsize(f'{bdir}/{x}') for x in os.listdir(bdir)); mx=max(os.path.getsize(f'{bdir}/{x}') for x in os.listdir(bdir)); print('files',len(os.listdir(bdir)))
print('barcodes MB',tot/1e6,'largest shard MB',mx/1e6)
