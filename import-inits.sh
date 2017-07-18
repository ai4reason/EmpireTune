#!/bin/sh

if [ "$#" -ne 3 ]; then
   echo "usage: $0 PROVER DIR INITS" 
   echo "use to: import initial strategies from DIR under name INITS"
   exit 1
fi

PROVER=$1
DIR=$2
INITS=$3

echo -n "importing $PROVER strategies $DIR as $INITS ... "

STRATS=$ATP_ROOT/inits/$PROVER/$INITS/strats
PROTS=$ATP_ROOT/inits/$PROVER/$INITS/prots

mkdir -p $STRATS $PROTS

cp $DIR/* $STRATS

for i in `ls $STRATS`; do
   ${PROVER}_params.py $STRATS/$i > $PROTS/protocol_$i
done

N=`ls $STRATS | wc -l`
echo "$N strategies imported"

