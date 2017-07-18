#!/usr/bin/python

import sys
import re
import json
from os import getenv, system

from epy import eprover
from epy.epymils.params import params_update_enigmatune
from epy.epymils.eargs import e_proto

RESULT="Result for ParamILS: %(STATUS)s, %(USER_TIME)s, %(PROCESSED)s, 1000000, %(SEED)s"

def make_params_argv():
   params = {}
   i = 6+1
   while i < len(sys.argv):
      params[sys.argv[i].lstrip("-")] = sys.argv[i+1]
      i += 2
   return params

def update_result(result, seed):
   result["SEED"] = seed
   if result["STATUS"] in eprover.STATUS_OUT+["CounterSatisfiable"]:
      if "USER_TIME" in result: del result["USER_TIME"]
      if "PROCESSED" in result: del result["PROCESSED"]
   if not "USER_TIME" in result:
      result["USER_TIME"] = 100 
   if not "PROCESSED" in result:
      result["PROCESSED"] = 1000000 

def run():
   global_params = json.loads(sys.argv[1])
   limit = int(float(sys.argv[3+1]))
   problem = sys.argv[1+1]
   seed = sys.argv[5+1]
   
   enigma_params = make_params_argv()
   params_update_enigmatune(global_params, enigma_params)

   print "running eprover: %s" % problem
   proto = e_proto(global_params)
   print "proto: ", proto

   result = eprover.prover.run(proto, problem, limit, out=sys.stdout)
   update_result(result, seed)
   print RESULT % result

if len(sys.argv) < 2:
   print "usage: %s JSON instance spec time cutoff seed arg1 val1 ..." % sys.argv[0]
else:
   run()

