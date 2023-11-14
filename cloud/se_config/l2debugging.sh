#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-a863884d-2cdb-4f3a-b964-dad449c588ab".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-a863884d-2cdb-4f3a-b964-dad449c588ab".*' | grep '.*instance="T2_US_Caltech_Test:sandie-1.ultralight.org".*'; then
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_caltech_test:sandie_1_ultralight_org"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_caltech_test:sandie_1_ultralight_org"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-a863884d-2cdb-4f3a-b964-dad449c588ab".*' | grep '.*instance="T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net".*' | grep '.*IPaddress="172.18.3.1".*'; then
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net_script_exporter_task2_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_sdsc:k8s_gen4_01_sdsc_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-a863884d-2cdb-4f3a-b964-dad449c588ab".*' | grep '.*instance="T2_US_Caltech_Test:sandie-1.ultralight.org".*' | grep '.*IPaddress="172.18.3.2".*'; then
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task2_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_caltech_test:sandie_1_ultralight_org"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_caltech_test:sandie_1_ultralight_org_script_exporter_task2_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="t2_us_caltech_test:sandie_1_ultralight_org"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="NRM_CENIC:aristaeos_s0".*' | grep '.*flow="rtmon-a863884d-2cdb-4f3a-b964-dad449c588ab".*'; then
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="nrm_cenic:aristaeos_s0"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 'nrm_cenic:aristaeos_s0_script_exporter_task1_rtmon_a863884d_2cdb_4f3a_b964_dad449c588ab{host="nrm_cenic:aristaeos_s0"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    