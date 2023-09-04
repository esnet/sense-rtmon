#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="UNIQUE_GLOBAL_ID".*' | grep '.*instance="sdn-dtn-2-10.ultralight.org".*'; then
            echo 'sdn_dtn_2_10_ultralight_org_script_exporter_task1_UNIQUE_GLOBAL_ID{host="sdn_dtn_2_10_ultralight_org"} 1'
        else
            echo 'sdn_dtn_2_10_ultralight_org_script_exporter_task1_UNIQUE_GLOBAL_ID{host="sdn_dtn_2_10_ultralight_org"} 0'
        fi
        
        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="UNIQUE_GLOBAL_ID".*' | grep '.*instance="k8s-gen4-02.sdsc.optiputer.net".*'; then
            echo 'k8s_gen4_02_sdsc_optiputer_net_script_exporter_task1_UNIQUE_GLOBAL_ID{host="k8s_gen4_02_sdsc_optiputer_net"} 1'
        else
            echo 'k8s_gen4_02_sdsc_optiputer_net_script_exporter_task1_UNIQUE_GLOBAL_ID{host="k8s_gen4_02_sdsc_optiputer_net"} 0'
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="UNIQUE_GLOBAL_ID".*' | grep '.*instance="sdn-dtn-2-10.ultralight.org".*' | grep '.*IPaddress="10.251.86.12".*'; then
            echo 'sdn_dtn_2_10_ultralight_org_script_exporter_task2_UNIQUE_GLOBAL_ID{host="sdn_dtn_2_10_ultralight_org"} 1'
        else
            echo 'sdn_dtn_2_10_ultralight_org_script_exporter_task2_UNIQUE_GLOBAL_ID{host="sdn_dtn_2_10_ultralight_org"} 0'
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="UNIQUE_GLOBAL_ID".*' | grep '.*instance="k8s-gen4-02.sdsc.optiputer.net".*' | grep '.*IPaddress="10.251.86.10".*'; then
            echo 'k8s_gen4_02_sdsc_optiputer_net_script_exporter_task2_UNIQUE_GLOBAL_ID{host="k8s_gen4_02_sdsc_optiputer_net"} 1'
        else
            echo 'k8s_gen4_02_sdsc_optiputer_net_script_exporter_task2_UNIQUE_GLOBAL_ID{host="k8s_gen4_02_sdsc_optiputer_net"} 0'
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="UCSD SN3700".*' | grep '.*flow="UNIQUE_GLOBAL_ID".*'; then
        echo 'ucsd sn3700_script_exporter_task1_UNIQUE_GLOBAL_ID{host="ucsd sn3700"} 1'
    else
        echo 'ucsd sn3700_script_exporter_task1_UNIQUE_GLOBAL_ID{host="ucsd sn3700"} 0'
    fi
    