import os, sys, random, contextlib, io, csv, statistics
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.environ.get('ROBO_SRC', os.path.join(HERE,'src'))
sys.path.insert(0,SRC)
import networld, taxi, dispatcher, ruparams, node

def run_one(seed):
    random.seed(seed); np.random.seed(seed)
    original_default_rng=np.random.default_rng
    original_pickup=node.Node.pickupFare
    counter_rng={'n':0}
    def seeded_default_rng(*args, **kwargs):
        if args or 'seed' in kwargs: return original_default_rng(*args, **kwargs)
        counter_rng['n'] += 1
        return original_default_rng(seed*1000+counter_rng['n'])
    np.random.default_rng=seeded_default_rng
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            world=networld.NetWorld(x=ruparams.worldX,y=ruparams.worldY,runtime=ruparams.runTime,
                fareprob=ruparams.fGenDefault,jctNodes=ruparams.junctions,edges=ruparams.streets,
                interpolateNodes=True,farefile=None)
            counters={'requests':0,'cancelled':0,'completed':0,'pickups':0}
            def counted_pickup(self,*a,**kw):
                result=original_pickup(self,*a,**kw)
                if result is not None: counters['pickups']+=1
                return result
            node.Node.pickupFare=counted_pickup
            original_insert,original_remove,original_complete=world.insertFare,world.removeFare,world.completeFare
            def counted_insert(*a,**kw):
                counters['requests']+=1; return original_insert(*a,**kw)
            def counted_remove(*a,**kw):
                counters['cancelled']+=1; return original_remove(*a,**kw)
            def counted_complete(*a,**kw):
                counters['completed']+=1; return original_complete(*a,**kw)
            world.insertFare=counted_insert; world.removeFare=counted_remove; world.completeFare=counted_complete
            service_map=world.exportMap()
            starts=[(20,0),(49,15),(15,49),(0,35)]
            taxis=[taxi.Taxi(world=world,taxi_num=100+i,service_area=service_map,start_point=p) for i,p in enumerate(starts)]
            disp=dispatcher.Dispatcher(parent=world,taxis=taxis)
            world.addDispatcher(disp)
            for t in taxis: t.comeOnDuty()
            outputs={'time':[],'fares':{},'taxis':{}}
            import threading
            lock=threading.Lock()
            for _ in range(ruparams.runTime): world.runWorld(ticks=1,outputs=outputs,outlock=lock)
        accounts=[float(t._account) for t in taxis]
        duty=[sum(1 for timeline in outputs['taxis'].values() if minute in timeline) for minute in range(ruparams.runTime)]
        row={'Run':seed,'Taxi 100':accounts[0],'Taxi 101':accounts[1],'Taxi 102':accounts[2],'Taxi 103':accounts[3],
             'Dispatcher':float(disp._revenue),'Joint':sum(accounts)+float(disp._revenue),
             'Requests':counters['requests'],'Pickups':counters['pickups'],'Completed':counters['completed'],
             'Cancelled':counters['cancelled'],'Cancellation rate':counters['cancelled']/counters['requests'] if counters['requests'] else 0,
             'Average taxis on duty':sum(duty)/len(duty)}
        return row,duty
    finally:
        np.random.default_rng=original_default_rng
        node.Node.pickupFare=original_pickup

rows=[]; duty_series=[]
for seed in range(20261013,20261018):
    row,duty=run_one(seed); rows.append(row); duty_series.append(duty)
    print('completed',seed,row)
label=os.environ.get('ROBO_LABEL','improved')
outdir=os.path.join(HERE,'results','week3_dispatcher'); os.makedirs(outdir,exist_ok=True)
with open(os.path.join(outdir,label+'_raw.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open(os.path.join(outdir,label+'_duty_timeseries.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['Minute']+[f'Trial {i+1}' for i in range(len(rows))]+['Average'])
    for minute in range(ruparams.runTime):
        vals=[series[minute] for series in duty_series]
        w.writerow([minute+1]+vals+[sum(vals)/len(vals)])
print('wrote results for',label)
