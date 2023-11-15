#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-5d3ca075-3c24-4c24-88e2-a7e6ac924de2".*' | grep '.*instance="T2_US_Caltech_Test:sandie-1.ultralight.org".*'; then
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_caltech_test:sandie_1_ultralight_org"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_caltech_test:sandie_1_ultralight_org"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-5d3ca075-3c24-4c24-88e2-a7e6ac924de2".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-5d3ca075-3c24-4c24-88e2-a7e6ac924de2".*' | grep '.*instance="T2_US_Caltech_Test:sandie-1.ultralight.org".*' | grep '.*IPaddress="10.251.87.130".*'; then
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task2_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_caltech_test:sandie_1_ultralight_org"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task2_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_caltech_test:sandie_1_ultralight_org"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-5d3ca075-3c24-4c24-88e2-a7e6ac924de2".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*' | grep '.*IPaddress="10.251.87.129".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="NRM_CENIC:aristaeos_s0".*' | grep '.*flow="rtmon-5d3ca075-3c24-4c24-88e2-a7e6ac924de2".*'; then
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="nrm_cenic:aristaeos_s0"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_5d3ca075_3c24_4c24_88e2_a7e6ac924de2{host="nrm_cenic:aristaeos_s0"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    