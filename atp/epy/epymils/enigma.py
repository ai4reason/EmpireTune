import os
import sys
import commands
from itertools import islice, cycle
from os.path import join, isdir

from .. import ATP_ROOT, mkdir

def make_symbols(pos, neg, f_out=None, f_tmp="all.p.tmp"):
   "Extract symbols from positive and negative samples."

   file(f_tmp,"w").write("\n".join(pos))
   file(f_tmp,"a").write("\n".join(neg))
   symbols = commands.getoutput("enigma-symbols %s" % f_tmp)
   os.system("rm -f %s" % f_tmp)
   if f_out:
      file(f_out,"w").write(symbols)
   return symbols.strip().split("\n")

def make_train(pos, neg, boost=True, f_sym="symbols.map", f_train="train.in", f_pos="train.pos", f_neg="train.neg"):
   
   # boosting:
   #   TEN    ... repeat positives 10x
   #   FAIR   ... the same number of positives and negatives
   #   POS3   ... 3-times more positives than negatives
   #   DISJ   ... remove negatives which are also in positives
   #   DISJ3  ... combine DISJ with POS3
   if boost=="TEN":
      pos = pos*10
   if boost=="FAIR" and len(pos)>0 and len(neg)>0:
      count = max(len(pos), len(neg))
      pos = list(islice(cycle(pos),count))
      neg = list(islice(cycle(neg),count))
   if boost=="POS3" and len(pos)<3*len(neg):
      pos = list(islice(cycle(pos),3*len(neg)))
   if boost=="DISJ":
      neg = [x for x in neg if x not in pos]
   if boost=="DISJ3":
      neg = [x for x in neg if x not in pos]
      if len(pos)<3*len(neg):
         pos = list(islice(cycle(pos),3*len(neg)))

   file(f_pos,"w").write("\n".join(pos))
   file(f_neg,"w").write("\n".join(neg))
   train = commands.getoutput("enigma-features %s %s %s" % (f_pos, f_neg, f_sym))
   if f_train:
      file(f_train,"w").write(train)
   return train.strip().split("\n")

def train(f_train="train.in", f_train_out="train.log"):
   os.system("train -s 2 %s > %s" % (f_train,f_train_out))
   ret = commands.getoutput("predict %s %s.model %s.out" % (f_train,f_train,f_train))
   return ret.strip()

def model_dir(name, d_enigma=None):
   d_root = os.getenv("ENIGMA_ROOT", "Enigma") if not d_enigma else d_enigma
   return join(d_root, name)

def save_model(name, f_sym="symbols.map", f_feat="features.map", f_mod="train.in.model", d_enigma=None, debug=False):
   d_model = model_dir(name, d_enigma)
   os.system("mkdir -p %s" % d_model)
   os.system("mv %s %s/symbols.map" % (f_sym, d_model))
   os.system("mv %s %s/features.map" % (f_feat, d_model))
   os.system("mv %s %s/model.lin" % (f_mod, d_model))
   if debug:
      os.system("cp data/problems.txt %s" % d_model)
      os.system("cp data/all.txt %s" % d_model)
      os.system("cp train.txt %s" % d_model)
      os.system("cp proto %s" % d_model)
      os.system("cp params.json %s" % d_model)
      os.system("cp train.in %s" % d_model)
      os.system("cp train.pos %s" % d_model)
      os.system("cp train.neg %s" % d_model)

def rename_model(old, new, d_enigma=None):
   d_old = model_dir(old, d_enigma)
   d_new = model_dir(new, d_enigma)
   if isdir(d_new):
      print "Enigma: Warning: Model '%s' exists. Destroying!" % d_new
      os.system("rm -fr %s" % d_new)
   os.system("mv %s %s" % (d_old,d_new))

def collect_samples(problems, results, key):
   samples = []
   for problem in problems:
      if not problem in results:
         print "Enigma: Warning: Missing result for problem '%s'." % problem
      samples.extend(results[problem][key])
   return samples

def collect_pos(problems, results):
   return collect_samples(problems, results, "trainpos")

def collect_neg(problems, results):
   return collect_samples(problems, results, "trainneg")

