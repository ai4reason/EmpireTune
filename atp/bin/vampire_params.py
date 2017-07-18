#!/usr/bin/python

import sys
import vampiretools

def run():
   init = file(sys.argv[1]).read().strip().split()
   params = vampiretools.make_params(init)
   params = vampiretools.clean_params(params)
   proto = vampiretools.vampire_cmd(params)
   sys.stdout.write(proto)
   
run()

