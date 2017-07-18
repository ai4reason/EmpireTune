#!/usr/bin/python

import sys
import json
import commands
import vampiretools

RESULT="\nResult for ParamILS: %(STATUS)s, %(USER_TIME)s, %(PROCESSED)s, 1000000, %(SEED)s"
CMD="perf stat -e task-clock:up,page-faults:up,instructions:up vampire --statistics full -m 2048 -t %ds %s %s%s"
PREFIX="/home/yan/atp/benchmarks/" # sorry

def make_cmd(params, limit, problem):
   cmd = vampiretools.vampire_cmd(params)
   return CMD % (limit, cmd, PREFIX, problem)
   
def make_result(output, limit, seed):
   result = {}
   result["STATUS"] = "Terminated"
   result["USER_TIME"] = limit
   for line in output.split("\n"):
      if line == "Termination reason: Refutation":
         result["STATUS"] = "Theorem"
      #elif line.startswith("Passive clauses: "):
      #elif line.startswith("Generated clauses: "):
      #   result["PROCESSED"] = int(line.split(":")[1])
      elif line.startswith("Time elapsed: "):
         result["USER_TIME"] = float(line.split(":")[1].rstrip("s"))
      elif "instructions:up" in line:
         result["PROCESSED"] = int(line.split()[0].replace(",",""))/1000000
   if result["STATUS"] != "Theorem":
      result["PROCESSED"] = 1000000
   #else:
   #   result["PROCESSED"] = int(result["USER_TIME"]*1000)
   result["SEED"] = seed
   return result

def run():
   limit = int(float(sys.argv[4]))
   problem = sys.argv[2]
   seed = sys.argv[6]
   params_global = vampiretools.make_params(sys.argv[7:])
   params_order = json.loads(sys.argv[1])

   params = vampiretools.join_params(params_global, params_order)
   params = vampiretools.clean_params(params)

   cmd = make_cmd(params, limit, problem) 
   print "running vampire: %s" % cmd
   output = commands.getoutput(cmd)
   print output
   result = make_result(output, limit, seed)

   #if "User error" in output or "WARNING" in output:
   #   if not "does not exist." in output:
   #      log = file("/home/yan/vampire-errors.log","a")
   #      log.write(("running vampire: %s\n\n"%cmd)+output+"\n"+(RESULT%result)+"\n\n\n")
   #      log.close()

   print RESULT % result

if len(sys.argv) < 2:
   print "usage: %s JSON instance spec time cutoff seed arg1 val1 ..." % sys.argv[0]
else:
   run()

