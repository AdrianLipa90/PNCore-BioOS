from __future__ import annotations
import hashlib, json, os, platform, shutil, statistics, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from phasenav36d.terminal36d import Terminal36D

PAYLOAD=bytes((i*131+17)&255 for i in range(288))
EXPECTED=hashlib.sha256(PAYLOAD).hexdigest()
SOURCE_EXPECTED={
 'terminal36d.py':'78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b',
 'vector_kernel.py':'68663aea2c188b77b46e5ecf2488bfdfb27a7f2cd8387fb78b6bc5dce6de0e14',
 'concept_gates.py':'a3aeda6f1ca0c445767bba8176c5b6c7d791bd97e03b33fe2ed8dccb9c97bc49',
}

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def percentile(xs,p):
    ys=sorted(xs); idx=(len(ys)-1)*p; lo=int(idx); hi=min(lo+1,len(ys)-1); f=idx-lo; return ys[lo]*(1-f)+ys[hi]*f

def summarize_us(vals_us):
    med=statistics.median(vals_us)
    return {'trials':len(vals_us),'median_us':med,'min_us':min(vals_us),'max_us':max(vals_us),'p10_us':percentile(vals_us,.1),'p90_us':percentile(vals_us,.9),'ops_per_s_from_median':1e6/med}

def timed(fn,n):
    t=time.perf_counter_ns(); last=None
    for _ in range(n): last=fn()
    dt=time.perf_counter_ns()-t
    return dt/n/1000.0,last

def host_receipted(payload):
    started=time.time_ns(); op='HASH'; allowed={'HASH':hashlib.sha256}; fn=allowed[op]
    digest=fn(payload).hexdigest()
    r={'schema':'HOST_RECEIPT_V1','operation':op,'status':'PASS','digest':digest,'started_unix_ns':started,'finished_unix_ns':time.time_ns()}
    r['receipt_sha256']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return r

def main():
    try: os.sched_setaffinity(0,{0})
    except Exception: pass
    actual={k:sha_file(ROOT/'phasenav36d'/k) for k in SOURCE_EXPECTED}
    if actual != SOURCE_EXPECTED: raise SystemExit(f'FAIL_SOURCE_HASH {actual}')
    t36=Terminal36D()
    packet={'schema':'PHASENAV_ACTION_PACKET_V1','action_id':'HEAD_TO_HEAD_V0_1','operation':'PHASENAV_HASH_BATCH','intent':'hash inspect','payload':{'items':[PAYLOAD]}}
    assert t36.hash_batch({'items':[PAYLOAD]})['sha256'][0] == EXPECTED
    r=t36.execute(packet); assert r['status']=='PASS' and r['result']['sha256'][0]==EXPECTED
    for _ in range(3000): t36.hash_batch({'items':[PAYLOAD]}); t36.execute(packet); host_receipted(PAYLOAD)
    bio_direct=[]; bio_full=[]; host_receipt=[]
    for _ in range(7):
        x,last=timed(lambda:t36.hash_batch({'items':[PAYLOAD]}),50000); assert last['sha256'][0]==EXPECTED; bio_direct.append(x)
        x,last=timed(lambda:t36.execute(packet),20000); assert last['status']=='PASS' and last['result']['sha256'][0]==EXPECTED; bio_full.append(x)
        x,last=timed(lambda:host_receipted(PAYLOAD),50000); assert last['digest']==EXPECTED; host_receipt.append(x)
    native={}; exe=ROOT/'linux_native_bench'
    for _ in range(5):
        cp=subprocess.run([str(exe),'20000'],check=True,text=True,capture_output=True)
        for line in cp.stdout.strip().splitlines():
            name,ns,ops=line.split(); native.setdefault(name,[]).append(float(ns)/1000.0)
    sha256sum=shutil.which('sha256sum'); forkexec=[]
    if sha256sum:
        for _ in range(5):
            n=250; t0=time.perf_counter_ns(); last=None
            for __ in range(n):
                cp=subprocess.run([sha256sum],input=PAYLOAD,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=True)
                last=cp.stdout.split()[0].decode()
            dt=time.perf_counter_ns()-t0; assert last==EXPECTED; forkexec.append(dt/n/1000.0)
    results={'bioos_direct_hash_batch':summarize_us(bio_direct),'bioos_terminal36d_full_execute':summarize_us(bio_full),'host_conventional_receipted_dispatch':summarize_us(host_receipt)}
    for name,vals in native.items(): results[name]=summarize_us(vals)
    if forkexec: results['linux_fork_exec_sha256sum']=summarize_us(forkexec)
    bio=results['bioos_terminal36d_full_execute']['median_us']; direct=results['bioos_direct_hash_batch']['median_us']
    for v in results.values(): v['ratio_vs_bioos_full']=v['median_us']/bio; v['ratio_vs_bioos_direct']=v['median_us']/direct
    uname=platform.uname(); cpu='UNKNOWN'
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'): cpu=line.split(':',1)[1].strip(); break
    except Exception: pass
    payload={'schema':'BIOOS_LINUX_HEAD_TO_HEAD_V0_1','status':'PASS_HOST_REFERENCE','claim_boundary':'same-host latency benchmark; BioOS is current Python host runtime, Linux controls include native C/OpenSSL; not bare-metal BioOS or universal Linux performance','payload_bytes':len(PAYLOAD),'payload_sha256':EXPECTED,'cpu':cpu,'kernel':uname.release,'python':platform.python_version(),'affinity_main':[0],'native_ipc_worker_cpu':1,'source_sha256':actual,'compiler_command':'gcc -O3 -march=native -Wall -Wextra src/linux_native_bench.c -lcrypto','results':results,'notes':['tmpfs path uses pwrite+pread+SHA256 without fsync; it is not a durability benchmark','shared-mmap, pipe, and Unix-socket controls use a persistent worker process and SHA256 in native C/OpenSSL','fork-exec control launches /usr/bin/sha256sum for every operation','Terminal36D receipts are not persisted to disk in this benchmark','no timings are subtracted for loop overhead'],'canon_allowed':False,'epistemic':'MEASURED_HOST_REFERENCE'}
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(); payload['receipt_sha256']=hashlib.sha256(raw).hexdigest()
    out=ROOT/'results'/'BIOOS_LINUX_HEAD_TO_HEAD_V0_1.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps(payload,indent=2,sort_keys=True))

if __name__=='__main__': main()
