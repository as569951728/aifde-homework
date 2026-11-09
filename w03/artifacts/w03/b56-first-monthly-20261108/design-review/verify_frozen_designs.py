"""Read-only review of frozen author artifacts against raw CSV; writes only review output.
No author calculator import/execution, build, SQL, metric library or Agent call.
"""
from pathlib import Path
import csv,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE=OUT.parent
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
def csvs(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def check(label, passed, evidence=None):checks.append(dict(id=label,passed=bool(passed),evidence=evidence))
def valid(r):return r['status']=='paid' and int(r['paid_cents'])>int(r['refund_cents'])
def net(r):return int(r['paid_cents'])-int(r['refund_cents'])
def dataset(p):
 d={t:csvs(p/(t+'.csv')) for t in ['orders','members','stores','cards']};man=js(p/'manifest.json')
 for t,rows in d.items():
  pk={'orders':'order_id','members':'member_id','stores':'store_id','cards':'card_id'}[t]
  check(str(p.relative_to(ROOT))+'/'+t+'-integrity',len(rows)==man['counts'][t] and len({r[pk] for r in rows})==len(rows) and all(r[pk] for r in rows) and sha(p/(t+'.csv'))==man['sha256'][t+'.csv'])
 mids={r['member_id'] for r in d['members']};sids={r['store_id'] for r in d['stores']}
 check(str(p.relative_to(ROOT))+'-foreign-keys',all(r['member_id'] in mids and r['store_id'] in sids for r in d['orders']) and all(r['member_id'] in mids for r in d['cards']) and all(r['home_store_id'] in sids for r in d['members']))
 return d

def firsts(d):
 # Direct per-account minimum from raw records, independent from authors' rank ledgers.
 out={}
 for m in d['members']:
  candidates=[r for r in d['orders'] if r['member_id']==m['member_id'] and valid(r)]
  if candidates:out[m['member_id']]=min(candidates,key=lambda r:(r['ordered_at'],r['order_id']))
 return out

def b5_values(d,first,metrics,start,end,mids=None,regs=None):
 regs=regs if regs is not None else [r for r in d['members'] if start<=r['registered_at']<end and (mids is None or r['member_id'] in mids)]
 orders=[r for r in d['orders'] if valid(r) and start<=r['ordered_at']<end and (mids is None or r['member_id'] in mids)]
 f=[r for r in orders if r['order_id']==first[r['member_id']]['order_id']]
 vals=dict(new_member_count=len(regs),first_buyer_count=len({r['member_id'] for r in f}),first_order_sales_cents=sum(net(r) for r in f),first_order_count=len(f),repeat_order_count=len(orders)-len(f),valid_order_count=len(orders))
 return [vals[m] for m in metrics]

def b6_values(d,month):
 c=collections.Counter(r['member_id'] for r in d['orders'] if valid(r) and r['ordered_at'][:7]==month)
 b=len(c);rr=sum(v>=2 for v in c.values())
 return [b,rr,rr/b if b else None]

all_tests=[]; hash_evidence={}
for batch in ['b5','b6']:
 folder=BASE/('independent-'+batch);freeze=js(folder/'expected-freeze.json');hash_evidence[str((folder/'expected-freeze.json').relative_to(ROOT))]=sha(folder/'expected-freeze.json')
 sources=freeze.get('source_files',freeze.get('inputs_sha256',{}))
 for rel,h in sources.items():check(batch+' source '+rel,sha(ROOT/rel)==h)
 for rel,h in freeze.get('artifacts',freeze.get('artifacts_sha256',{})).items():
  p=folder/rel if batch=='b5' else ROOT/rel
  check(batch+' artifact '+rel,sha(p)==h);hash_evidence[str(p.relative_to(ROOT))]=sha(p)
 for label,p in [('small',ROOT/'materials/data/small'),('fixture',folder/'fixture-data')]:
  d=dataset(p);first=firsts(d)
  tests=js(folder/('tests-'+label+'.json'));all_tests+=tests
  for t in tests:
   e=t['expected'];ok=e['status']=='ok'
   check(t['id']+' schema',set(t)=={'id','question','expected','expected_source'} and (not ok or set(e)>= {'status','intent','columns','rows','units'}))
   if not ok:
    check(t['id']+' unsupported',e=={'status':'unsupported'});continue
   i=e['intent'];g=i['group_by'];s=i['start'];end=i['end'];ms=i['metrics']
   check(t['id']+' full intent',set(i)=={'metrics','start','end','group_by','filters'} and s<end and e['columns']==g+ms and set(e['units'])==set(ms))
   if batch=='b5':
    if g==['home_store','member__tier']:
     groups=collections.defaultdict(list)
     for r in d['members']:
      if s<=r['registered_at']<end:groups[(r['home_store_id'],r['tier'])].append(r)
     expected=[list(k)+b5_values(d,first,ms,s,end,regs=v) for k,v in sorted(groups.items())]
    elif g==['member']:
     assert i['filters'][0]['field']=='member' and i['filters'][0]['op']=='in'
     ids=i['filters'][0]['value'];expected=[[mid]+b5_values(d,first,ms,s,end,{mid}) for mid in sorted(ids)]
    else:expected=[b5_values(d,first,ms,s,end)]
   else:
    if g:expected=[[r[0]]+b6_values(d,r[0][:7]) for r in e['rows']]
    else:expected=[b6_values(d,s[:7])]
   check(t['id']+' independent values',e['rows']==expected,{'independent_rows':expected})
   check(t['id']+' units',all(e['units'][m]==('cents' if m=='first_order_sales_cents' else 'ratio' if m=='monthly_repeat_rate' else 'count') for m in ms))
  if batch=='b5':
   account=csvs(folder/f'ledger-{label}-accounts.csv');orderledger=csvs(folder/f'ledger-{label}-orders.csv');regledger=csvs(folder/f'ledger-{label}-registrations.csv');byid={r['order_id']:r for r in d['orders']}
   check(batch+label+' ledger sizes',len(account)==len(d['members']) and len(orderledger)==len(d['orders']) and len(regledger)==len(d['members']))
   accountok=True
   for row in account:
    f=first.get(row['member_id']);accountok &= row['first_order_id']==(f['order_id'] if f else '') and row['first_net_cents']==(str(net(f)) if f else '')
   check(batch+label+' first identity/net ledger',accountok)
   orderok=True
   for row in orderledger:
    raw=byid[row['order_id']]; candidates=[r for r in d['orders'] if valid(r) and r['member_id']==raw['member_id']]
    rank=1+sum((r['ordered_at'],r['order_id'])<(raw['ordered_at'],raw['order_id']) for r in candidates) if valid(raw) else None
    orderok &= all(row[k]==v for k,v in raw.items()) and row['net_cents']==str(net(raw)) and row['valid']==str(valid(raw)) and row['valid_rank']==(str(rank) if rank else '') and row['is_observation_first']==str(rank==1)
   check(batch+label+' complete order ledger',orderok)
   caseledger=js(folder/f'ledger-{label}-cases.json')
   check(batch+label+' case ledger expects',all(next(x for x in tests if x['id']==r['case_id'])['expected']==r['expected'] for r in caseledger))
   idok=True
   for row in caseledger:
    t=next(x for x in tests if x['id']==row['case_id']);i=t['expected']['intent'];allowed=set(i['filters'][0]['value']) if i['filters'] else None
    selected=[r for r in d['orders'] if i['start']<=r['ordered_at']<i['end'] and (allowed is None or r['member_id'] in allowed)]
    expected_first={(r['order_id'],r['member_id'],net(r)) for r in selected if valid(r) and first[r['member_id']]['order_id']==r['order_id']}
    idok &= {(r['order_id'],r['member_id'],r['net_cents']) for r in row['first_orders']}==expected_first
    idok &= set(row['subsequent_ids'])=={r['order_id'] for r in selected if valid(r) and first[r['member_id']]['order_id']!=r['order_id']}
   check(batch+label+' exact selected IDs',idok)
  else:
   ledger=csvs(folder/f'ledger-{label}.csv');summary=js(folder/f'monthly-summary-{label}.json');ok=True
   check(batch+label+' 24x20 ledger',len(ledger)==480 and len({(r['month'],r['member_id']) for r in ledger})==480)
   for row in ledger:
    raw=[r for r in d['orders'] if r['member_id']==row['member_id'] and r['ordered_at'][:7]==row['month']]
    v=[r for r in raw if valid(r)];split=lambda text:set(filter(None,text.split(';')))
    ok &= split(row['all_order_ids'])=={r['order_id'] for r in raw} and split(row['effective_order_ids'])=={r['order_id'] for r in v} and split(row['excluded_order_ids'])=={r['order_id'] for r in raw if not valid(r)}
    ok &= int(row['effective_count'])==len(v) and int(row['buyer'])==int(bool(v)) and int(row['repeat_buyer'])==int(len(v)>=2)
    decisions=json.loads(row['order_decisions'])
    for r in decisions:
     rawrow=d['orders'][r['csv_line']-2]
     ok &= r['id']==rawrow['order_id'] and r['date']==rawrow['ordered_at'] and r['status']==rawrow['status'] and r['paid_cents']==int(rawrow['paid_cents']) and r['refund_cents']==int(rawrow['refund_cents'])
   check(batch+label+' complete monthly ledger',ok)
   check(batch+label+' all 24 monthly summaries',len(summary)==24 and all([r[k] for k in ['monthly_buyer_count','monthly_repeat_buyer_count','monthly_repeat_rate']]==b6_values(d,m) for m,r in summary.items()))
 # compare design embedded expected to tests
 testsmap={t['id']:t for t in all_tests}
 design=js(folder/'design.json')
 if batch=='b5':
  check('B5 design test alignment',all(q['expected']==testsmap[q['case_id']]['expected'] and q['question']==testsmap[q['case_id']]['question'] for x in design['designs'] for q in x['questions_and_expected']))
  check('B5-A01 no duplicate query','B5-A01' not in testsmap and next(x for x in design['designs'] if x['id']=='B5-A01')['candidate_ids']==['B5-N01','B5-H03','B5-H02-F'])
 else:check('B6 design test alignment',all(x['independent_expected']==testsmap[x['id']]['expected'] and x['question']==testsmap[x['id']]['question'] for x in design['cases']))

small=dataset(ROOT/'materials/data/small')
b5=dataset(BASE/'independent-b5/fixture-data');b6=dataset(BASE/'independent-b6/fixture-data')
check('B5 preserves original rows',all(b5[t][:len(small[t])]==small[t] for t in small))
check('B6 original other three tables unchanged',all(b6[t]==small[t] for t in ['members','stores','cards']))
check('13 unique query candidates',len(all_tests)==13 and len({t['id'] for t in all_tests})==13)
check('all 8 new targets covered',set(js(BASE/'scope.json')['new_metrics']) <= {m for t in all_tests if t['expected']['status']=='ok' for m in t['expected']['intent']['metrics']})
# Explicit value contrast independent from author contrast files.
fx={r['order_id']:r for r in b5['orders'] if r['order_id'].startswith('B5F-')}
check('same-day distinct-net tie exposure',net(fx['B5F-O003'])==137 and net(fx['B5F-O004'])==869 and b5['orders'].index(fx['B5F-O004'])<b5['orders'].index(fx['B5F-O003']))
check('partial first refund exposure',int(fx['B5F-O003']['paid_cents'])==200!=137)
check('B6 invalid paid repeat exposure',sum(n>=2 for n in collections.Counter(r['member_id'] for r in b6['orders'] if r['status']=='paid').values())==2 and b6_values(b6,'2026-08')==[3,1,1/3])
check('B6 month keys independently confirmed',next(t for t in all_tests if t['id']=='B6-M01')['expected']['rows'][0][0]=='2026-07-01 00:00:00' and next(t for t in all_tests if t['id']=='B6-M01')['expected']['rows'][1][0]=='2026-08-01 00:00:00')
result={'scope':'independent static design and raw-CSV audit; not native tests','checks':checks,'failed_checks':[c for c in checks if not c['passed']],'reviewed_case_ids':[t['id'] for t in all_tests],'evidence_sha256':hash_evidence,'native_build_calls':0,'native_queries':0}
(OUT/'verification-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'check_count':len(checks),'failed_checks':result['failed_checks'],'case_count':len(all_tests)},ensure_ascii=False))
