#!/bin/bash

installdir=/nokia/catalog/install

getEnvInfo() {
        if [ ! -f "${installdir}/catalog/application.properties" ]; then
                echo "ERROR: Catalog application.properties file not found."
                exit 1
        fi
        server_host=$(grep -Po '(?<=server.hostname=).*' ${installdir}/catalog/application.properties)
        server_port=$(grep -Po '(?<=server.port=).*' ${installdir}/catalog/application.properties)
        server_user="admin"
        server_pass="password123!"
        db_url=$(grep -Po '(?<=db.url=jdbc:).*' ${installdir}/catalog/application.properties)
        db_url=$(grep -Po '(?<=db.url=jdbc:).*' ${installdir}/catalog/application.properties)
        db_hostport=$(echo ${db_url} | cut -d'/' -f3)
        db_host=$(echo ${db_hostport} | cut -d':' -f1)
        db_port=$(echo ${db_hostport} | cut -d':' -f2)
        db_name=$(echo ${db_url} | cut -d'/' -f4)
        db_user=$(grep -Po '(?<=db.username=).*' ${installdir}/catalog/application.properties)
        db_pass=$(grep -Po '(?<=db.password=).*' ${installdir}/catalog/application.properties)
}

if [ $# -lt 1 ]; then
        echo "Usage: `basename $0` <FACTORY_PROD> [...]"
        exit 1
fi

getEnvInfo
export PGPASSWORD=${db_pass}

for arg in "$@"; do
        pattern=`echo "$arg" | sed -e's/\*/%/' -e's/\..*//'`
        echo "Querying pattern $pattern"
#echo "dbname='$db_name' user='$db_user' host='$db_host' port='$db_port'"
        psql -t -A "dbname='$db_name' user='$db_user' host='$db_host' port='$db_port'" \
-c "select i.name || '/' || i.version
 from items i
 join lifecycle_states l on i.lifecycle_state_id = l.lifecycle_state_id
where i.name like '$pattern'
  and l.name = 'Testing'
  and i.last_changed_date >= ALL(select i2.last_changed_date from items i2 where i2.name = i.name)
order by i.name;" | while read item; do
                echo "Exporting $item"
                tmpfilename=tmp_${item%%/*}.xml
                java -jar ImportExport.jar -export -user $server_user -pass "$server_pass" -server $server_host:$server_port -secure true \
                        -filename $tmpfilename -items "$item" -type items
                xmllint --format --nsclean -o ${item%%/*}.xml $tmpfilename
                rm $tmpfilename
        done
done
