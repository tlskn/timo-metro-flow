import argparse
from pathlib import Path
from train import prepare
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--history');a=p.parse_args()
h=prepare(a.history) if a.history else None
result=prepare(a.input,history=h)
if h is not None:
    incoming=prepare(a.input)
    keys=set(zip(incoming.station,incoming.line,incoming.t))
    result=result[[k in keys for k in zip(result.station,result.line,result.t)]]
result.to_csv(a.output,index=False)
print(len(result))
