#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-6c1c4758-d804-4b70-8cf5-d6ef1d8a5292".*' | grep '.*instance="T2_US_UCSD:k8s-igrok-02.calit2.optiputer.net".*'; then
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-6c1c4758-d804-4b70-8cf5-d6ef1d8a5292".*' | grep '.*instance="T2_US_UCSD:k8s-igrok-02.calit2.optiputer.net".*' | grep '.*IPaddress="10.251.86.130".*'; then
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task2_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task2_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="calit2.optiputer.net:2020:prism-core".*' | grep '.*flow="rtmon-6c1c4758-d804-4b70-8cf5-d6ef1d8a5292".*'; then
        echo 'calit2_optiputer_net:2020:prism_core_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="calit2_optiputer_net:2020:prism_core"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 'calit2_optiputer_net:2020:prism_core_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="calit2_optiputer_net:2020:prism_core"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="T2_US_UCSD:s1".*' | grep '.*flow="rtmon-6c1c4758-d804-4b70-8cf5-d6ef1d8a5292".*'; then
        echo 't2_us_ucsd:s1_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:s1"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 't2_us_ucsd:s1_script_exporter_task1_rtmon_6c1c4758_d804_4b70_8cf5_d6ef1d8a5292{host="t2_us_ucsd:s1"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    