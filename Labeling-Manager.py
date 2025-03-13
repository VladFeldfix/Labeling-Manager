# Download SmartConsole.py from: https://github.com/VladFeldfix/Smart-Console/blob/main/SmartConsole.py
from SmartConsole import *
import shutil

class main:
    # constructor
    def __init__(self):
        # load smart console
        self.sc = SmartConsole("Labeling Manager", "4.0")

        # set-up main memu
        self.sc.add_main_menu_item("MAKE NEW LABELS", self.new)
        self.sc.add_main_menu_item("PRINT LABELS", self.print)
        self.sc.add_main_menu_item("INVENTORY", self.inventory)

        # get settings
        self.info = {}
        self.templates = {}
        self.templates_main = {}
        self.path_main = self.sc.get_setting("Labeling folder")
        self.path_templates = self.path_main+"/.Templates"
        self.path_main_lbl_templates = self.path_main+"/.Templates/Main Labels"
        self.path_db_pn = self.path_main+"/.Database/INV Part Numbers.csv"
        self.path_db_inv = self.path_main+"/.Database/Inventory.csv"
        self.path_db_wo = self.path_main+"/.Database/Printed Work Orders.csv"
        self.inv_lbl = self.path_main+"/.Database/LBL DATABASE AR00179 INV.btw"
        self.inv_csv = self.path_main+"/.Database/Inventory LBL.csv"

        # test all paths
        self.sc.test_path(self.inv_lbl)
        self.sc.test_path(self.inv_csv)
        self.sc.test_path(self.path_main)
        self.sc.test_path(self.path_templates)
        self.sc.test_path(self.path_main_lbl_templates)
        self.sc.test_path(self.path_db_pn)
        self.sc.test_path(self.path_db_inv)
        self.sc.test_path(self.path_db_wo)

        # load databases
        self.load_database()

        # display main menu
        self.sc.start()
    
    ################################################################ MAIN MENU FUNCTIONS ################################################################
    def new(self):
        # load database
        self.load_database()

        # get part number
        part_number = self.sc.input("Insert product part number [Without R-]")

        # process
        if not part_number == "":
            folder = self.path_main+"/"+part_number.upper()
            script_file = folder+"/script.txt"
            if not os.path.isdir(folder):
                self.sc.warning("There is no folder for this product!")
                if self.sc.question("Would you like to create a new folder: "+folder):
                    os.makedirs(folder)
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
                    file.write("MAIN_LBL( balloon )\n")
                    file.close()
                    self.sc.open_folder(folder)
                    os.popen(script_file)
                    self.sc.input("Edit the script file and press ENTER to continue")
                else:
                    self.sc.warning("Mission aborted!")
            if os.path.isfile(script_file):
                self.run_script(script_file)
            self.sc.open_folder(folder)
        else:
            self.sc.error("Invalid product part number")

        # restart
        self.sc.restart()

    def print(self):
        # load database
        self.load_database()

        # get work order
        wo = self.sc.input("Insert work order")
        if wo == "":
            self.sc.error("Invalid work order!")
            self.sc.restart()
            return
        if wo in self.work_orders:
            self.sc.error("Work order is not new!")
            self.sc.restart()
            return
        
        # get part number
        part_number = self.sc.input("Insert product part number [Without R-]")
        if part_number == "":
            self.sc.error("Invalid part number!")
            self.sc.restart()
            return
        path_to_product = self.path_main+"/"+part_number.upper()
        script_file = path_to_product+"/script.txt"
        if not os.path.isdir(path_to_product):
            self.sc.error("There is no folder for "+part_number+"! go to MAIN MENU > MAKE NEW LABELS")
            self.sc.restart()
            return
        
        # read script
        if not os.path.isfile(script_file):
            self.sc.error("There is no script file for "+part_number+"!")
            self.sc.restart()
            return
        self.run_script(script_file)

        # get first serial number
        if not "SERIAL_NUMBER_FORMAT" in self.info:
            self.sc.error("Script missing function: SERIAL_NUMBER_FORMAT()")
            self.sc.restart()
            return
        first_serial_number = self.sc.input("Insert first serial number in format: "+self.info["SERIAL_NUMBER_FORMAT"]).upper()
        if len(first_serial_number) != len(self.info["SERIAL_NUMBER_FORMAT"]):
            self.sc.error("Invalid serial number format!")
            self.sc.restart()
            return
        first_serial_number_int = first_serial_number[-4:]
        try:
            first_serial_number_int = int(first_serial_number_int)
        except:
            self.sc.error("Invalid serial number! last 4 digits must be a number 0000-9999")
            self.sc.restart()
            return
        
        # get wo size
        size = self.sc.input("Insert work order size")
        try:
            size = int(size)
        except:
            self.sc.error("Invalid work order size!")
            self.sc.restart()
            return
        
        # make all serial numbers
        path = path_to_product+"/SerialNumbers.csv"
        file = open(path, 'w')
        file.write("SN\n")
        for i in range(first_serial_number_int, first_serial_number_int+size):
            suffix = str(i).zfill(4)
            preffix = first_serial_number[:-4]
            file.write(preffix+suffix+"\n")
        file.close()

        # write to the database
        self.work_orders[wo] = (self.sc.today(), first_serial_number, str(size))
        self.sc.save_database(self.path_db_wo, self.work_orders)

        # open all files
        for path, dirs, files in os.walk(path_to_product):
            for file in files:
                if ".btw" in file:
                    cmd = path_to_product+"/"+file
                    if os.path.isfile(cmd):
                        os.popen(cmd)
        self.sc.open_folder(path_to_product)
        
        # restart
        self.sc.restart()

    def inventory(self):
        # load database
        self.load_database()

        # display inventory
        pn_qty = {}
        last_id = 0
        for inv in self.inventory:
            box_id = inv[0]
            try:
                box_id = int(box_id)
            except:
                box_id = 0
            pn = inv[1]
            if last_id < box_id:
                last_id = box_id
            last_id += 1
            if not pn in pn_qty:
                pn_qty[pn] = 1
            else:
                pn_qty[pn] += 1
        longest_pn = ""
        for pns in self.part_numbers:
            pn = pns[0]
            if len(pn) > len(longest_pn):
                longest_pn = pn
        longest_cust_pn = ""
        for cust_pns in self.part_numbers:
            cust_pn = cust_pns[1]
            if len(cust_pn) > len(longest_cust_pn):
                longest_cust_pn = cust_pn
        longest_description = ""
        for descs in self.part_numbers:
            desc = descs[2]
            if len(desc) > len(longest_description):
                longest_description = desc
        pn_spaces = (len(longest_pn)+2)-len("PART NUMBER")
        pn_spaces = " "*pn_spaces
        cust_pn_spaces = (len(longest_cust_pn)+2)-len("CUSTOMER PART NUMBER")
        cust_pn_spaces = " "*cust_pn_spaces
        ds_spaces = (len(longest_description)+2)-len("DESCRIPTION")
        ds_spaces = " "*ds_spaces
        self.sc.print("PART NUMBER"+pn_spaces+" | CUSTOMER PART NUMBER"+cust_pn_spaces+" | DESCRIPTION"+ds_spaces+" | QTY.",'red')
        part_numbers = []
        descriptions = {}
        report = []
        for pns in self.part_numbers[1:]:
            pn = pns[0]
            cust_pn = pns[1]
            description = pns[2]
            part_numbers.append(pn)
            descriptions[pn] = description
            pn_spaces = (len(longest_pn)+2)-len(pn)
            pn_spaces = " "*pn_spaces
            cust_pn_spaces = (len(longest_cust_pn)+2)-len(cust_pn)
            cust_pn_spaces = " "*cust_pn_spaces
            ds_spaces = (len(longest_description)+2)-len(description)
            ds_spaces = " "*ds_spaces
            if pn in pn_qty:
                qty = str(pn_qty[pn])
            else:
                qty = "0"
            self.sc.print(pn+pn_spaces+" | "+cust_pn+cust_pn_spaces+" | "+description+ds_spaces+" | "+qty)
            report.append((pn,cust_pn,description,qty))

        
        # choose an action
        action = self.sc.choose("Choose inventory action", ("ADD", "DELETE", "GENERATE REPORT", "CANCEL"))
        if action == "ADD":
            # get part number
            item = self.sc.input("Insert item part number")
            if item == "":
                self.sc.error("Invalid part number")
                self.sc.restart()
                return

            if not item in part_numbers:
                self.sc.error("Part number is not in the database!\nUpdate file "+self.path_db_pn)
                self.sc.restart()
                return
            
            # add part number to the inventory
            self.inventory.append((last_id,item))
            description = descriptions[item]
            self.sc.good("Part number was successfully added to the database!")
            self.sc.save_csv(self.path_db_inv, self.inventory)
            file = open(self.inv_csv, 'w')
            file.write("BoxID,PartNumber,Description\n")
            file.write(str(last_id)+","+item+","+description+"\n")
            file.close()
            os.popen(self.inv_lbl)

        if action == "DELETE":
            n = self.sc.input("Insert Box-ID to delete")
            if n == "":
                # restart
                self.sc.error("Invalid Box-ID")
                self.sc.restart()
                return
            try:
                n = int(n)
            except:
                # restart
                self.sc.error("Invalid Box-ID")
                self.sc.restart()
                return
            n = str(n)
            was_deleted = False
            new_inv = [["Box-ID","Part Number"]]
            for inv in self.inventory[1:]:
                box_id = inv[0]
                part_number = inv[1]
                if box_id != n:
                    new_inv.append((box_id,part_number))
                else:
                    was_deleted = True
            
            if was_deleted:
                self.sc.good("Box-ID "+n+" was successfully deleted!")
                self.sc.save_csv(self.path_db_inv, new_inv)
            else:
                # restart
                self.sc.error("Box-ID dosen't exist!")
                self.sc.restart()
                return
        
        if action == "GENERATE REPORT":
            report.sort(key=lambda x: x[3])
            file = open(self.path_main+"/.Database/Inventory Roport.html", 'w')
            file.write("<html>\n")
            file.write("\t<head>\n")
            file.write("\t\t<style>\n")
            file.write("\t\t\thtml{\n")
            file.write("\t\t\t\tfont-family: Arial, Helvetica, sans-serif;\n")
            file.write("\t\t\t}\n")
            file.write("\t\t\ttable{\n")
            file.write("\t\t\t\tborder-collapse: collapse;\n")
            file.write("\t\t\t}\n")
            file.write("\t\t\tth{\n")
            file.write("\t\t\t\tbackground-color:#4f4f4f;\n")
            file.write("\t\t\t\tcolor:white;\n")
            file.write("\t\t\t}\n")
            file.write("\t\t\tth, td{\n")
            file.write("\t\t\t\ttext-align: left;\n")
            file.write("\t\t\t\tpadding: 8px;\n")
            file.write("\t\t\t}\n")
            file.write("\t\t\ttable, tr, th, td{\n")
            file.write("\t\t\t\tborder-color: black;\n")
            file.write("\t\t\t\tborder: black solid 1px;\n")
            file.write("\t\t\t}\n")
            file.write("\t\t</style>\n")
            file.write("\t</head>\n")
            file.write("\t<body>\n")
            file.write("\t\t<table>\n")
            file.write("\t\t\t<tr>\n")
            file.write("\t\t\t\t<th>PART NUMBER</th>\n")
            file.write("\t\t\t\t<th>CUSTOMER PART NUMBER</th>\n")
            file.write("\t\t\t\t<th>DESCRIPTION</th>\n")
            file.write("\t\t\t\t<th>QTY.</th>\n")
            file.write("\t\t\t</tr>\n")
            for line in report:
                color = ""
                qty = int(line[3])
                if qty == 0:
                    color = " style = 'background-color:#d93b3b;'"
                if qty == 1:
                    color = " style = 'background-color:#dee344;'"
                if qty > 1:
                    color = " style = 'background-color:#72d682;'"
                file.write("\t\t\t<tr"+color+">\n")
                file.write("\t\t\t\t<td>"+line[0]+"</td>\n")
                file.write("\t\t\t\t<td>"+line[1]+"</td>\n")
                file.write("\t\t\t\t<td>"+line[2]+"</td>\n")
                file.write("\t\t\t\t<td>"+line[3]+"</td>\n")
                file.write("\t\t\t</tr>\n")
            file.write("\t\t</table>\n")
            file.write("\t</body>\n")
            file.write("</html>\n")
            file.close()
            os.popen(self.path_main+"/.Database/Inventory Roport.html")

        if action == "CANCEL":
            # restart
            self.sc.restart()
            return

        # restart
        self.sc.restart()

    ################################################################ DATABASE FUNCTIONS ################################################################
    def load_database(self):
        # load database
        self.part_numbers = self.sc.load_csv(self.path_db_pn)
        self.inventory = self.sc.load_csv(self.path_db_inv)
        self.work_orders = self.sc.load_database(self.path_db_wo, ["Work Order", "Date Printed", "First SN", "Size"])

        # load templates
        self.templates = {} # {lbl_part_number: [template file location, (LBL, TMS, or SPL), (1-2, 3-8, ... 1_1-2)]}
        for path, dirs, files in os.walk(self.path_templates):
            for file in files:
                if ".btw" in file:
                    filename = file.replace(".btw", "")
                    filename = filename.split(" ")
                    if len(filename) == 4:
                        # 0 TMS
                        # 1 TEMPLATE
                        # 2 lbl_part_number
                        # 3 lbl_size
                        lbl_type = filename[0]
                        lbl_part_number = filename[2]
                        size = filename[3]
                        self.templates[lbl_part_number] = (path+"/"+file, lbl_type, size)
        
        # load templates for main lbl
        for path, dirs, files in os.walk(self.path_main_lbl_templates):
            for file in files:
                if ".btw" in file:
                    filename = file.replace(".btw", "")
                    filename = filename.split(" ")
                    if len(filename) == 6 or len(filename) == 7:
                        # 0 TMS 
                        # 1 TEMPLATE 
                        # 2 R-606101044
                        # 3 3-4
                        # 4 MAIN
                        # 5 LABEL
                        # 6 SIDE-A

                        # lbltype = self.templates_main[lbl_part_number][0]
                        # lbl_size = self.templates_main[lbl_part_number][1]
                        # sides = self.templates_main[lbl_part_number][2]
                        
                        lbltype = filename[0]
                        lbl_pn = filename[2]
                        lbl_size = filename[3]
                        if len(filename) == 6:
                            self.templates_main[lbl_pn] = [lbltype, lbl_size, ["",]]

                        elif len(filename) == 7:
                            side = filename[6]
                            if not lbl_pn in self.templates_main:
                                self.templates_main[lbl_pn] = [lbltype, lbl_size, [" "+side,]]
                            else:
                                self.templates_main[lbl_pn][2].append(" "+side)

    ################################################################ SCRIPT FUNCTIONS ################################################################
    def run_script(self, script_file):
        self.sc.test_path(script_file)
        functions = {}
        functions["PART_NUMBER"] = (self.script_add_part_number, ("PART_NUMBER",))
        functions["DESCRIPTION"] = (self.script_add_description, ("DESCRIPTION",))
        functions["ORDER_NUMBER"] = (self.script_add_order_number, ("ORDER_NUMBER",))
        functions["DRAWING"] = (self.script_add_drawing, ("DRAWING",))
        functions["REV"] = (self.script_add_drawing_rev, ("REV",))
        functions["BOM"] = (self.script_add_bom_rev, ("BOM",))
        functions["SERIAL_NUMBER_FORMAT"] = (self.script_add_sn_format, ("FORMAT",))
        functions["BALLOON"] = (self.script_add_balloon, ("BALLOON NUMBER" , "LBL PART NUMBER"))
        functions["LBL"] = (self.script_add_lbl, ("NAME" , "BALLOON"))
        functions["MAIN_LBL"] = (self.script_add_main_lbl, ("BALLOON",))
        self.sc.run_script(script_file, functions)
    
    def script_add_part_number(self, arguments):
        self.info["PART_NUMBER"] = arguments[0]
    
    def script_add_description(self, arguments):
        self.info["DESCRIPTION"] = arguments[0]

    def script_add_sn_format(self, arguments): # format
        self.info["SERIAL_NUMBER_FORMAT"] = arguments[0]
    
    def script_add_balloon(self, arguments): # balloon_number , lbl_part_number
        self.info["balloon_"+arguments[0]] = arguments[1]
    
    def script_add_order_number(self, arguments): # ORDER_NUMBER
        self.info["ORDER_NUMBER"] = arguments[0]

    def script_add_drawing(self, arguments): # DRAWING
        self.info["DRAWING"] = arguments[0]
    
    def script_add_drawing_rev(self, arguments): # DRAWING REV
        self.info["DRAWING_REV"] = arguments[0]
    
    def script_add_bom_rev(self, arguments): # BOM
        self.info["BOM"] = arguments[0]
    
    def script_add_lbl(self, arguments): # name , balloon
        # lbl_name
        lbl_name = arguments[0]

        # balloon
        balloon = arguments[1]

        # product_part_number
        if "PART_NUMBER" in self.info:
            product_part_number = self.info["PART_NUMBER"]
        else:
            self.sc.fatal_error("Script missing function: PART_NUMBER()")
            return
        self.sc.test_path(self.path_main+"/"+product_part_number)

        # lbl_part_number
        if "balloon_"+balloon in self.info:
            lbl_part_number = self.info["balloon_"+balloon]
        else:
            self.sc.fatal_error("No such balloon: "+balloon+" Fix script")
            return
        
        # create a copy from a template
        if lbl_part_number in self.templates:
            src = self.templates[lbl_part_number][0] # template file location
            lbltype = self.templates[lbl_part_number][1] # LBL, TMS, SPL
            lbl_size = self.templates[lbl_part_number][2] # 1-2, 3-8, 1_1-2
        else:
            self.sc.fatal_error("There is no template file for "+lbl_part_number)
            return
        dst = self.path_main+"/"+product_part_number+"/"+lbltype+" "+product_part_number+" "+lbl_part_number+" "+lbl_size+" "+lbl_name+".btw"

        # create a new main lbl
        if not os.path.isfile(dst):
            shutil.copy(src, dst)
            self.sc.good("Created: "+dst)
    
    def script_add_main_lbl(self,arguments): # balloon
        # balloon
        balloon = arguments[0]

        # product_part_number
        if "PART_NUMBER" in self.info:
            product_part_number = self.info["PART_NUMBER"]
        else:
            self.sc.fatal_error("Script missing function: PART_NUMBER()")
            return
        self.sc.test_path(self.path_main+"/"+product_part_number)
        
        # lbl_part_number
        if "balloon_"+balloon in self.info:
            lbl_part_number = self.info["balloon_"+balloon]
        else:
            self.sc.fatal_error("No such balloon: "+balloon+" Fix script")
            return

        # get template data
        lbltype = ""
        lbl_size = ""
        sides = []
        if lbl_part_number in self.templates_main:
            lbltype = self.templates_main[lbl_part_number][0]
            lbl_size = self.templates_main[lbl_part_number][1]
            sides = self.templates_main[lbl_part_number][2]

        # create a new main lbl
        for side in sides:
            # TMS TEMPLATE R-606101044 3-4 MAIN LABEL SIDE-A.btw
            src = self.path_main_lbl_templates+"/"+lbltype+" TEMPLATE "+lbl_part_number+" "+lbl_size+" MAIN LABEL"+side+".btw"
            self.sc.test_path(src)
            dst = self.path_main+"/"+product_part_number+"/"+lbltype+" "+product_part_number+" "+lbl_part_number+" "+lbl_size+" MAIN LABEL"+side+".btw"
            if not os.path.isfile(dst):
                shutil.copy(src, dst)
                self.sc.good("Created: "+dst)
main()