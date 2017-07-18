from copy import deepcopy
from epy.epymils.data import Parameters, Arg, Domain, Condition, Forbidden
from epy.epymils.params import params_set_default

STATIC_VAMPIRE_PARAMS = Parameters(
   Arg("sa", Domain("discount","inst_gen","lrs","otter"), "lrs"),
   Arg("erd", Domain("off","input_only"), "off"),
   Arg("fde", Domain("all","none","unused"), "all"),
   Arg("gsp", Domain("input_only","off"), "off"),
   Arg("ins", Domain("0","1","2","4","8"), "0"),
   Arg("nm", Domain("2","4","8","26","32","64"), "8"),
   Arg("ss", Domain("axioms","included","off","priority"), "off"),
   Arg("sd", Domain("0","1","2","3","4"), "0"),
   Arg("sgt", Domain("0","1","2","3","4"), "0"),
   Arg("st", Domain("0","1","2","3","4"), "1"),
   Arg("sos", Domain("all","off","on"), "off"),
   Arg("awr", Domain("8_1","5_1","4_1","3_1","2_1","3_2","5_4","1","2_3","2","3","4","5","6","7","8","10","12","14","16","20","24","28","32","40","50","64","128","1024"), "1"),
   Arg("lcm", Domain("predicate","reverse","standard"), "standard"),
   Arg("s", Domain("0","1","2","3","4","10","11","1002","1003","1004","1010","1011","_1","_2","_3","_4","_10","_11","_1002","_1003","_1004","_1010"), "10"),
   Arg("bd", Domain("all","off","preordered"), "all"),
   Arg("bs", Domain("off","on","unit_only"), "off"),
   Arg("bsr", Domain("off","on","unit_only"), "off"),
   Arg("cond", Domain("fast","off","on"), "off"),
   Arg("drc", Domain("on","off"), "on"),
   Arg("er", Domain("filter","known","off"), "off"),
   Arg("fd", Domain("all","off","preordered"), "all"),
   Arg("fs", Domain("on","off"), "on"),
   Arg("fsr", Domain("on","off"), "on"),
   Arg("gs", Domain("on","off"), "off"),
   Arg("urr", Domain("ec_only","off","on"), "off"),
   Arg("bce", Domain("on","off"), "off"),
   Arg("updr", Domain("on","off"), "on"),
   #
   #
   # --newcnf on|off 
   #
   Arg("av", Domain("on","off"), "on"),
   Arg("aac", Domain("ground","none"), "ground"),
   Arg("acc", Domain("model","off","on"), "off"),
   Arg("anc", Domain("all","all_dependent","known","none"), "known"),
   Arg("sas", Domain("minisat","vampire","z3"), "vampire"),
   #
   Condition("sd", "ss", "axioms,included,priority"),
   Condition("sgt", "ss", "axioms,included,priority"),
   Condition("st", "ss", "axioms,included,priority"),
   Condition("er", "ins", "0"),
   #
   Condition("aac", "av", "on"),
   Condition("acc", "av", "on"),
   Condition("anc", "av", "on"),
   #
   Forbidden("fs", "off", "fsr", "on"),
   Forbidden("sa", "inst_gen", "av", "on"),
   Forbidden("acc", "on", "sas", "z3"),
   Forbidden("acc", "model", "sas", "z3")
)

VAMPIRE_PARAMS_ORDER = Parameters(
   #
   Arg("spmode", Domain("coefs","user"), "coefs"),
   Arg("spoc", Domain("_10","_8","_6","_4","_3","_2","_1","0","1","2","3","4","6","8","10"), "1"),
   Arg("spac", Domain("_10","_8","_6","_4","_3","_2","_1","0","1","2","3","4","6","8","10"), "0"),
   Arg("spfc", Domain("_10","_8","_6","_4","_3","_2","_1","0","1","2","3","4","6","8","10"), "0"),
   #
   Arg("spuc_identity", Domain("1","2","3","4","5","6","7","8","9","10"), "1"),
   Arg("spuc_multiply", Domain("1","2","3","4","5","6","7","8","9","10"), "2"),
   Arg("spuc_associator", Domain("1","2","3","4","5","6","7","8","9","10"), "3"),
   Arg("spuc_commutator", Domain("1","2","3","4","5","6","7","8","9","10"), "4"),
   Arg("spuc_left_division", Domain("1","2","3","4","5","6","7","8","9","10"), "5"),
   Arg("spuc_right_division", Domain("1","2","3","4","5","6","7","8","9","10"), "6"),
   Arg("spuc_left_inner_mapping", Domain("1","2","3","4","5","6","7","8","9","10"), "7"),
   Arg("spuc_right_inner_mapping", Domain("1","2","3","4","5","6","7","8","9","10"), "8"),
   Arg("spuc_middle_inner_mapping", Domain("1","2","3","4","5","6","7","8","9","10"), "9"),
   Arg("spuc_sK", Domain("1","2","3","4","5","6","7","8","9","10"), "10"),
   #
   Condition("spoc", "spmode", "coefs"),
   Condition("spac", "spmode", "coefs"),
   Condition("spfc", "spmode", "coefs"),
   Condition("spuc_identity", "spmode", "user"),
   Condition("spuc_multiply", "spmode", "user"),
   Condition("spuc_associator", "spmode", "user"),
   Condition("spuc_commutator", "spmode", "user"),
   Condition("spuc_left_division", "spmode", "user"),
   Condition("spuc_right_division", "spmode", "user"),
   Condition("spuc_left_inner_mapping", "spmode", "user"),
   Condition("spuc_right_inner_mapping", "spmode", "user"),
   Condition("spuc_middle_inner_mapping", "spmode", "user"),
   Condition("spuc_sK", "spmode", "user"),
)

