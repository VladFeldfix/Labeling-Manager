from SmartConsole import *
import os
import shutil

class main:
    # constructor
    def __init__(self):
        # load smart console
        self.sc = SmartConsole("Labeling Manager", "4.0")

        # set-up main memu
        self.sc.main_menu["MAKE NEW LABELS"] = self.new
        self.sc.main_menu["PRINT LABELS"] = self.print
        self.sc.main_menu["PRINT DHR LABELS"] = self.dhr

        # get settings
        self.path_main = self.sc.get_setting("Labeling folder")
        self.path_templates = self.path_main+"/_Templates_"
        self.path_main_labels_templates = self.path_main+"/_Templates_/Main Labels"

        # test all paths
        self.sc.test_path(self.path_main)
        self.sc.test_path(self.path_templates)
        self.sc.test_path(self.path_main_labels_templates)

        # load databases
        self.load_databases()

        # display main menu
        self.sc.start()
    
    def load_databases(self):
        # load databases
        self.TEMPLATES = {} # {part_number: size}
        self.TEMPLATES_MAIN = {} # {part_number: (size, formatt, side)}
        self.INFO = {}

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
        
        # self.TEMPLATES_MAIN
        for path, dirs, files in os.walk(self.path_templates):
            for file in files:
                if ".btw" in file:
                    filename = file.replace(".btw", "")
                    filename = filename.split(",")
                    if len(filename) == 6:
                        # 0 TMS
                        # 1 TEMPLATE
                        # 2 lbl_part_number1
                        # 3 lbl_size
                        # 4 format
                        # 5 SIDE-A
                        lbl_part_number = filename[2]
                        size = filename[3]
                        formatt = filename[4]
                        side = filename[5]
                        self.TEMPLATES_MAIN[lbl_part_number] = (size, formatt, side)

    def new(self):
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
                
                if os.path.isfile(script_file):
                    # run script
                    functions = {}
                    functions["PART_NUMBER"] = (self.script_add_part_number, 1)
                    functions["DESCRIPTION"] = (self.script_add_description, 1)
                    functions["ORDER_NUMBER"] = (self.script_add_order_number, 1)
                    functions["DRAWING"] = (self.script_add_drawing, 1)
                    functions["REV"] = (self.script_add_drawing_rev, 1)
                    functions["BOM"] = (self.script_add_bom_rev, 1)
                    functions["SERIAL_NUMBER_FORMAT"] = (self.script_add_sn_format, 1)
                    functions["BALLOON"] = (self.script_add_balloon, 2)
                    functions["LBL"] = (self.script_add_lbl, 2)
                    functions["MAIN_LBL"] = (self.script_add_main_lbl, 2)
                    self.sc.run_script(script_file, functions)
        else:
            self.sc.error("Invalid PRODUCT PART NUMBER")
        
        # restart
        self.sc.restart()

    def print(self):
        # get part number
        part_number = self.sc.input("Insert PRODUCT PART NUMBER").upper()

        if not part_number == "":
            pass
        else:
            self.sc.error("Invalid PRODUCT PART NUMBER")

        # restart
        self.sc.restart()
    
    def dhr(self):
        # restart
        self.sc.restart()

    # SCRIPT FUNCTIONS
    def script_add_part_number(self, arguments):
        self.INFO["part_number"] = arguments[0]

    def script_add_description(self, arguments):
        self.INFO["description"] = arguments[0]
        
    def script_add_order_number(self, arguments):
        self.INFO["order_number"] = arguments[0]

    def script_add_drawing(self, arguments):
        self.INFO["drawing"] = arguments[0]

    def script_add_drawing_rev(self, arguments):
        self.INFO["drawing_rev"] = arguments[0]

    def script_add_bom_rev(self, arguments):
        self.INFO["bom_reV"] = arguments[0]

    def script_add_sn_format(self, arguments):
        self.INFO["sn_format"] = arguments[0]

    def script_add_balloon(self, arguments): # balloon_number , lbl_part_number
        self.INFO["balloon_"+arguments[0]] = arguments[1]

    def script_add_lbl(self, arguments): # name , balloon
        # lbl_name
        lbl_name = arguments[0]

        # balloon
        balloon = arguments[1]

        # product_part_number
        if "part_number" in self.INFO:
            product_part_number = self.INFO["part_number"]
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
        dst = self.path_main+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" "+lbl_name+".btw"
        if not os.path.isfile(dst):
            self.sc.print(dst)
            shutil.copy(src, dst)

    def script_add_main_lbl(self, arguments):
        pass

main()