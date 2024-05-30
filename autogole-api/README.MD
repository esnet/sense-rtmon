Structure for SENSE-O and RT-Mon communications. This is just a draft to initiate discussion as I put my thoughts loud.
I was reviewing code, and I think we need a structure and API layout in how things will be working. There are multiple ideas (might be missing some), feel free to add, comment as you see fit (or which better approach).
First:
RT-Mon runs an http server which accepts GET/PUT/POST/DELETE methods.
  To submit new action: Orchestrator (via button click) does POST to RT-Mon Service; Information it needs to provide is {“referenceUUID”:“63ee9df4-c273-4d24-8556-364eaa5b0a71", “orchestrator”: “sense-o.es.net”}. It get’s back URL to monitoring page;
   To get state of request - issues GET - which will have submitted information and any information regarding that submission;
   To modify state (not needed for Orchestrator) - that will be internal for RT-Mon;
   To delete - Orchestrator issues DELETE with referenceUUID - and dashboard is deleted and all records from RT-Mon;
RT-Mon - once receives POST - get’s all manifest from Orchestrator (via API calls), prepares all dashboards and communicates with any of RMs as needed;
         once received DELETE - deletes all records in local db; grafana, prometheus and or if any RMs.
SENSE-O will need to ensure that rt-mon user/key is able to get/view intent and send template request for that intent;
Second:
 To submit new action: Orchestrator (via button click) authorizes rt-mon user/key to view that intent and allow submit templates for it;
RT-Mon in background monitors all intents and any intent is visible for rt-mon api user - it will:
  get’s all manifest from Orchestrator (via API calls), prepares all dashboards and communicates with any of RMs as needed;
  once intent list changes (not present - either deleted intent, or deleted user from authorized list) - deletes all records in local db; grafana, prometheus and or if any RMs.
SENSE-O will need to ensure that rt-mon user/key is able to get/view intent and send template request for that intent;
Third:
RT-Mon runs an http server which accepts GET/PUT/POST/DELETE methods.
  To submit new action: Orchestrator (via button click) does POST to RT-Mon Service; Information it provides is all manifest (why we would need to call it back from rt-mon?). For example it provides all of this information:
{'serviceUUID': 'e8b70b24-694a-44b9-86de-bb3910aa4d48', 'jsonTemplate': '{"Ports":[{"Site":"urn:ogf:network:tier2.ultralight.org:2024","Port":"urn:ogf:network:tier2.ultralight.org:2024:dellos10_s1:Port-channel_101","Node":"T2_US_Caltech:dellos10_s1","Peer":"urn:ogf:network:ultralight.org:2013:dellos9_s0:Port-channel_103","Vlan":"1790","Name":"Port-channel 101"},{"Site":"urn:ogf:network:tier2.ultralight.org:2024","Port":"urn:ogf:network:tier2.ultralight.org:2024:dellos10_s1:Port-channel_102","Node":"T2_US_Caltech:dellos10_s1","Peer":"urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel501","Vlan":"1790","Name":"Port-channel 102"},{"Site":"urn:ogf:network:ultralight.org:2013","Port":"urn:ogf:network:ultralight.org:2013:dellos9_s0:Port-channel_103","Node":"T2_US_Caltech_Test:dellos9_s0","Peer":"urn:ogf:network:tier2.ultralight.org:2024:dellos10_s1:Port-channel_101","Vlan":"1790","Name":"Port-channel 103"},{"Site":"urn:ogf:network:ultralight.org:2013","Port":"urn:ogf:network:ultralight.org:2013:dellos9_s0:hundredGigE_1-10","Node":"T2_US_Caltech_Test:dellos9_s0","Peer":"?peer?","Host":[{"IPv4":"10.251.86.233\\/30","Interface":"mlx4p2s1","Name":"T2_US_Caltech_Test:sandie-1.ultralight.org"}],"Vlan":"1790","Name":"hundredGigE 1\\/10"},{"Site":"urn:ogf:network:sc-test.cenic.net:2020","Port":"urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel501","Node":"NRM_CENIC:aristaeos_s0","Peer":"urn:ogf:network:tier2.ultralight.org:2024:dellos10_s1:Port-channel_102","Vlan":"1790","Name":"Port-Channel501"},{"Site":"urn:ogf:network:sc-test.cenic.net:2020","Port":"urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel502","Node":"NRM_CENIC:aristaeos_s0","Peer":"urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc502","Vlan":"1790","Name":"Port-Channel502"},{"Site":"urn:ogf:network:sense-oasis-nrp-nautilus.io:2020","Port":"urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc501","Node":"T2_US_UCSD_OASIS:oasis","Peer":"?peer?","Vlan":"1790","Name":"?port_name?"},{"Site":"urn:ogf:network:sense-oasis-nrp-nautilus.io:2020","Port":"urn:ogf:network:sense-oasis-nrp-nautilus.io:2020:oasis:Pc502","Node":"T2_US_UCSD_OASIS:oasis","Peer":"urn:ogf:network:sc-test.cenic.net:2020:aristaeos_s0:Port-Channel502","Vlan":"1790","Name":"Pc502"}]}', 'jsonModel': None}
   To get state of - issues GET - which will have submitted information and any information regarding that submission;
   To modify state (not needed for Orchestrator) - that will be internal for RT-Mon;
   To delete - Orchestrator issues DELETE with referenceUUID - and dashboard is deleted and all records from RT-Mon;
RT-Mon - once receives POST - prepares all dashboards and communicates with any of RMs as needed;
         once received DELETE - deletes all records in local db; grafana, prometheus and or if any RMs.
NO need for SENSE-O will to ensure that rt-mon user/key is able to get/view intent and send template request for that intent;
