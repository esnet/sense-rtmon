### Building Dashboards

`dynamic.py` builds the dashboard from sections and blocks from the `templates` folder. Each dashboard is consisted of two parts, flow panels and L2 debugging tables. Flow panels are built from the `panel` folder. L2 debugging tables are built from the `l2_debugging_panel` folder. The script reads the given configuration file and replaces key words in the template files with the values from the configuration file. The script then writes the output to a json file. 

The dashboard json file is built similar to a sandwich structure in the following order:
Dashboard Top Section          file_1
   Panels                      file_2
       Info Panel              file_3
       Interface Panel         file_4
           Interface targets   file_n
       L2 Debugging Panel      file_5
Dashboard Bottom Section       file_1

`api.py` file sends HTTP Post Request to Grafana to import the generated dashboard json file.

`topology` contains the code for mermaid plug-in diagram. The groundwork is layed out but not yet implemented.