_ENEMIES = ["awr","bd","bs","bsr","cond","drc","fsr","s"]

SPUC = "identity 0 %(spuc_identity)s#multiply 2 %(spuc_multiply)s#associator 3 %(spuc_associator)s#commutator 2 %(spuc_commutator)s#left_division 2 %(spuc_left_division)s#right_division 2 %(spuc_right_division)s#left_inner_mapping 3 %(spuc_left_inner_mapping)s#right_inner_mapping 3 %(spuc_right_inner_mapping)s#middle_inner_mapping 2 %(spuc_middle_inner_mapping)s#sK* 0 %(spuc_sK)s"

def _generate():
   forbiddens = []
   for param in STATIC_VAMPIRE_PARAMS:
      if not isinstance(param, Arg):
         continue 
      if not param[0] in _ENEMIES:
         continue
      for val in param[1]:
         if val == param[2]:
            continue
         forbiddens.append(Forbidden(param[0], val, "sa", "inst_gen"))
   return Parameters(*(STATIC_VAMPIRE_PARAMS+forbiddens))

VAMPIRE_PARAMS = _generate()

def make_params(init):
   params = {}
   i = 0
   while i < len(init):
      try:
         params[init[i].lstrip("-")] = init[i+1]
      except:
         raise Exception(str(init))
      i += 2
   return params

def split_params(params):
   params_global = {}
   for param in VAMPIRE_PARAMS:
      if not isinstance(param, Arg):
         continue
      if param[0] not in params:
         continue
      params_global[param[0]] = params[param[0]]
   
   params_order = {}
   for param in VAMPIRE_PARAMS_ORDER:
      if not isinstance(param, Arg):
         continue
      if param[0] not in params:
         continue
      params_order[param[0]] = params[param[0]]

   return (params_global, params_order)

def join_params(params_global, params_order):
   params = {}
   params.update(params_global)
   params.update(params_order)
   return params

def clean_params(params):
   # remove conditioned parameters from params
   for param in VAMPIRE_PARAMS+VAMPIRE_PARAMS_ORDER:
      if not isinstance(param, Condition):
         continue
      if param[0] in params and param[1] in params and params[param[1]] not in param[2]:
         del params[param[0]]

   # remove default values from params
   for param in VAMPIRE_PARAMS+VAMPIRE_PARAMS_ORDER:
      if not isinstance(param, Arg):
         continue
      if param[0] not in params:
         continue
      if params[param[0]] == param[2]:
         del params[param[0]]

   return params

def vampire_params_global(defaults):
   copy = deepcopy(VAMPIRE_PARAMS)
   params_set_default(copy, defaults)
   return copy

def vampire_params_order(defaults):
   copy = deepcopy(VAMPIRE_PARAMS_ORDER)
   params_set_default(copy, defaults)
   return copy

def spuc_default_params():
   params = {}
   for param in VAMPIRE_PARAMS_ORDER:
      if not isinstance(param, Arg):
         continue
      if not param[0].startswith("spuc_"):
         continue
      params[param[0]] = param[2]
   return params

def vampire_cmd(params):
   copy = dict(params)
   if "awr" in copy: 
      copy["awr"] = copy["awr"].replace("_",":")
   if "s" in copy:
      copy["s"] = copy["s"].replace("_","-")
   for x in ["spoc", "spac", "spfc"]:
      if x in copy:
         copy[x] = copy[x].replace("_","-")

   if "spmode" in copy:
      if copy["spmode"] == "user":
         params_spuc = spuc_default_params()
         params_spuc.update({x:copy[x] for x in copy if x.startswith("spuc_")})
         for x in [y for y in copy if y.startswith("spuc_")]:
            del copy[x]
         copy["fp"] = repr('"%s"' % (SPUC % params_spuc))
         copy["spoc"] = "0"
         copy["spuc"] = "1"
      del copy["spmode"]

   cmd = " ".join(["-%s %s"%(x,copy[x]) for x in sorted(copy)])
   return cmd

