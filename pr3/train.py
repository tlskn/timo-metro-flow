from pathlib import Path
import pandas as pd,numpy as np,json,time,hashlib,platform,joblib,sklearn
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge,Lasso
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.base import clone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'reports'; OUT.mkdir(exist_ok=True); (ROOT/'models').mkdir(exist_ok=True)
SOURCE=ROOT/'data/initial.csv'
NUM=['lag2','lag4','mean4','growth','sin_q','cos_q','age']; CAT=['station','line']
def prepare(path,history=None):
    d=pd.read_csv(path,sep=';'); d=d.rename(columns={'Metro station name':'station','Line name':'line','Incoming passengers':'y'})
    d['q']=d.Quarter.map({'I квартал':1,'II квартал':2,'III квартал':3,'IV квартал':4}); d['t']=(d.Year-2021)*4+d.q-1
    if history is not None: d=pd.concat([history,d],ignore_index=True)
    d=d.drop_duplicates(['station','line','t']).sort_values(['station','line','t']).copy()
    d=d[d.y.ge(0)&d.station.notna()&d.line.notna()]
    service_pairs = {
        ('Библиотека имени Ленина', 'Сокольническая линия'),
        ('Киевская', 'Филёвская линия'),
        ('Китай-город', 'Таганско-Краснопресненская линия'),
        ('Петровско-Разумовская', 'Серпуховско-Тимирязевская линия'),
        ('Тверская', 'Замоскворецкая линия'),
        ('Театральная', 'Замоскворецкая линия'),
        ('Третьяковская', 'Калужско-Рижская линия'),
    }
    d = d[[pair not in service_pairs for pair in zip(d.station, d.line)]]
    lookup=d.set_index(['station','line','t']).y.to_dict()
    for lag in [2,3,4,5]: d['lag'+str(lag)]=[lookup.get((s,l,t-lag),np.nan) for s,l,t in zip(d.station,d.line,d.t)]
    d['mean4']=d[['lag2','lag3','lag4','lag5']].mean(axis=1)
    d['growth']=d.lag2/d.lag5.replace(0,np.nan)-1
    d['sin_q']=np.sin(2*np.pi*d.q/4); d['cos_q']=np.cos(2*np.pi*d.q/4)
    d['age']=d.t-d.groupby(['station','line']).t.transform('min')
    return d.replace([np.inf,-np.inf],np.nan)
