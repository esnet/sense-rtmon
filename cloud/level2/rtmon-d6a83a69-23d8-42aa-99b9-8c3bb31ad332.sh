#!/bin/bash 

        # check_arp_on
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-d6a83a69-23d8-42aa-99b9-8c3bb31ad332".*' | grep '.*instance="T2_US_UCSD:k8s-igrok-02.calit2.optiputer.net".*'; then
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
        # check_arp_contain_ip
        if curl http://dev2.virnao.com:9091/metrics | grep '.*arp_state.*' | grep '.*flow="rtmon-d6a83a69-23d8-42aa-99b9-8c3bb31ad332".*' | grep '.*instance="T2_US_UCSD:k8s-igrok-02.calit2.optiputer.net".*' | grep '.*IPaddress="10.251.85.190".*'; then
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task2_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        else
            echo 't2_us_ucsd:k8s_igrok_02_calit2_optiputer_net_script_exporter_task2_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:k8s_igrok_02_calit2_optiputer_net"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
        fi
        
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="T2_US_UCSD:s1".*' | grep '.*flow="rtmon-d6a83a69-23d8-42aa-99b9-8c3bb31ad332".*'; then
        echo 't2_us_ucsd:s1_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:s1"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 't2_us_ucsd:s1_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="t2_us_ucsd:s1"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    
    # check_snmp_on
    if curl http://dev2.virnao.com:9091/metrics | grep '.*ifHCInOctets.*' | grep '.*instance="calit2.optiputer.net:2020:prism-core".*' | grep '.*flow="rtmon-d6a83a69-23d8-42aa-99b9-8c3bb31ad332".*'; then
        echo 'calit2_optiputer_net:2020:prism_core_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="calit2_optiputer_net:2020:prism_core"} 1' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    else
        echo 'calit2_optiputer_net:2020:prism_core_script_exporter_task1_rtmon_d6a83a69_23d8_42aa_99b9_8c3bb31ad332{host="calit2_optiputer_net:2020:prism_core"} 0' | curl --data-binary @- http://dev2.virnao.com:9091/metrics/job/single
    fi
    