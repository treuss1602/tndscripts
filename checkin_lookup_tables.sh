#!/bin/bash

source ./tndcomponents.sh

REPODIR=~/repo/flowonecdff/01_SourceCode_CDFF/ilink/lookup/lookup_tables/src/lookups/LOOKUP_TABLES
BRANCH=`cd $REPODIR && git rev-parse --abbrev-ref HEAD`
ANSWER=what
while [ "$ANSWER" != "yes" -a "$ANSWER" != "y" ]; do
	echo "Update Lookup Tables in $BRANCH ?"
	read ANSWER
done
TNDREPODIR=~/tndrepo/ossservicedefinitionrepo
TNDREPOBRANCH=`cd $TNDREPODIR && git rev-parse --abbrev-ref HEAD`
ANSWER=what
while [ "$ANSWER" != "yes" -a "$ANSWER" != "y" ]; do
	echo "Take lookup tables from OSS Service Definition Repo, branch $TNDREPOBRANCH ?"
	read ANSWER
done
(cd $TNDREPODIR && git pull)
STATCOUNT=`cd $TNDREPODIR && git status -s -- FactoryProducts CFSs | wc -l`
echo $STATCOUNT
if [ $STATCOUNT != 0 ]; then
	echo "Directory $TNDREPODIR not clean"
	cd $TNDREPODIR && git status
fi

STAGINGDIR=stagedir
echo "--------------------------------------------------------------------------------"
echo "Generating all Lookup Tables in staging dir"
echo "--------------------------------------------------------------------------------"
echo

if [ -d $STAGINGDIR ]; then
        echo "Cleaning all files from directory $STAGINGDIR"
        rm -f $STAGINGDIR/LKT*
else
        echo "Creating staging dir $STAGINGDIR"
        mkdir $STAGINGDIR
fi

for fp in $FACTORY_PRODUCTS; do
    winpty python.exe ./create_lookup_tables.py -D10 "FP_${fp}.json" -d $STAGINGDIR
done
for comp in $COMPONENTS; do
    winpty python.exe ./create_lookup_tables.py -D10 "Component_${comp}.json" -d $STAGINGDIR
done
for cfs in $CFSES; do
    winpty python.exe ./create_lookup_tables.py -D10 "CFS_${cfs}.json" -d $STAGINGDIR
done

echo "--------------------------------------------------------------------------------"
echo "Merging LKT_MANDATORY_PARAM_CHECK with repository version"
echo "--------------------------------------------------------------------------------"
echo
mv $STAGINGDIR/LKT_MANDATORY_PARAM_CHECK $STAGINGDIR/TND_MAND_PARAM_CHECK
(head -1 $REPODIR/LKT_MANDATORY_PARAM_CHECK; cat $STAGINGDIR/TND_MAND_PARAM_CHECK; sed -e1d -e'/key="FACTORY_PRODUCT_/d' $REPODIR/LKT_MANDATORY_PARAM_CHECK) >$STAGINGDIR/LKT_MANDATORY_PARAM_CHECK
echo "--------------------------------------------------------------------------------"
echo "Copying files to $REPODIR"
echo "--------------------------------------------------------------------------------"
echo
for file in $STAGINGDIR/LKT*; do
	echo "$file -> $REPODIR/${file##*/}"
	cp $file $REPODIR
done
cd $REPODIR && git status
