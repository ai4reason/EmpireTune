#!/usr/bin/python

import os
import sys
import json
import time
import hashlib
from os.path import join
from os import system

from epy import eprover
from epy import epymils
from epy.epymils import paramils, setting, enigma, eargs
from epy.epymils.log import *

setting.TIMEOUT_GLOBAL = int(os.getenv("BST_TIMEOUT_GLOBAL",10))
setting.TIMEOUT_FINETUNES = int(os.getenv("BST_TIMEOUT_FINETUNES",10))
setting.TIMEOUT_ENIGMATUNE = int(os.getenv("BST_TIMEOUT_ENIGMATUNE",10))
setting.CUTOFF = int(os.getenv("BST_CUTOFF",1))
setting.MIN_SLOTS = int(os.getenv("BST_MIN_CEFS",1))
setting.SLOTS = int(os.getenv("BST_MAX_CEFS",6))
setting.CORES = int(os.getenv("CORES",4))

EVAL_LIMIT = int(os.getenv("BST_EVAL_LIMIT",1))

setting.ITERS = 2
setting.PROBLEMS = "200"
setting.INSTANCE_FILE = "data/problems.txt"

USE_ENIGMA = False
VERIFY_ENIGMA = False
ENFORCE_ENIGMA = False   # either ENFORCE or ITER, not both!
ITER_ENIGMA = False     # use enigma-tuning in iterations after fine-tuning

best_info = None
best_params = None
update_cefs = False

def extend_cefs(cefs, params):
   "Extend cefs with CEFs from params."

   keys = [x for x in params if x.startswith("cef")]
   for key in keys:
      cef = params[key]
      if cef not in cefs:
         log("Extending CEFS with %s"%cef)
         cefs.append(cef)

def update_best(params, info):
   "Update best parameters when required."
   global best_info, best_params, start_time, iter_counter
   
   q = float(info[1])
   n = float(info[2])
   s = round(n-(q*n/10**6))
   runtime = time.time()-start_time
   #print "PROGRES: %d %d %d %d %.1f %.2f" % (iter_counter,runtime,s,n,(s/n)*100.0 if n!=0 else 0, q)

   if paramils.params_better(info, best_info):
      log("Q OUT:", ["currently best solution"])
      best_params = dict(params)
      best_info = list(info)

def training_results(proto, problems, limit, cores, samples=True):
   print "proving %d problems with limit %d on %d cores" % (len(problems), limit, cores)
   results = eprover.prover.run_parallel(proto, problems, limit, cores=cores, samples=samples)
   print
   #unsolved = [p for p in results if not results[p].solved()]
   #if unsolved:
   #   print "unsolved:\n\t", "\n\t".join(unsolved)
   #   print "protocol: ", proto
   return results

def train_enigma(results, problems, name, boost="POS3", debug=False):
   sha1 = hashlib.sha1()
   sha1.update("\n".join(problems))
   file("train.txt","w").write("\n".join(problems))
   pos = enigma.collect_pos(problems, results)
   neg = enigma.collect_neg(problems, results)
   symbols = enigma.make_symbols(pos, neg, "symbols.map")
   train = enigma.make_train(pos, neg, boost=boost)
   sha1.update("\n".join(train))
   accuracy = enigma.train()
   log("> Enigma candidate model: %s (samples=%s/%s symbols=%s trains=%s): %s"%(name,len(pos),len(neg),len(symbols),len(train),accuracy))
   enigma.save_model(name, debug=debug)
   return (name, sha1.hexdigest())

def clause(cnf):
   "Remove TPTP prefix like 'cnf(id,axiom,' ..."
   return ",".join(cnf.split(",")[2:])

def compatible(pos1, neg1, pos2, neg2, tolerance=0.02):
   #return pos1.isdisjoint(neg2) and neg1.isdisjoint(pos2)
   p = pos1.union(pos2)
   n = neg1.union(neg2)
   return len(p.intersection(n)) < tolerance*(len(p)+len(n))

def make_enigma_models(results, problems_all, problems_train):
   models = [
      train_enigma(results, problems_all, "all", boost=None, debug=True),
      train_enigma(results, problems_all, "allPOS3", boost="POS3", debug=True),
      train_enigma(results, problems_all, "allDISJ", boost="DISJ", debug=True),
      train_enigma(results, problems_all, "allDISJ3", boost="DISJ3", debug=True),
      train_enigma(results, problems_all, "allFAIR", boost="FAIR", debug=True),
      train_enigma(results, problems_train, "train", boost=None, debug=True),
      train_enigma(results, problems_train, "trainPOS3", boost="POS3", debug=True),
      train_enigma(results, problems_train, "trainDISJ", boost="DISJ", debug=True),
      train_enigma(results, problems_train, "trainDISJ3", boost="DISJ3", debug=True),
      train_enigma(results, problems_train, "trainFAIR", boost="FAIR", debug=True)
   ]
   models = {model:sha1 for (model,sha1) in models}
   
   free = list(problems_all)
   pos = {}
   neg = {}
   for problem in problems_all:
      pos[problem] = set(map(clause, results[problem]["trainpos"]))
      neg[problem] = set(map(clause, results[problem]["trainneg"]))
      #print problem, "pos", pos[problem]
      #print problem, "neg", neg[problem]
   
   i = 0
   while free:
      problem = free.pop()
      m_pos = set(pos[problem])
      m_neg = set(neg[problem])
      compat = [problem]
      for other in free:
         if compatible(m_pos, m_neg, pos[other], neg[other]):
            m_pos.update(pos[other])
            m_neg.update(neg[other])
            compat.append(other)
         #else:
         #   print "incompatible", problem, other
         #   print "p+/\m-", pos[other].intersection(m_neg)
         #   print "p-/\m+", neg[other].intersection(m_pos)
      #print "compat", compat
      (model,sha1) = train_enigma(results, compat, "compat%d"%i, boost=None, debug=True)
      models[model] = sha1
      (model,sha1) = train_enigma(results, compat, "compat%dPOS3"%i, boost="POS3", debug=True)
      models[model] = sha1
      i += 1
      free = [x for x in free if x not in compat]

   return models

