#!/bin/bash 

    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*instance="dellos9_s0".*job="job-224".*'; then
        echo "dellos9_s0_script_exporter_task1{host="dellos9_s0"} 1"
    else
        echo "dellos9_s0_script_exporter_task1{host="dellos9_s0"} 0"
    fi
    
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*instance="sdn_dtn_1_7_ultralight_org".*'; then
            echo "sdn_dtn_1_7_ultralight_org_script_exporter_task1{host="sdn_dtn_1_7_ultralight_org"} 1"
        else
            echo "sdn_dtn_1_7_ultralight_org_script_exporter_task1{host="sdn_dtn_1_7_ultralight_org"} 0"
        fi
        
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*IPaddress="sdn-dtn-1-7.ultralight.org".*instance="sdn_dtn_1_7_ultralight_org".*'; then
            echo "sdn_dtn_1_7_ultralight_org_script_exporter_task2{host="sdn_dtn_1_7_ultralight_org"} 1"
        else
            echo "sdn_dtn_1_7_ultralight_org_script_exporter_task2{host="sdn_dtn_1_7_ultralight_org"} 0"
        fi
        
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*instance="sdn_dtn_2_10_ultralight_org".*'; then
            echo "sdn_dtn_2_10_ultralight_org_script_exporter_task1{host="sdn_dtn_2_10_ultralight_org"} 1"
        else
            echo "sdn_dtn_2_10_ultralight_org_script_exporter_task1{host="sdn_dtn_2_10_ultralight_org"} 0"
        fi
        
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*IPaddress="sdn-dtn-2-10.ultralight.org".*instance="sdn_dtn_2_10_ultralight_org".*'; then
            echo "sdn_dtn_2_10_ultralight_org_script_exporter_task2{host="sdn_dtn_2_10_ultralight_org"} 1"
        else
            echo "sdn_dtn_2_10_ultralight_org_script_exporter_task2{host="sdn_dtn_2_10_ultralight_org"} 0"
        fi
        