from multiprocessing import Pool
import sys
from os.path import join

import benchmark
import protocol
import scheduler
import prover

OUT = sys.stdout

def _run_proto(arg):
   result = prover.run(arg[0], arg[1], arg[2], samples=arg[3])
   report(result)
   return result

def _run_pid(arg):
   result = protocol.run(arg[0], arg[1], arg[2])
   report(result)
   return result

def _run_sid(arg):
   result = scheduler.run(arg[0], arg[1], arg[2])
   report(result)
   return result

def report(result):
   if OUT:
      if result.failed():
         OUT.write("!")
      else:
         OUT.write("+" if result.solved() else "-")
      OUT.flush()

def parallel(wrapper, id, problems, limit, cores=4, samples=False, thepool=None):
   n = len(problems)
   pool = Pool(cores) if not thepool else thepool
   args = zip([id]*n,problems,[limit]*n,[samples]*n) 
   results = pool.map(wrapper, args)
   if not thepool:
      pool.close()
      pool.join()
   return {x:y for (x,y) in zip(problems, results)}

def parallel_proto(proto, problems, limit, cores=4, samples=False, thepool=None):
   return parallel(_run_proto, proto, problems, limit, cores, samples, thepool)

def parallel_pid(pid, problems, limit, cores=4):
   return parallel(_run_pid, pid, problems, limit, cores)

def parallel_sid(sid, problems, limit, cores=4):
   return parallel(_run_sid, sid, problems, limit, cores)


