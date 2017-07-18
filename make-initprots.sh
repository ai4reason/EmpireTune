#!/bin/sh

CORES=${CORES:-42}

if [ "$#" -ne 4 ]; then
   echo "usage: $0 PROVER INITS BID LIMIT"
   echo "use to: evaluate initial protocol set INITS on benchmark BID with time LIMIT"
   exit 1
fi

PROVER=$1
INITS=$2
BID=$3
LIMIT=$4

PROTS=$ATP_ROOT/inits/$PROVER/$INITS/prots

OUT=$ATP_ROOT/inits/$PROVER/$INITS/${LIMIT}s/$BID
echo $OUT

echo "initial evaluation of $PROVER strategies $INITS on benchmark $BID @ ${LIMIT}s"
if [ -d "$OUT" ]; then
   echo "allready done"
   exit 0;
fi

PERF="perf stat -e task-clock:up,page-faults:up,instructions:up"
if [ "$PROVER" = "eprover" ]; then
   CMD="$PERF eprover -s -p -R --memory-limit=1024 --print-statistics --tstp-format --cpu-limit=$LIMIT"
else
   CMD="$PERF vampire --statistics full --proof tptp -m 2048 -t ${LIMIT}s" 
fi

mkdir -p $OUT
for init in `ls $PROTS`; do
   echo "-> $init"
   cat $ATP_ROOT/benchmarks/${BID}.problems | parallel -j$CORES "($CMD `cat $PROTS/${init}` $ATP_ROOT/benchmarks/{}) >$OUT/{/}.$init 2>&1"
done

