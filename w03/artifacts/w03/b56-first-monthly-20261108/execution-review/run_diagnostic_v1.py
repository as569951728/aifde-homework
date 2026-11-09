import os,json,sys
from pathlib import Path
base=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(base/'platform'))
out=Path(__file__).resolve().parent
os.environ['DBT_LOG_PATH']=str(out/'diagnostic-v1-project/logs')
os.environ['DBT_SEND_ANONYMOUS_USAGE_STATS']='false'
from fde_product.metrics.engine import Engine
case=json.loads((out/'diagnostic-v1-request.json').read_text())
e=Engine(out/'diagnostic-v1-project')
actual=e.query(case['expected']['intent'])
(out/'diagnostic-v1-actual.json').write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n')
(out/'diagnostic-v1.sql').write_text(actual.get('sql','')+'\n')
print(json.dumps({k:v for k,v in actual.items() if k!='sql'},ensure_ascii=False))
