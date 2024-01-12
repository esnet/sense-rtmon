#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-724a382d-84df-4cce-918a-3b68c75ba613".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-724a382d-84df-4cce-918a-3b68c75ba613".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*' | grep '.*IPaddress="10.251.87.162".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="T2_US_Caltech_Test:dellos9_s0".*' | grep '.*flow="rtmon-724a382d-84df-4cce-918a-3b68c75ba613".*'; then
        echo 't2_us_caltech_test:dellos9_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_caltech_test:dellos9_s0"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 't2_us_caltech_test:dellos9_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_caltech_test:dellos9_s0"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="T2_US_SDSC:sn3700_s0".*' | grep '.*flow="rtmon-724a382d-84df-4cce-918a-3b68c75ba613".*'; then
        echo 't2_us_sdsc:sn3700_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:sn3700_s0"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 't2_us_sdsc:sn3700_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="t2_us_sdsc:sn3700_s0"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="NRM_CENIC:aristaeos_s0".*' | grep '.*flow="rtmon-724a382d-84df-4cce-918a-3b68c75ba613".*'; then
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="nrm_cenic:aristaeos_s0"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_724a382d_84df_4cce_918a_3b68c75ba613{host="nrm_cenic:aristaeos_s0"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    