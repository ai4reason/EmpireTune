"""
Create scenario files for ParamILS runs.
"""

SCENARIO = """algo = %s
execdir = .
deterministic = 1
run_obj = runlength
overall_obj = mean
cutoff_time = %s
cutoff_length = max
tunerTimeout = %s
paramfile = %s/params.txt
outdir = %s/paramils-out
instance_file = %s
test_instance_file = data/empty.tst
"""

def scenario_globaltune(cutoff, timeout, d_dir, instance_file, bin="eprover_wrapper_globaltune.py"):
   return SCENARIO % (bin, cutoff, timeout, d_dir, d_dir, instance_file)

def scenario_finetune(parstr, cutoff, timeout, d_dir, instance_file, bin="eprover_wrapper_finetune.py"):
   return SCENARIO % (bin+" "+parstr, cutoff, timeout, d_dir, d_dir, instance_file)

def scenario_enigmatune(parstr, cutoff, timeout, d_dir, instance_file, bin="eprover_wrapper_enigmatune"):
   return SCENARIO % (bin+" "+parstr, cutoff, timeout, d_dir, d_dir, instance_file)

