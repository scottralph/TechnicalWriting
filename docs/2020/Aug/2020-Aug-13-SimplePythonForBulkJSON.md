# August 13, 2020,  Simple JSON reading utility for bulk JSON file deciphering

When dealing with bulk-import of data, often the data is of a
one-JSON-object-line format.
Most recently I was trying to uncover problems with [AVRO files](https://en.wikipedia.org/wiki/Apache_Avro),
which are binary, however they can be converted to JSON using a JAVA utility
[avro-tools.jar](https://mvnrepository.com/artifact/org.apache.avro/avro-tools).

But just one line of this JSON is very cubmersome:
```json
{"mm_mtrl_id":{"string":"000000025537730333"},"mm_gro_cd":{"long":915036220},"mm_source_sys_cd":{"string":"DCP"},"mm_mtrl_grp_cd":{"string":"DNU-UNK"},"mm_trsptation_gro_cd":null,"mm_ext_mtrl_grp":{"string":"DONOTUSE"},"mm_sales_div_cd":{"string":"72"},"mm_product_hie_cd":null,"mm_mtrl_pkgg_grp_cd":null,"mm_mtrl_type":{"string":"DIEN"},"mm_industry_sec_cd":{"string":"M"},"mm_dangerous_goo_cd":null,"mm_gross_wei_cd":null,"mm_net_wei_cd":null,"mm_mtrl_msr_cd":{"string":"KGM"},"mm_mtrl_vol_cd":null,"mm_mtrl_sls_cd":null,"mm_mtrl_plt_cd":{"string":"03"},"mm_mtrl_plnt_dt":{"long":1546300800000},"mm_mtrl_sls_dt":null,"mm_industry_sta_cd":null,"mm_mtrl_doc_cd":null,"mm_configurable_mat_cd":null,"mm_authorization_gro_cd":null,"mm_environment_rel_cd":null,"mm_manufacturer_par_cd":null,"mm_mtrl_crss_id":null,"mm_mtrl_cd":{"string":"LEIS"},"mtrl_type_cd":{"string":"DIEN"},"mtrl_type_dn":{"string":"Service"},"mtrl_grp_dn":{"string":"Do Not Use"},"product_hie_cd":null,"product_hie_descr":null,"product_hie_lev":null,"product_hie_product_type_cd":null,"product_hie_product_descr":null,"product_hie_product_catgry_cd":null,"product_hie_product_catgry_descr":null,"product_hie_product_family_cd":null,"product_hie_product_family_descr":null,"product_hie_product_mod_cd":null,"product_hie_product_mod_descr":null,"dang_goods_cd":null,"dang_goods_descr":null,"ext_mtrl_grp_cd":{"string":"DONOTUSE"},"ext_mtrl_grp_descr":{"string":"DONOTUSE"},"pkg_mtrl_grp_cd":null,"pkg_mtrl_grp_descr":null,"mtrl_lang_mtrl_dn":{"string":"Informix I-ESQL/C Runtime, Class D 32"},"mtrl_plant_plant":{"string":"802Z"},"mtrl_plant_status_cd":null,"mtrl_plant_eff_date":null,"mtrl_plant_profit_center_cd":{"string":"P000000549"},"mtrl_plant_catgry_cd":null,"mtrl_plant_abc_id":null,"mtrl_plant_config_mtrl_id":null,"mtrl_plant_pur_grp_cd":null,"mtrl_plant_mtrl_proc_type_cd":null,"mtrl_plant_proc_type_cd":null,"mtrl_plant_planned_deli_days":null,"mtrl_plant_goods_recpt_process_days":null,"mtrl_plant_mrp_planning_grp_cd":null,"mtrl_plant_pro_days":null,"mtrl_planning_mat_cd":{"string":"000000025537730333"},"mtrl_plant_planning_plant_cd":null,"mtrl_type_pla_cd":null,"mtrl_proc_type_cd":null,"mtrl_proc_type_descr":null,"mrp_typ_cd":null,"mrp_typ_descr":null,"mrp_mtrl_bsn_cd":null,"mrp_mtrl_cntr_cd":null,"mrp_mtrl_typ_cd":null,"mrp_id":null,"mtrl_abc_ind":null,"mtrl_abc_descr":null,"pur_grp_cd":null,"pur_grp_descr":null,"mtrl_status_cd":null,"mtrl_status_descr":null,"mrp_ctrll":null,"mtrl_source_sys_cd":{"string":"300"},"mtrl_descr":{"string":"Informix I-ESQL/C Runtime, Class D 32"},"mtrl_basic_dat_cd":null,"mtrl_internal_com_cd":null,"language":{"string":"EN"},"prod_lf_cyc_cycle_pla_cd":null,"pro_lifecycle_staus":null,"dist_chan_cd":{"string":"00"},"dist_chan_descr":{"string":"Common"},"zlasttimestamp":{"string":"20200521012426"}}
```

So, to make searching for particular patterns easier, I wrote a Python utility to parse each entry, and look for key-values of interest.
Ideally I would be able to run the Python script from the command-line like a [grep](https://en.wikipedia.org/wiki/Grep) command.

Here is the small script, also given [here](../../../utils/json-field-print/json-field-print.py )
```Python
import json
import sys

if __name__ == '__main__':
    args = sys.argv
    if len(args) < 2:
        print('Usage: ' + args[0] + ' [json-field-name] [field-value]')
        exit(1)

    field = args[1]
    field_val = args[2]
    line_count = 1
    for line in sys.stdin:
        try:
            obj = json.loads(line)
            if field in obj:
                if obj[field]["string"] == field_val:
                    print(line)
        except Exception as e:
            print('Line ' + str(line_count) + ' Got exception from parsing JSON\n' + line )
            exit(1)
        line_count = line_count + 1
```
Note: The installed Python did not support the newer string interpolation, so that was unfortunate.

This allowed me to find things of interest in a single JSON file.
The slightly harder part was to find *all* the AVRO files, convert each to a JSON file, and then extract the interesting bits.

```
#! /bin/bash
# This file was named uat-207.sh in the following example, because it was a
# specific JIRA ticket associated with the "bug"

echo "Looking in file $1 for field $2 equal to $3"
echo "Copying file locally"

hdfs dfs -get $1 /tmp/temp.avro

echo "Starting processing $1" >> /tmp/bug.log

java -jar avro-tools-1.9.2.jar tojson /tmp/temp.avro | python3 json-field-print.py $2 $3  >> /tmp/bug.log
rm /tmp/temp.avro
```
The AVRO files are vast, so I have to remove the JSON as I go along.

The last piece of the puzzle is to find all the AVRO files within the [HDFS File System](https://hadoop.apache.org/docs/r1.2.1/hdfs_design.html)

```console
hadoop fs  -find abfs://qbertitg@qbert.dfs.core.windows.net/EA/supplychain/inprogress/qbert_V2_0_materialmaster -name \*.avro -print | xargs -ithefile ./uat-207.sh thefile mm_mtrl_id Q9V06D
```

This looks for all AVRO files under the given directory, and calls the shell script, to look for JSON objects with the key *mm_mtrl_id* whose value is *Q9V06D*.

After running this, processing tens of terabytes of data, enough evidence was collected to show that the bug was not actually a bug.
