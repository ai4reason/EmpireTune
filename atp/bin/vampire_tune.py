#!/usr/bin/python -u

import sys
import math
import json
from os import system, getenv
from os.path import join, exists

from epy.epymils import paramils, scenario, data
from epy.epymils.params import params_size

import vampiretools

TIMEOUT_GLOBAL = int(getenv("BST_TIMEOUT_GLOBAL",10))
TIMEOUT_ORDER = int(getenv("BST_TIMEOUT_ORDERTUNE",10))
CUTOFF = int(getenv("BST_CUTOFF",1))
CORES = int(getenv("CORES",4))

#EVAL_LIMIT = int(getenv("BST_EVAL_LIMIT",1))

PROBLEMS = "200"
INSTANCE_FILE = "data/problems.txt"

def setup():
   init = file(sys.argv[1]).read().strip().split()
   params = vampiretools.make_params(init)
   (params_global, params_order) = vampiretools.split_params(params)
   return (params_global, params_order)

def log(msg):
   sys.stdout.write(msg+"\n")
   sys.stdout.flush()

def log_params(params, label, delim):
   cmd = " ".join(["%s%s%s"%(x,delim,params[x]) for x in sorted(params)])
   log("%s: %s"%(label,cmd))

def vampire_tune_global(params_global, params_order):

   d_global = "iter-00-global"
   if exists(d_global):
      system("rm -fr %s" % d_global)
   system("mkdir -p %s" % d_global)

   binary = "vampire_wrapper_globaltune.py %s" % repr(json.dumps(params_order))
   scenar = scenario.scenario_globaltune(CUTOFF, TIMEOUT_GLOBAL if TIMEOUT_GLOBAL!=0 else 9999, d_global, INSTANCE_FILE, bin=binary)
   vamparams = vampiretools.vampire_params_global(params_global)
   log("Prameter space size: 10^%.2f" % math.log(params_size(vamparams),10))
   
   f_scenario = join(d_global, "scenario.txt")
   f_params = join(d_global, "params.txt")
   d_output = join(d_global, "paramils-out")

   file(f_scenario,"w").write(scenar)
   file(f_params,"w").write(str(vamparams))
   
   if TIMEOUT_GLOBAL == 0:
      probs = len(file(INSTANCE_FILE).readlines())
      out_params = paramils.run_reparamils(f_scenario,d_output,count=CORES,N=probs,validN="0",init="1",out=None)
   else:
      out = file(join(d_global,"paramils.out"),"w")
      paramils.run_paramils(f_scenario,count=CORES,N=PROBLEMS,validN="0",init="1",out=out)
      out.close()
      (out_params, out_info) = paramils.params_best(d_output)
      log("Q OUT: T = %ss Q =%s # =%s" % (int(float(out_info[0])),out_info[1],out_info[2]))
   
   (in_params, in_info) = paramils.params_best(d_output, select_index=1)
   log_params(in_params, "REAL INPUT    ", "=")
   out_params = vampiretools.clean_params(out_params)

   return out_params # developed version of global params

def vampire_tune_order(params_global, params_order):

   d_global = "iter-01-order"
   if exists(d_global):
      system("rm -fr %s" % d_global)
   system("mkdir -p %s" % d_global)

   binary = "vampire_wrapper_ordertune.py %s" % repr(json.dumps(params_global))
   scenar = scenario.scenario_globaltune(CUTOFF, TIMEOUT_ORDER if TIMEOUT_ORDER!=0 else 9999, d_global, INSTANCE_FILE, bin=binary)
   vamparams = vampiretools.vampire_params_order(params_order)
   log("Prameter space size: 10^%.2f" % math.log(params_size(vamparams),10))
   
   f_scenario = join(d_global, "scenario.txt")
   f_params = join(d_global, "params.txt")
   d_output = join(d_global, "paramils-out")

   file(f_scenario,"w").write(scenar)
   file(f_params,"w").write(str(vamparams))
   
   if TIMEOUT_ORDER == 0:
      probs = len(file(INSTANCE_FILE).readlines())
      out_params = paramils.run_reparamils(f_scenario,d_output,count=CORES,N=probs,validN="0",init="1",out=None)
   else:
      out = file(join(d_global,"paramils.out"),"w")
      paramils.run_paramils(f_scenario,count=CORES,N=PROBLEMS,validN="0",init="1",out=out)
      out.close()
      (out_params, out_info) = paramils.params_best(d_output)
      log("Q OUT: T = %ss Q =%s # =%s" % (int(float(out_info[0])),out_info[1],out_info[2]))
   
   (in_params, in_info) = paramils.params_best(d_output, select_index=1)
   log_params(in_params, "REAL INPUT    ", "=")
   out_params = vampiretools.clean_params(out_params)

   return out_params # developed version of order params

def run():

   (params_global, params_order) = setup()
   log_params(params_global, "VAMPILS INPUT (global) ", "=")
   log_params(params_order, "VAMPILS INPUT (order)  ", "=")

   params_global = vampire_tune_global(params_global, params_order)
   log_params(params_global, "VAMPILS OUTPUT (GLOBAL) ", "=")

   params_order = vampire_tune_order(params_global, params_order)
   log_params(params_order, "VAMPILS OUTPUT (ORDER)  ", "=")
   log_params(params_global, "VAMPILS OUTPUT (global) ", "=")

   params = vampiretools.join_params(params_global, params_order)
   params = vampiretools.clean_params(params)
   log_params(params, "\nRESULT", " ")

run()

