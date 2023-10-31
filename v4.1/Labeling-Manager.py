from SmartConsole import *
import os
import shutil



class main:
    # constructor
    def __init__(self):
        # load smart console
        self.sc = SmartConsole("Labeling Manager", "4.1")

        # set-up main memu
        self.sc.add_main_menu_item("MAKE NEW LABELS", self.new)
        self.sc.add_main_menu_item("PRINT LABELS", self.print)
        self.sc.add_main_menu_item("INVENTORY", self.inventory)

        # get settings
        self.path_main = self.sc.get_setting("Labeling folder")
        self.path_templates = self.path_main+"/_Templates_"
        self.path_main_labels_templates = self.path_main+"/_Templates_/Main Labels"
        self.path_inventory_label = self.path_main+"/TMS BOX.btw"

        # test all paths
        self.sc.test_path(self.path_main)
        self.sc.test_path(self.path_templates)
        self.sc.test_path(self.path_main_labels_templates)
        self.sc.test_path(self.path_inventory_label)

        # load databases
        self.load_databases()

        # display main menu
        self.sc.start()
    
    def load_databases(self):
        self.FILES_THAT_HAVE_BEEN_PRINTED = []

        # load databases
        self.TEMPLATES = {} # {part_number: size}
        self.INFO = {}
        self.WORK_ORDERS = {} # {work_order: 1}

        # self.TEMPLATES
        for path, dirs, files in os.walk(self.path_templates):
            for file in files:
                if ".btw" in file:
                    filename = file.replace(".btw", "")
                    filename = filename.split(" ")
                    if len(filename) == 4:
                        # 0 TMS
                        # 1 TEMPLATE
                        # 2 lbl_part_number1
                        # 3 lbl_size
                        lbl_part_number = filename[2]
                        size = filename[3]
                        self.TEMPLATES[lbl_part_number] = size

        for path, dirs, files in os.walk(self.path_main):
            for file in files:
                if ".html" in file:
                    if not file in self.WORK_ORDERS:
                        add = file.replace(".html", "")
                        self.WORK_ORDERS[add] = 1
                    else:
                        self.sc.fatal_error("Work order "+file+" is not unique!")

    def new(self):
        # load database
        self.load_databases()

        # get part number
        part_number = self.sc.input("Insert PRODUCT PART NUMBER").upper()

        # make sure part number is not empty
        if not part_number == "":
            # if part number dont have a folder, make a folder
            path = self.path_main+"/"+part_number
            if not os.path.isdir(path):
                if self.sc.question("Make new directory: "+path+" ?"):
                    os.makedirs(path)
            
            # if part number have a folder
            if os.path.isdir(path):
                # write script if there is none
                script_file = path+"/script.txt"
                if not os.path.isfile(script_file):
                    file = open(script_file, 'w')
                    file.write("PART_NUMBER( "+part_number+" )\n")
                    file.write("DESCRIPTION( description )\n")
                    file.write("ORDER_NUMBER( order_number )\n")
                    file.write("DRAWING( drawing )\n")
                    file.write("REV( drawing_rev )\n")
                    file.write("BOM( bom_rev )\n")
                    file.write("SERIAL_NUMBER_FORMAT( FLT0000-0000 )\n\n")
                    file.write("BALLOON( balloon_number , tms_part_number )\n")
                    file.write("LBL( name , balloon )\n")
                    file.write("MAIN_LBL( format , balloon )")
                    file.close()
                    os.popen(script_file)
                    self.sc.input("Edit the script file and press ENTER to continue")
                
                self.run_script(script_file)
                

        else:
            self.sc.error("Invalid PRODUCT PART NUMBER")
        
        # restart
        self.sc.restart()
    
    def run_script(self, script_file):
        if os.path.isfile(script_file):
            # run script
            functions = {}
            functions["PART_NUMBER"] = (self.script_add_part_number, ("part_number",))
            functions["DESCRIPTION"] = (self.script_add_description, ("desc",))
            functions["ORDER_NUMBER"] = (self.script_add_order_number, ("order_number",))
            functions["DRAWING"] = (self.script_add_drawing, ("dwg",))
            functions["REV"] = (self.script_add_drawing_rev, ("rev",))
            functions["BOM"] = (self.script_add_bom_rev, ("bom",))
            functions["SERIAL_NUMBER_FORMAT"] = (self.script_add_sn_format, ("sn",))
            functions["BALLOON"] = (self.script_add_balloon, ("balloon_number" , "lbl_part_number"))
            functions["LBL"] = (self.script_add_lbl, ("name" , "balloon"))
            functions["MAIN_LBL"] = (self.script_add_main_lbl, ("format" , "balloon"))
            self.sc.run_script(script_file, functions)
            self.test_script()

    def test_script(self):
        must_keys = ("PART_NUMBER", "DESCRIPTION", "ORDER_NUMBER", "DRAWING", "REV", "BOM", "SERIAL_NUMBER_FORMAT")
        for key in must_keys:
            if not key in self.INFO:
                self.sc.fatal_error("Script file is missing a function: "+key+"()")

    def print(self):
        # load database
        self.load_databases()

        # get work order
        work_order = self.sc.input("Insert WORK ORDER")
        if work_order == "":
            self.sc.error("Invalid WORK ORDER")
            self.sc.restart()
            return
        self.INFO["WORK_ORDER"] = work_order
        if work_order in self.WORK_ORDERS:
            self.sc.error("WORK ORDER: "+work_order+" is not new")
            self.sc.restart()
            return

        # get part number
        part_number = self.sc.input("Insert PRODUCT PART NUMBER").upper()
        if part_number == "":
            self.sc.error("Invalid PRODUCT PART NUMBER")
            self.sc.restart()
            return
        goto = self.path_main+"/"+part_number
        if not os.path.isdir(goto):
            self.sc.error("No such folder: "+goto)
            self.sc.restart()
            return
        
        # read script
        script_file = goto+"/script.txt"
        if os.path.isfile(script_file):
            self.run_script(script_file)
            self.test_script()
        else:
            self.sc.error("No script file: "+goto+"/script.txt")
            self.sc.restart()
            return

        # get qty
        qty = self.sc.input("Insert WORK ORDER SIZE")
        self.INFO["QTY"] = qty
        try:
            qty = int(qty)
        except:
            self.sc.error("Invalid size")
            self.sc.restart()
            return

        # get first serial number
        first_sn = self.sc.input("Insert FIRST SERIAL NUMBER according to format: "+self.INFO["SERIAL_NUMBER_FORMAT"]).upper()
        self.INFO["FIRST_SN"] = first_sn
        if len(self.INFO["SERIAL_NUMBER_FORMAT"]) != len(first_sn):
            self.sc.error("Invalid serial number format")
            self.sc.restart()
            return
        running_number = first_sn[-4:]
        try:
            running_number = int(running_number)
        except:
            self.sc.error("Invalid serial number format")
            self.sc.restart()
            return

        # get p.r.
        pr = self.sc.input("Insert P.R. NUMBER or leave empty for 00").upper() or "00"
        self.INFO["PR"] = pr

        # generate serial numbers
        snfile = open(goto+"/SerialNumbers.csv", 'w')
        snfile.write("SN\n")
        for x in range(qty):
            sn = first_sn[0:-4]
            sn = sn+str(running_number+x).zfill(4)
            snfile.write(sn+"\n")
        snfile.close()

        # generate html report
        self.generate_html_report(goto+"/TMS APPROVAL FORM")

        # open all files
        for path, dirs, files in os.walk(goto):
            for file in files:
                if ".btw" in file:
                    cmd = goto+"/"+file
                    if os.path.isfile(cmd):
                        os.popen(cmd)

    # SCRIPT FUNCTIONS
    def script_add_part_number(self, arguments):
        self.INFO["PART_NUMBER"] = arguments[0]

    def script_add_description(self, arguments):
        self.INFO["DESCRIPTION"] = arguments[0]
        
    def script_add_order_number(self, arguments):
        self.INFO["ORDER_NUMBER"] = arguments[0]

    def script_add_drawing(self, arguments):
        self.INFO["DRAWING"] = arguments[0]

    def script_add_drawing_rev(self, arguments):
        self.INFO["REV"] = arguments[0]

    def script_add_bom_rev(self, arguments):
        self.INFO["BOM"] = arguments[0]

    def script_add_sn_format(self, arguments):
        self.INFO["SERIAL_NUMBER_FORMAT"] = arguments[0]

    def script_add_balloon(self, arguments): # balloon_number , lbl_part_number
        self.INFO["balloon_"+arguments[0]] = arguments[1]

    def script_add_lbl(self, arguments): # name , balloon
        # lbl_name
        lbl_name = arguments[0]

        # balloon
        balloon = arguments[1]

        # product_part_number
        if "PART_NUMBER" in self.INFO:
            product_part_number = self.INFO["PART_NUMBER"]
        else:
            self.sc.fatal_error("Script missing function: PART_NUMBER()")
            return
        
        # lbl_part_number
        if "balloon_"+balloon in self.INFO:
            lbl_part_number = self.INFO["balloon_"+balloon]
        else:
            self.sc.fatal_error("No such balloon: "+balloon+" Fix script")
            return

        # lbl_size
        if lbl_part_number in self.TEMPLATES:
            lbl_size = self.TEMPLATES[lbl_part_number]
        else:
            self.sc.fatal_error("LABEL PART NUMBER: "+lbl_part_number+" is not in the database. Fix script, or create a new template")
            return

        src = self.path_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+".btw"
        self.sc.test_path(src)
        dst = self.path_main+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" "+lbl_name+".btw"
        self.FILES_THAT_HAVE_BEEN_PRINTED.append([lbl_part_number,lbl_size,lbl_name])
        if not os.path.isfile(dst):
            self.sc.print(dst)
            shutil.copy(src, dst)

    def script_add_main_lbl(self, arguments):
        # MAIN_LBL( format , balloon )

        # GATHER DATA
        # formatt
        formatt = arguments[0]

        # balloon
        balloon = arguments[1]

        # lbl_part_number
        if "balloon_"+balloon in self.INFO:
            lbl_part_number = self.INFO["balloon_"+balloon]
        else:
            self.sc.fatal_error("No such balloon: "+balloon+" Fix script")
            return
        
        # lbl_size
        if lbl_part_number in self.TEMPLATES:
            lbl_size = self.TEMPLATES[lbl_part_number]
        else:
            self.sc.fatal_error("LABEL PART NUMBER: "+lbl_part_number+" is not in the database. Fix script, or create a new template")
            return

        # product_part_number
        if "PART_NUMBER" in self.INFO:
            product_part_number = self.INFO["PART_NUMBER"]
        else:
            self.sc.fatal_error("Script missing function: PART_NUMBER()")
            return
        
        # side
        lbls = []
        for abc in ("", "-A", "-B", "-C"):
            for part_side in ("", " PART", " SIDE"):
                side = part_side+abc
                path = self.path_main_labels_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+" "+formatt+side+".btw"
                if os.path.isfile(path):
                    lbls.append([lbl_part_number, lbl_size, formatt, side, product_part_number])

        # if failed to make any main labels
        if len(lbls) == 0:
            self.sc.fatal_error("Failed to create any main label, make sure all given information is accurate")

        # generate all labels
        for lbl in lbls:
            lbl_part_number = lbl[0]
            lbl_size = lbl[1]
            formatt = lbl[2]
            side = lbl[3]
            product_part_number = lbl[4]

            src = self.path_main_labels_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+" "+formatt+side+".btw"
            dst = self.path_main+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" MAIN LABEL"+side+".btw"
            self.FILES_THAT_HAVE_BEEN_PRINTED.append([lbl_part_number,lbl_size,"MAIN LABEL"+side])
            if not os.path.isfile(dst):
                self.sc.print(dst)
                shutil.copy(src, dst)
    
    def generate_html_report(self, location):
        # save html file
        path = location+"/"+self.INFO["WORK_ORDER"]+".html"
        if not os.path.isdir(location):
            os.makedirs(location)
        
        # WRITE
        html = open(path, 'w')
        # head
        html.write('<html>')
        html.write('    <head>')
        html.write('        <style>')
        html.write('            body, header, footer{')
        html.write('                direction: rtl;')
        html.write('                font-family: "David CLM";')
        html.write('                font-size: 11pt;')
        html.write('            }')
        html.write('            h1{')
        html.write('                font-family: "David CLM";')
        html.write('                font-size: 15pt;')
        html.write('            }')
        html.write('            td{')
        html.write('                font-family: "David CLM";')
        html.write('                font-size: 11pt;')
        html.write('            }')
        html.write('            .grey{')
        html.write('                font-family: "David CLM";')
        html.write('                font-size: 11pt;')
        html.write('                color:black;')
        html.write('            }')
        html.write('            .content, .content tr, .content th, .content td{')
        html.write('                border-collapse: collapse;')
        html.write('                border-color: black;')
        html.write('                border-width: 1px;')
        html.write('                border-style: solid;')
        html.write('                padding: 4px;')
        html.write('                direction: rtl;')
        html.write('                text-align: right;')
        html.write('            }')
        html.write('            .content th{')
        html.write('                color:white;')
        html.write('                background-color: rgb(102,102,102);')
        html.write('            }')
        html.write('        </style>')
        html.write('    </head>')

        # head
        html.write('    <header>')
        html.write('        <h1>טופס אישור הדפסת סימוני חוטים</h1>')
        html.write('    </header>')

        # body
        html.write('    <body>')

        # top info table
        html.write('        <table>')
        html.write('            <tr>')
        html.write('                <td>מק"ט הרכבה:</td>')
        html.write('                <td width="100" class="grey"><u>'+self.INFO["PART_NUMBER"]+'</u></td>')
        html.write('                <td>תיאור:</td>')
        html.write('                <td colspan="5" class="grey"><u>'+self.INFO["DESCRIPTION"]+'</u></td>')
        html.write('            </tr>')
        html.write('            <tr>')
        html.write('                <td>מס’ הזמנה:</td>')
        html.write('                <td class="grey"><u>'+self.INFO["ORDER_NUMBER"]+'</u></td>')
        html.write('                <td width="60">מס’ פק"ע:</td>')
        html.write('                <td class="grey"  width="60"><u>'+self.INFO["WORK_ORDER"]+'</u></td>')
        html.write('                <td>רוויזיה:</td>')
        html.write('                <td class="grey"><u>'+self.INFO["PR"]+'</u></td>')
        html.write('                <td>כמות:</td>')
        html.write('                <td class="grey"><u>'+self.INFO["QTY"]+'</u></td>')
        html.write('            </tr>')
        html.write('            <tr>')
        html.write('                <td>מק"ט שרטוט:</td>')
        html.write('                <td class="grey"><u>'+self.INFO["DRAWING"]+'</u></td>')
        html.write('                <td>רוויזיה:</td>')
        html.write('                <td class="grey"><u>'+self.INFO["REV"]+'</u></td>')
        html.write('                <td colspan="2">רוויזיה של BOM:</td>')
        html.write('                <td colspan="2" class="grey"><u>'+self.INFO["BOM"]+'</u></td>')
        html.write('            </tr>')
        html.write('        </table>')

        # signitures
        html.write('        <p>-----------------------------------------------------------------------------------------------------------------</p>')
        html.write('        <table>')
        html.write('            <tr>')
        html.write('                <td>הודפס ע"י</td>')
        html.write('                <td width="150">:_______________</td>')
        html.write('                <td>בתאריך</td>')
        html.write('                <td>:_______________</td>')
        html.write('            </tr>')
        html.write('            <tr>')
        html.write('                <td>נבדק ע"י</td>')
        html.write('                <td width="150">:_______________</td>')
        html.write('                <td>בתאריך</td>')
        html.write('                <td>:_______________</td>')
        html.write('            </tr>')
        html.write('        </table>')

        # printed files
        html.write('        <p>-----------------------------------------------------------------------------------------------------------------</p>')
        html.write('        <p>רשימת סימונים:</p>')
        html.write('        <table class="content">')
        html.write('            <tr>')
        html.write('                <th width="40">#</th>')
        html.write('                <th width="322">תיאור</th>')
        html.write('                <th width="200">מק"ט</th>')
        html.write('                <th width="40">גודל</th>')
        html.write('            </tr>')
        i = 0
        for lbl in self.FILES_THAT_HAVE_BEEN_PRINTED:
            i += 1
            if i < 21:
                # self.FILES_THAT_HAVE_BEEN_PRINTED.append([lbl_part_number,lbl_size,"MAIN LABEL"+side])
                lbl_part_number = lbl[0]
                size = lbl[1]
                name = lbl[2]
                html.write('        <tr>')
                html.write('            <td>'+str(i)+'.</td>')
                html.write('            <td class="grey">'+name+'</td>')
                html.write('            <td class="grey">'+lbl_part_number+'</td>')
                html.write('            <td class="grey">'+size+'</td>')
                html.write('        </tr>')
        x = i
        for _ in range(20-x):
            i += 1
            html.write('        <tr>')
            html.write('            <td>'+str(i)+'.</td>')
            html.write('            <td class="grey"></td>')
            html.write('            <td class="grey"></td>')
            html.write('            <td class="grey"></td>')
            html.write('        </tr>')

        html.write('        </table>')
        html.write('        <p>-----------------------------------------------------------------------------------------------------------------</p>')
        # end
        html.write('        <table class="content">')
        html.write('            <tr>')
        html.write('                <td style="padding: 10px;">')
        html.write('                    <p style="line-height: 0.5;">הערות:</p>')
        html.write('                    <p style="line-height: 0.5;">_____________________________________________________________________________________________________</p>')
        html.write('                    <p style="line-height: 0.5;">_____________________________________________________________________________________________________</p>')
        html.write('                    <p style="line-height: 0.5;">_____________________________________________________________________________________________________</p>')
        html.write('                </td>')
        html.write('            </tr>')
        html.write('        </table>')
        html.write('    </body>')
        html.write('    <footer>')
        html.write('        <br>')
        html.write('        <text>תחנת בדיקה חשמלית והדפסת סימוני חוטים</text>')
        html.write('        <br>')
        html.write('        <text>טופס לא מבוקר&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp</text>')
        html.write('        <text>עמוד 1 מתוך 1</text>')
        html.write('    </footer>')
        html.write('</html>')

        html.close()
        os.popen(path)
    
    def inventory(self):
        # load table
        inventory_database = self.sc.load_database(self.path_main+"/Inventory.csv", ("BOX-ID", "PART-NUMBER"))
        last_id = 0
        if len(inventory_database) > 1:
            self.sc.print("BOX-ID  PART NUMBER")
        ignore = True
        for key, value in inventory_database.items():
            if not ignore:
                if len(inventory_database) > 1:
                    self.sc.print(key.zfill(4)+"    "+value[0])
                try:
                    key = int(key)
                    if key > last_id:
                        last_id = key
                except:
                    key = 0
            else:
                ignore = False

        # choose what to do
        action = self.sc.choose("Choose inventory action", ("ADD", "DELETE", "CANCEL"))
        if action == "ADD":
            boxid = last_id + 1
            part_number = self.sc.input("Box #"+str(boxid)+" Insert TMS PART NUMBER").upper()
            if part_number in self.TEMPLATES:
                size = self.TEMPLATES[part_number]
            else:
                self.sc.error("TMS PART NUMBER is not in the databse")
                self.sc.restart()
                return
            inventory_database[boxid] = (part_number, )
            self.sc.save_database(self.path_main+"/Inventory.csv", inventory_database)
            file = open(self.path_main+"/TMS_BOX.csv", 'w')
            file.write("BOX ID,PART NUMBER,SIZE\n")
            file.write(str(boxid)+","+part_number+","+size)
            file.close()
            os.popen(self.path_inventory_label)

        if action == "DELETE":
            boxid = self.sc.input("Insert BOX-ID to delete") or 0
            if boxid in inventory_database:
                inventory_database[boxid] = "DELETE"
            else:
                self.sc.error("This BOX-ID is not in the database")
                self.sc.restart()
                return
            temp = {}
            for boxid, part_number in inventory_database.items():
                if part_number != "DELETE":
                    temp[boxid] = part_number
            
            self.sc.save_database(self.path_main+"/Inventory.csv", temp)
        
        if action == "CANCEL":
            # restart
            self.sc.restart()
            return

        # restart
        self.sc.restart()
main()