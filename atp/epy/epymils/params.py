"""
Create ParamILS parameter files.
"""

import setting
from .data import *

def make_cef(weight, fparams, prefix=""):
   """Return CEF with weight function and arguments from `fparams` in format {arg:val}.

   Keys in fparams for each weigth function are specified in WEIGHTS.
   Optinally prefix fparams keys with prefix.
   """
   args = [x.split(":")[0] for x in setting.WEIGHTS[weight].split(" ")]
   args = [fparams[prefix+x] for x in args]
   return "%s(%s)" % (weight, ",".join(args))

def make_params(lparams):
   "Translate list [key, val, ...] to dict {key:val}."
   params = {}
   i = 0
   while i < len(lparams):
      try:
         params[lparams[i]] = lparams[i+1]
      except:
         raise Exception(str(lparams))
      i += 2
   return params

def read_params(f_params):
   lparams = file(f_params).read().rstrip().split(" ")
   return make_params(lparams)

def cefs_args(slots, cefs):
   """Return ParamILS parameters for tunning with n slots and `cefs` collection.
   
   Define argument "slot" for the number of slots (positions for CEFs).
   For each slot i define arguments "freq_i" and "cef_i" with frequency
   and CEF at slot i.
   Count CEFs from 0.
   Set default for "slot" to MIN_SLOTS, for "freq_i" to 1, and for "cef_i" to the
   i-th CEF (usually we have much more CEFs than slots).
   """

   args = [Arg("slots",Domain(*[str(x) for x in range(setting.MIN_SLOTS,slots+1)]),str(setting.MIN_SLOTS))]
   for i in range(slots):
      args += [Arg("freq%d"%i, setting.DOMAIN["freq"], "1")]
      args += [Arg("cef%d"%i, cefs, cefs[i])]
   return Parameters(*args)

def cefs_conditions(slots, cefs):
   "Return conditions for cefs (cef_i is used when i<slots)."

   conditions = []
   for i in range(setting.MIN_SLOTS,slots):
       dom = ",".join(map(str,range(i+1,slots+1)))
       conditions += [Condition("freq%d"%i, "slots", dom)]
       conditions += [Condition("cef%d"%i, "slots", dom)]
   return Parameters(*conditions)

def cefs_forbiddens(slots, cefs):
   "Return forbidden values for cefs (same CEF at different positions)."

   forbiddens = []
   for n in range(setting.MIN_SLOTS,slots+1):
      forbiddens += ["#%d" % n]
      ns = range(0,n)
      pairs = [(i,j) for i in ns for j in ns if i<j]
      for cef in cefs:
         for (i,j) in pairs:
            forbiddens += [Forbidden("slots",n,"cef%d"%i,cef,"cef%d"%j,cef)]
   return Parameters(*forbiddens)

def params_size(params):
   sizes = [str(arg[1]).count(",")+1 for arg in params if type(arg) is Arg]
   total = reduce(lambda x,y:x*y, sizes) if sizes else 0
   # FIXME: count conditionals and forbiddens
   return total

def params_update_finetune(global_params, tunes_params):
   "Update global parameters with the result of fine tuning."

   slots = int(global_params["slots"])
   ret = {}
   for i in range(slots):
      cef_key = "cef%d"%i
      cef_old = global_params[cef_key]
      if cef_old.startswith("Enigma"):
         continue
      weight = cef_old.split("__")[0]
      cef_new = make_cef(weight, tunes_params, prefix=cef_key+"_")
      cef_new = cef2block(cef_new)

      global_params[cef_key] = cef_new
      if cef_old != cef_new:
         ret[cef_old] = cef_new
   return ret

def params_update_enigmatune(global_params, enigma_params):
   "Update global parameters with the result of enigma tuning."

   slot = int(global_params["slots"])
   global_params["slots"] = str(slot+1)
   prio = enigma_params["prio"]
   mult = enigma_params["mult"]
   model = enigma_params["model"]
   global_params["cef%d"%slot] = cef2block("Enigma(%s,%s,%s)" % (prio,model,mult))
   global_params["freq%d"%slot] = enigma_params["freq"]

def params_set_default(params, defaults):
   "Set default values to params in format [(name,values,default)]."

   for param in sorted(params):
      if not isinstance(param, Arg):
         continue
      if param[0] in defaults:
         param[2] = defaults[param[0]]
      #if param[2].startswith("Enigma"):
      #   print "epymils: Disabling removing Enigma CEF: %s" % param[2]
      #   param[1] = Domain(*[param[2]])
      if param[2] not in param[1]:
         # add default to the list of values
         dom = param[1]
         dom = dom.split(",") if isinstance(param[1],str) else dom
         dom = Domain(*dom)
         dom.append(param[2])
         param[1] = dom
         print "epymils: Extending domain of %s by %s" % (param[0], param[2])

def params_globaltune(slots, cefs):
   "Prepare ParamILS parameters for global tuning with len(slots) CEF slots."
   cefs = Domain(*cefs)
   parts = setting.ARGS + cefs_args(slots,cefs)+\
      setting.CONDITIONS + cefs_conditions(slots,cefs)+\
      setting.FORBIDDENS + cefs_forbiddens(slots,cefs)
   return Parameters(*parts)

def params_finetune_cef(cef, prefix=""):
   "Prepare ParamILS parameters for fine tuning of one CEF."

   wargs = cef.replace("_M_","-").replace("_D_",".").split("__")
   weight = wargs.pop(0)
   args = []
   argtyps = [x.split(":") for x in setting.WEIGHTS[weight].split(" ") if x]
   for (arg,typ) in argtyps:
      dom = setting.DOMAIN[typ]
      #default = str(dom).split(",")[0] # yeah, ugly
      default = wargs.pop(0)
      args += [Arg(prefix+arg,dom,default)]
   return Parameters(*args)

def params_finetune(params):
   "Prepare ParamILS parameters for fine tuning of global `params`."

   slots = int(params["slots"])
   args = []
   for i in range(slots):
      if params["cef%d"%i].startswith("Enigma"):
         continue 
      args += ["#"+params["cef%d"%i]] # just a comment
      args += params_finetune_cef(params["cef%d"%i],"cef%d_"%i)
   return Parameters(*args)

def params_enigmatune(params, models):
   "Prepare ParamILS parameters for tuning enigma CEFs with global `params`."

   args = [Arg("prio", setting.DOMAIN["prio"], "ConstPrio"),
           Arg("freq", Domain("30","40","50","75","100","150"), "30"),
           Arg("model", Domain(*models), models[0]),
           Arg("mult", setting.DOMAIN["mult"],"0.2")]
   return Parameters(*args)