def pipe(model,nums=NUM):
    pre=ColumnTransformer([('num',Pipeline([('fill',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])
    return Pipeline([('pre',pre),('model',model)])
def metrics(y,p):
    p=np.maximum(p,0); e=np.asarray(y)-p
    return dict(WAPE=100*np.abs(e).sum()/np.asarray(y).sum(),MAE=np.abs(e).mean(),RMSE=np.sqrt((e*e).mean()))
def run():
    d=prepare(SOURCE); d=d[d.t>=5].copy(); train=d[d.t<=10]; test=d[d.t>=12]
    folds=[7,8,9,10]; rows=[]; details=[]; estimators={}; predictions=[]
    configs=[('Ridge '+str(a),Ridge(alpha=a)) for a in [.1,1,10,100]]+ [('Lasso '+str(a),Lasso(alpha=a,max_iter=10000,tol=.001)) for a in [100,1000,10000,100000]]
    configs += [('KNN '+str(k),KNeighborsRegressor(n_neighbors=k)) for k in [5,15,30]]
    configs += [('Tree '+str(k),DecisionTreeRegressor(max_depth=k,min_samples_leaf=5,random_state=42)) for k in [2,4,6,8,12,None]]
    configs += [('Forest '+str(k),RandomForestRegressor(n_estimators=100,max_depth=k,min_samples_leaf=3,random_state=42,n_jobs=2)) for k in [6,12]]
    configs += [('Boost '+str(k),HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=k,learning_rate=.05,l2_regularization=1,random_state=42)) for k in [7,15,31]]
    configs += [('Ridge short '+str(a),Ridge(alpha=a)) for a in [.1,1,10,100]]
    for name,model in [('Seasonal',None)]+configs:
        vals=[]; seconds=0; nonzero=[]
        for v in folds:
            tr=train[train.t<=v-2]; va=train[train.t==v]; start=time.perf_counter()
            if model is None: pred=va.lag4.fillna(tr.y.median()).to_numpy(); fitpred=tr.lag4.fillna(tr.y.median()).to_numpy()
            else:
                p=pipe(clone(model),['lag2','lag4'] if name.startswith('Ridge short') else NUM); p.fit(tr[NUM+CAT],tr.y); pred=p.predict(va[NUM+CAT]); fitpred=p.predict(tr[NUM+CAT]);
                if hasattr(p['model'],'coef_'): nonzero.append(int((np.abs(p['model'].coef_)>1e-7).sum()))
            elapsed=time.perf_counter()-start; seconds+=elapsed; m=metrics(va.y,pred); vals.append(m)
            details.append(dict(model=name,fold=v,train_max=int(tr.t.max()),n_train=len(tr),n_valid=len(va),seconds=elapsed,train_WAPE=metrics(tr.y,fitpred)['WAPE'],**m))
            if name=='Seasonal': predictions.extend([dict(t=v,y=float(y),prediction=float(z)) for y,z in zip(va.y,pred)])
        r=dict(model=name,**{k:float(np.mean([m[k] for m in vals])) for k in vals[0]},std_WAPE=float(np.std([m['WAPE'] for m in vals])),seconds=seconds,nonzero=float(np.mean(nonzero)) if nonzero else None)
        rows.append(r); estimators[name]=model; print(name,round(r['WAPE'],3),flush=True)
    results=pd.DataFrame(rows).sort_values('WAPE'); results.to_csv(OUT/'experiments.csv',index=False); pd.DataFrame(details).to_csv(OUT/'folds.csv',index=False)
    best_wape=results.WAPE.min(); eligible=results[results.WAPE < best_wape + 0.1].copy(); eligible['complexity']=eligible.model.map(lambda x: 0 if x=='Seasonal' else 1 if x.startswith(('Ridge','Lasso')) else 2 if x.startswith('Tree') else 3 if x.startswith('KNN') else 4); winner=eligible.sort_values(['complexity','seconds']).iloc[0]['model']; best=pipe(clone(estimators[winner]),['lag2','lag4'] if winner.startswith('Ridge short') else NUM); best.fit(train[NUM+CAT],train.y); joblib.dump(best,ROOT/'models/model_v1.joblib')
    a=prepare(SOURCE); b=prepare(SOURCE); repeat=a.equals(b); reloaded=joblib.load(ROOT/'models/model_v1.joblib'); same=np.array_equal(best.predict(train[NUM+CAT]),reloaded.predict(train[NUM+CAT]))
    ridge=pipe(Ridge(alpha=10)); ridge.fit(train[NUM+CAT],train.y); coef=pd.DataFrame({'feature':ridge['pre'].get_feature_names_out(),'coefficient':ridge['model'].coef_}); coef.to_csv(OUT/'coefficients.csv',index=False)
    meta=dict(winner=winner,seed=42,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),versions=dict(python=platform.python_version(),sklearn=sklearn.__version__,pandas=pd.__version__,numpy=np.__version__),train_rows=len(train),test_rows=len(test),raw_rows=len(pd.read_csv(SOURCE,sep=';')),clean_rows=len(a),usable_rows=len(d),repeat=repeat,reload_identical=same,features=(['lag2','lag4'] if winner.startswith('Ridge short') else NUM)+CAT,test_periods=sorted(test.t.unique().tolist()),parameters=best['model'].get_params(),created=pd.Timestamp.now().isoformat())
    (ROOT/'models/model_v1.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8'); (OUT/'summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(9,6)); sub=results[~results.model.str.endswith('новых')]; ax.barh(sub.model,sub.WAPE); ax.invert_yaxis(); ax.set_xlabel('WAPE, %'); fig.tight_layout(); fig.savefig(OUT/'comparison.png',dpi=160); plt.close(fig)
    det=pd.DataFrame(details); fig,ax=plt.subplots(figsize=(7,4)); sub=det[det.model.str.startswith('Tree')].groupby('model',sort=False)[['WAPE','train_WAPE']].mean(); sub.plot(ax=ax,marker='o'); ax.set_ylabel('WAPE, %'); ax.set_xlabel('Глубина дерева'); fig.tight_layout(); fig.savefig(OUT/'depth.png',dpi=160); plt.close(fig)
if __name__=='__main__': run()
