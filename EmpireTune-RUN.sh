#!/bin/bash

# These must be set before running!!!

export CORES=4
export BST_TIMEOUT_GLOBAL=300
export BST_CUTOFF=2
export BST_EVAL_LIMIT=10
export BST_VERS=8
export BST_TOPS=10
export BST_MIN_PROC=500
export BST_MAX_PROC=20000
export BST_BENCHMARK=casc17-isa-train
export BST_PROVER=eprover
export BST_INITSTRATS=tptp

if [ "$BST_PROVER" = "vampire" ]; then
   export BST_TIMEOUT_ORDERTUNE=0
fi

if [ "$BST_PROVER" = "eprover" ]; then
   export BST_TIMEOUT_FINETUNES=300
   export BST_TIMEOUT_ENIGMATUNE=300
   export BST_MIN_CEFS=2
   export BST_MAX_CEFS=10
fi

#
# Non-hackers do not change below this line
#

#. ./setenv.sh      # always call this yourself before tuning

DIR="EmpireTune--${BST_PROVER}--${BST_BENCHMARK}--${BST_INITSTRATS}-"
if [ "$BST_PROVER" = "eprover" ]; then
   DIR="$DIR-${BST_TIMEOUT_GLOBAL}t${BST_TIMEOUT_FINETUNES}t${BST_TIMEOUT_ENIGMATUNE}"
else
   DIR="$DIR-${BST_TIMEOUT_GLOBAL}t${BST_TIMEOUT_ORDERTUNE}"
fi
DIR="$DIR-cut${BST_CUTOFF}-e${BST_EVAL_LIMIT}"
if [ "$BST_PROVER" = "eprover" ]; then
   DIR="$DIR-${BST_MIN_CEFS}c${BST_MAX_CEFS}"
fi
DIR="$DIR-${BST_MIN_PROC}mil${BST_MAX_PROC}"
DIR="$DIR-top${BST_TOPS}-vers${BST_VERS}-${CORES}cores"

rm -fr $DIR # dangerous!
mkdir -p $DIR
cp -r SKEL/* $DIR

./make-initprots.sh $BST_PROVER $BST_INITSTRATS $BST_BENCHMARK $BST_EVAL_LIMIT

mkdir -p $DIR/strats
mkdir -p $DIR/prots

cp -r $ATP_ROOT/inits/$BST_PROVER/$BST_INITSTRATS/${BST_EVAL_LIMIT}s/$BST_BENCHMARK $DIR/initprots
cp -r $ATP_ROOT/benchmarks/$BST_BENCHMARK $DIR/allprobs

#(cd $DIR; EmpireTune.pl | tee tuner.log)
(cd $DIR; nohup EmpireTune.pl > tuner.log &)