def setup():
   "Read CEF collection, set up directories, and reset best found params."
   global update_cefs, best_info, best_params, start_time, iter_counter
   
   cefs = epymils.cefs.bests(50)
   if len(sys.argv) == 2:
      params = epymils.params.make_params(file(sys.argv[1]).read().strip().split())
      extend_cefs(cefs, params)
      update_cefs = True
   else:
      params = None
      update_cefs = False
      
   log("CEFS:", ["[%2d] %s"%(n,s) for (n,s) in enumerate(map(epymils.params.block2cef,cefs))])

   system("rm -fr protos")
   system("mkdir -p protos")

   best_params = None
   best_info = None

   start_time = time.time()
   iter_counter = 0

   return (cefs, params)

def register_enigma_model(params, models):
   "Assign permanent id to the temporary enigma model in params."

   slots = int(params["slots"])
   for i in range(slots):
      key = "cef%d"%i
      if params[key].startswith("Enigma"):
         cef = epymils.block2cef(params[key])
         model = cef.split(",")[1]
         if model in models:
            #name = time.strftime("%A%U%b%Y%Z")+str(int(time.time()*100))
            name = "enigmodel"+models[model] # sha1 hash
            params["cef%d"%i] = params["cef%d"%i].replace(model, name)
            log("> Enigma new model (%s): %s"%(model,name))
            enigma.rename_model(model, name)
            return name
   return None
      
def global_tune(cefs, params):
   global iter_counter
   log("\nGLOBAL_TUNE %s" % iter_counter)
   (params, info) = paramils.run_globaltune(iter_counter, cefs, params)
   update_best(params, info)
   return params

def fine_tune(cefs, params):
   global iter_counter
   log("\nFINE_TUNE %s" % iter_counter)
   (params, info) = paramils.run_finetune(iter_counter, cefs, params)
   update_best(params, info)
   return params

def enigma_tune(cefs, params, REGISTER=False):
   global iter_counter, best_params
   log("\nENIGMA_TUNE %s" % iter_counter)
   if not params:
      return None
   params = dict(params)
   # get training samples
   proto = eargs.e_proto(params)
   file("proto","w").write(proto) # for debug=True in train_enigma
   json.dump(params,file("params.json","w"),indent=3,sort_keys=True) # as well for debug
   problems_train = file("data/problems.txt").read().strip().split("\n")
   problems_all = file("data/all.txt").read().strip().split("\n")
   results = training_results(proto, problems_all, EVAL_LIMIT, setting.CORES)
   # create enigma model and run ParamILS
   models = make_enigma_models(results, problems_all, problems_train)
   (params, info) = paramils.run_enigmatune(iter_counter, cefs, params, models.keys())
   update_best(params, info)
   # save model model if best
   if params == best_params:
      register_enigma_model(params, models)
      best_params = dict(params)
   elif REGISTER:
      register_enigma_model(params, models)
   # verify results 
   if VERIFY_ENIGMA:
      log("\nVERIFY_ENIGMA: Trial runs.")
      proto = eargs.e_proto(params)
      check = training_results(proto, problems_all, EVAL_LIMIT, setting.CORES)
      for r in results:
         if "PROCESSED" in results[r]:
            left = results[r]["PROCESSED"] if results[r].solved() else "?"
         else:
            left = "-"
         if r in check and "PROCESSED" in check[r]:
            right = check[r]["PROCESSED"] if check[r].solved() else "?"
         else:
            right = "-" if r in check else "!"
         print "%s: %10s --> %10s" % (r, left, right)
   return params

def cefs_update(params):
   if update_cefs:
      for i in range(int(params["slots"])):
         cef = params["cef%d"%i]
         if not cef.startswith("Enigma"):
            epymils.cefs.used(epymils.block2cef(cef))

def run():
   global iter_counter, best_params, best_info

   (cefs, params) = setup()
   if params:
      log_params(params, "EPYMILS INPUT:")
   
   if USE_ENIGMA:
      enigma_params = enigma_tune(cefs, params, REGISTER=(not ENFORCE_ENIGMA))
      if ENFORCE_ENIGMA:
         best_params = None
         best_info = None
      else:
         params = enigma_params
   else:
      enigma_params = None

   for it in range(setting.ITERS):
      iter_counter = it+1
      params = global_tune(cefs, params)
      params = fine_tune(cefs, params)
      if ITER_ENIGMA:
         params = enigma_tune(cefs, params, REGISTER=True)

   if best_params:
      best_params = dict(best_params)
      res = ["%s %s" % (x,best_params[x]) for x in sorted(best_params.keys())]
      log("\nRESULT: %s" % (" ".join(res)))
      log_proto("best_params", best_params)
      log_params(best_params, "EPYMILS OUTPUT:")
      cefs_update(best_params)
   if ENFORCE_ENIGMA and enigma_params:
      res = ["%s %s" % (x,enigma_params[x]) for x in sorted(enigma_params.keys())]
      log("\nRESULT: %s" % (" ".join(res)))
      log_params(enigma_params, "EPYMILS ENIGMA OUTPUT:")
      log_proto("enigma", enigma_params)

run()

