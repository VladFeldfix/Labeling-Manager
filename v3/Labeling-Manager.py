from SmartConsole import *
import os
import shutil

class main:
    def __init__(self):
        # setup smart console
        self.sc = SmartConsole("Labeling-Manager", "1.0")

        # create main menu
        self.sc.main_menu["PRINT"] = self.print_wo
        self.sc.main_menu["MAKE NEW"] = self.make_new

        # setup a directoy and make sure all paths exist
        self.loc_tms = self.sc.get_setting("TMS location")
        self.loc_tms_templates = self.loc_tms+"/_Templates_"
        self.loc_tms_main_label_templates = self.loc_tms+"/_Templates_/Main Labels"
        self.sc.test_path(self.loc_tms)
        self.sc.test_path(self.loc_tms_templates)
        self.sc.test_path(self.loc_tms_main_label_templates)
        
        # GLOBAL VARIABLES
        self.PRODUCT_PART_NUMBER = ""
        self.BOM_REV = ""
        self.DRAWING = ""
        self.DRAWING_REV = ""
        self.SERIAL_NUMBER_FORMAT = ""
        self.BALLOONS = {}
        self.LABELS = {}
        self.MAIN_LABEL = []
        self.TEMPLATES = self.load_templates()
        
        # run main menu
        self.sc.start()

        # run gui
        self.sc.gui()
    
    def print_wo(self):
        # get wo
        self.WORK_ORDER = self.sc.input("Insert WORK ORDER")

        # make sure wo is new
        exists = False
        for path, directories, files in os.walk(self.loc_tms):
            for file in files:
                if self.WORK_ORDER in file:
                    self.sc.error("Work Order not new!")
                    self.sc.abort()
                    return
        
        # if wo is new
        # get pn
        self.PRODUCT_PART_NUMBER = self.sc.input("Insert PRODUCT PART NUMBER").upper()
        path = self.loc_tms+"/"+self.PRODUCT_PART_NUMBER+"/script.txt"
        if os.path.isfile(path):
            # get info
            self.read_script(path)
            self.FIRST_SERIAL_NUMBER = self.sc.input("Insert FIRST SERIAL NUMBER").upper()
            if not self.serial_number_format_validation(self.FIRST_SERIAL_NUMBER):
                self.sc.error("Invalid SERIAL NUMBER: "+self.FIRST_SERIAL_NUMBER+"\nExpected format: FLT0000-0000")
                self.sc.abort()
                return
            self.QTY = self.sc.input("Insert WORK ORDER SIZE")
            self.PR = self.sc.input("Insert P.R.")
            self.generate_serial_numbers()
            self.generate_html_report()
            self.open_labels()
        else:
            self.sc.error("Missing file: "+path)
        
        # restart
        self.sc.restart()

    def make_new(self):
        # get part number
        self.PRODUCT_PART_NUMBER = self.sc.input("Insert PRODUCT PART NUMBER").upper()
        path = self.loc_tms+"/"+self.PRODUCT_PART_NUMBER+"/script.txt"
        if self.PRODUCT_PART_NUMBER == "":
            self.sc.error("Invalid serial number")
        else:
            # make directory
            if not os.path.isdir(self.loc_tms+"/"+self.PRODUCT_PART_NUMBER):
                os.makedirs(self.loc_tms+"/"+self.PRODUCT_PART_NUMBER)

            # make script file
            if not os.path.isfile(path):
                # make script file
                file = open(path, 'w')
                file.write("PRODUCT_PART_NUMBER("+self.PRODUCT_PART_NUMBER+")\n")
                file.write("BOM_REV()\n")
                file.write("DRAWING()\n")
                file.write("DRAWING_REV()\n")
                file.write("SERIAL_NUMBER_FORMAT( FLT0000-0000 )\n")
                file.write("BALLOON( balloon_number , tms_part_number )\n")
                file.write("LABEL( name , balloon_number )\n")
                file.write("MAIN_LABEL( format , balloon_number )\n")
                file.close()
                os.popen(path)
                self.sc.input("Finish editing the script and press ENTER to continue")
            
            # read script file
            self.read_script(path)

            # make new labels
            new_labels = []
            for lbl_name, balloon_number in self.LABELS.items():
                # get lbl_part_number
                if balloon_number in self.BALLOONS:
                    lbl_part_number = self.BALLOONS[balloon_number]
                else:
                    self.sc.fatal_error("No Such balloon: "+balloon_number)
                
                # get lbl_size
                if lbl_part_number in self.TEMPLATES:
                    lbl_size = self.TEMPLATES[lbl_part_number]
                else:
                    self.sc.fatal_error("No template for TMS part number: "+lbl_part_number)
                
                # get product_part_number
                product_part_number = self.PRODUCT_PART_NUMBER

                # make new lbl
                src = self.loc_tms_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+".btw"
                self.sc.test_path(src)
                dst = self.loc_tms+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" "+lbl_name+".btw"
                new_labels.append([src, dst])
            
            # make MAIN label
            if len(self.MAIN_LABEL) == 2:
                # get formatt
                formatt = self.MAIN_LABEL[0]

                # get balLoon_number
                balLoon_number = self.MAIN_LABEL[1]

                # get lbl_part_number
                if balloon_number in self.BALLOONS:
                    lbl_part_number = self.BALLOONS[balloon_number]
                else:
                    self.sc.fatal_error("No Such balloon: "+balloon_number)

                # get lbl_size
                if lbl_part_number in self.TEMPLATES:
                    lbl_size = self.TEMPLATES[lbl_part_number]
                else:
                    self.sc.fatal_error("No template for TMS part number: "+lbl_part_number)

                # for labels that are double sided
                made_a_main = False
                for side in ("A", "B"):
                    src = self.loc_tms_main_label_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+" "+formatt+" SIDE "+side+".btw"
                    dst = self.loc_tms+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" MAIN LABEL SIDE "+side+".btw"
                    if os.path.isfile(src):
                        new_labels.append([src, dst])
                        made_a_main = True
                
                # for labels that have several parts
                for part in ("A", "B", "C"):
                    src = self.loc_tms_main_label_templates+"/TMS TEMPLATE "+lbl_part_number+" "+lbl_size+" "+formatt+" PART "+part+".btw"
                    dst = self.loc_tms+"/"+product_part_number+"/TMS "+product_part_number+" "+lbl_part_number+" "+lbl_size+" MAIN LABEL PART "+part+".btw"
                    if os.path.isfile(src):
                        new_labels.append([src, dst])
                        made_a_main = True
                
                if not made_a_main:
                    self.sc.fatal_error("Failed to make the main label. Make sure there is a main label template for \nPart number: "+lbl_part_number+"\nFormat: "+formatt)

            # generate labels
            for lbl in new_labels:
                src = lbl[0]
                dst = lbl[1]
                if os.path.isfile(src) and not os.path.isfile(dst):
                    self.sc.print(dst)
                    shutil.copy(src, dst)
                
                path = self.loc_tms+"/"+self.PRODUCT_PART_NUMBER+"/SerialNumbers.csv"
                if not os.path.isfile(path):
                    file = open(path, 'w')
                    file.write("SN")
                    file.close()
            
            # open labels
            self.open_labels()
            
            # restart
            self.sc.restart()

    def generate_html_report(self):
        pass

    def generate_serial_numbers(self):
        if self.SERIAL_NUMBER_FORMAT != "":
            pass
        else:
            self.sc.fatal_error("Not given serial number format")
    
    def serial_number_format_validation(self, sn):
        if len(sn) != 12:
            return False
        if sn[0:3] != "FLT":
            return False
        if sn[7] != "-":
            return False
        try:
            first_number = int(sn[8:])
        except:
            return False
        return True
    
    def open_labels(self):
        for path, directories, files in os.walk(self.loc_tms+"/"+self.PRODUCT_PART_NUMBER):
            for file in files:
                if ".btw" in file:
                    cmd = self.loc_tms+"/"+self.PRODUCT_PART_NUMBER+"/"+file
                    if os.path.isfile(cmd):
                        os.popen(cmd)

    def load_templates(self):
        return_value = {}
        for path, directories, files in os.walk(self.loc_tms_templates):
            for file in files:
                if ".btw" in file:
                    file = file.replace(".btw", "")
                    array = file.split(" ")
                    # TMS TEMPLATE lbl_part_number lbl_size
                    # 0 TMS
                    # 1 TEMPLATE
                    # 2 lbl_part_number 
                    # 3 lbl_size
                    if len(array) == 4:
                        return_value[array[2]] = array[3]
        return return_value

    def read_script(self, path):
        functions = {}
        functions["PRODUCT_PART_NUMBER"] = (self.get_PRODUCT_PART_NUMBER, 1)
        functions["BOM_REV"] = (self.get_BOM_REV, 1)
        functions["DRAWING"] = (self.get_DRAWING, 1)
        functions["DRAWING_REV"] = (self.get_DRAWING_REV, 1)
        functions["SERIAL_NUMBER_FORMAT"] = (self.get_SERIAL_NUMBER_FORMAT, 1)
        functions["BALLOON"] = (self.get_BALLOON, 2)
        functions["LABEL"] = (self.get_LABEL, 2)
        functions["MAIN_LABEL"] = (self.get_MAIN_LABEL, 2)
        self.sc.run_script(path, functions)

    def get_PRODUCT_PART_NUMBER(self, agruments):
        self.PRODUCT_PART_NUMBER = agruments[0]

    def get_BOM_REV(self, agruments):
        self.BOM_REV = agruments[0]

    def get_DRAWING(self, agruments):
        self.DRAWING = agruments[0]

    def get_DRAWING_REV(self, agruments):
        self.DRAWING_REV = agruments[0]

    def get_BALLOON(self, agruments):
        self.BALLOONS[agruments[0]] = agruments[1]

    def get_LABEL(self, agruments):
        self.LABELS[agruments[0]] = agruments[1]
    
    def get_MAIN_LABEL(self, agruments):
        formatt = agruments[0]
        balLoon_number = agruments[1]
        self.MAIN_LABEL = [formatt, balLoon_number]
    
    def get_SERIAL_NUMBER_FORMAT(self, agruments):
        self.SERIAL_NUMBER_FORMAT = agruments[0]
main()