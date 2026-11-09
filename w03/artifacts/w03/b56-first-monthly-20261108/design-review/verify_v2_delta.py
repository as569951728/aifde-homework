from pathlib import Path
import csv,json,hashlib,collections
R=Path(__file__).resolve().parents[4]; O=Path(__file__).resolve().parent;B=O.parent;old=B/'independent-b6';new=B/'independent-b6-v2'
j=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();csvs=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
checks=[]
def ck(id,p,e=None):checks.append({'id':id,'passed':bool(p),'evidence':e})
freeze=j(new/'expected-freeze.json');evidence={}
ck('v2 expected freeze advertised hash',sha(new/'expected-freeze.json')=='18b010781fdf4d133926f36090ef3dcdd0141bdd449389ec874fe31f1f3743eb')
for rel,h in freeze['inputs_sha256'].items():ck('v2 input '+rel,sha(R/rel)==h)
for rel,h in freeze['artifacts_sha256'].items():ck('v2 artifact '+rel,sha(R/rel)==h);evidence[rel]=sha(R/rel)
prior=j(O/'verification-results.json')['evidence_sha256']
ck('B5 and B6 v1 previously audited artifacts preserved',all(sha(R/p)==h for p,h in prior.items()))
raw0=csvs(old/'fixture-data/orders.csv');raw=csvs(new/'fixture-data/orders.csv');delta=[r for r in raw if r not in raw0]
ck('only one extra artificial order',raw[:len(raw0)]==raw0 and len(raw)==8 and len(delta)==1,delta)
r=delta[0]
ck('third effective M00002 order',r['order_id']=='FXB6-008' and r['member_id']=='M00002' and r['ordered_at']=='2026-08-20' and r['status']=='paid' and int(r['paid_cents'])==1500 and int(r['refund_cents'])==0 and r['store_id']=='S03' and r['channel']=='门店')
ck('other three tables unchanged',all((old/'fixture-data'/f'{t}.csv').read_bytes()==(new/'fixture-data'/f'{t}.csv').read_bytes() for t in ['members','cards','stores']))
man=j(new/'fixture-data/manifest.json');ck('v2 manifest id count hashes',man['id']=='qinghe-w03-b6-independent-fixture-20261108-v2' and man['counts']['orders']==8 and all(sha(new/'fixture-data'/f)==h for f,h in man['sha256'].items()))
v=lambda r:r['status']=='paid' and int(r['paid_cents'])>int(r['refund_cents'])
c=collections.Counter(r['member_id'] for r in raw if v(r));good=[len(c),sum(x>=2 for x in c.values())];good.append(good[1]/good[0]);bad=[len(c),sum(x==2 for x in c.values())];bad.append(bad[1]/bad[0])
ck('>=2 versus ==2 differs with same correct result',dict(c)=={'M00001':1,'M00002':3,'M00003':1} and good==[3,1,1/3] and bad==[3,0,0],{'counts':dict(c),'correct':good,'wrong_exact2':bad})
a=j(old/'tests-fixture.json')[0];t=j(new/'tests-fixture.json')[0];ea=dict(a['expected']);en=dict(t['expected']);ea.pop('data_version');en.pop('data_version')
ck('fixture question/intent/rows/units unchanged',a['question']==t['question'] and ea==en and t['expected']['rows']==[good])
ck('small six cases byte unchanged',(old/'tests-small.json').read_bytes()==(new/'tests-small.json').read_bytes())
small=csvs(R/'materials/data/small/orders.csv');aug=[r for r in small if v(r) and r['ordered_at'][:7]=='2026-08'];cnt=collections.Counter(r['member_id'] for r in aug)
ck('original small exact2 positive control persists',sum(n==2 for n in cnt.values())==12 and sum(n>2 for n in cnt.values())==0)
ck('original small channel split remains distinguishable',sum(n>=2 for n in collections.Counter((r['member_id'],r['channel']) for r in aug).values())==0)
ledger0=csvs(old/'ledger-fixture.csv');ledger=csvs(new/'ledger-fixture.csv');changed=[(a,b) for a,b in zip(ledger0,ledger) if a!=b]
ck('only affected account-month ledger changed',len(changed)==1 and changed[0][1]['member_id']=='M00002' and changed[0][1]['month']=='2026-08')
l=changed[0][1];ck('changed row exact effective IDs and count',set(l['effective_order_ids'].split(';'))=={'FXB6-004','FXB6-005','FXB6-008'} and l['effective_count']=='3' and l['buyer']=='1' and l['repeat_buyer']=='1')
d=[x for x in json.loads(l['order_decisions']) if x['id']=='FXB6-008'][0];ck('new order ledger raw provenance',d['csv_line']==9 and d['date']==r['ordered_at'] and d['paid_cents']==1500 and d['refund_cents']==0)
s=j(new/'monthly-summary-fixture.json');s0=j(old/'monthly-summary-fixture.json');sc=[k for k in s if s[k]!=s0[k]];ck('only August order count changes in monthly summary',sc==['2026-08'] and s['2026-08']['all_order_count']==8 and all(s['2026-08'][k]==s0['2026-08'][k] for k in s['2026-08'] if k!='all_order_count'))
threshold=j(new/'threshold-discrimination.json');ck('counterexample independently correct',threshold['correct_rows']==[good] and threshold['wrong_rows']==[bad])
design=j(new/'design.json');tests={x['id']:x for x in j(new/'tests-small.json')+[t]};ck('v2 design tests aligned',len(design['cases'])==7 and all(x['independent_expected']==tests[x['id']]['expected'] and x['question']==tests[x['id']]['question'] for x in design['cases']))
# Re-check only mechanical assembly, not old case semantics.
smallnew=j(B/'tests-new-small-v2.json');allplanned=j(B/'tests-small-all-planned-v2.json');formal=j(R/'customer/w03/tests.json');b5=j(B/'independent-b5/tests-small.json')
ck('v2 combined new10 exact',smallnew==b5+j(new/'tests-small.json'))
ck('v2 combined43 exact objects',len(allplanned)==43 and len({x['id'] for x in allplanned})==43 and {x['id']:x for x in allplanned}=={x['id']:x for x in formal+smallnew})
ck('original33 exact bytes retained',(R/'customer/w03/tests.json').read_bytes()==(B/'before/customer/w03/tests.json').read_bytes())
for p in [new/'expected-freeze.json',B/'tests-new-small-v2.json',B/'tests-small-all-planned-v2.json',O/'verify_v2_delta.py',O/'verification-results.json',O/'review-v1-initial.json',O/'final-review.json']:
 evidence[str(p.relative_to(R))]=sha(p)
report={'stage':'v2_delta_review_only','checks':checks,'failed_checks':[x for x in checks if not x['passed']],'evidence_sha256':evidence,'reused_previous_evidence':'verification-results.json, 177 static checks; no old case semantic reassessment','native_build_calls':0,'native_queries':0}
(O/'verification-v2-delta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failed_checks']},ensure_ascii=False))
