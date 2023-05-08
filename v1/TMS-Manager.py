# GENERAL INFORMATION
## This is the place where general information is written
## Every new line will be numbered as a new line
## The general information section describes the general pupose of the application
## This is how you add an image to your help file <br><img src='image.jpeg'>

# HOW TO USE
## Download the application
## Set all the settings according to PART V
## Run App_Name.exe file

from PersonalAssistant import *
from PersonalAssistant import FIELD
import os
import sqlite3

class main:
    def __init__(self):
        # set up Personal Assistant
        self.pa = PersonalAssistant(__file__, "TMS-Manager", "1.0")
        
        # connect to database
        self.db_location = self.pa.get_setting("Database location")
        self.con = sqlite3.connect(self.db_location)
        self.cur = self.con.cursor()

        # create database tables
        self.cur.execute("CREATE TABLE IF NOT EXISTS tms (part_number VARCHAR(50), size VARCHAR(50), color VARCHAR(50))")
        self.cur.execute("CREATE TABLE IF NOT EXISTS tms_inventory (box_number INT, part_number VARCHAR(50))")
        self.cur.execute("CREATE TABLE IF NOT EXISTS work_orders (work_order INT, product VARCHAR(50), first_sn VARCHAR(50), qty INT, pr VARCHAR(5))")
        self.con.commit()

        # MAIN MENU
        self.pa.main_menu["PRINT CABLE MARKINGS"] = self.print_new
        self.pa.main_menu["INVENTORY"] = self.inventory
        self.pa.display_menu()

        # run GUI
        self.pa.run()

    def print_new(self):
        ## PRINT CABLE MARKINGS
        
        error = False
        # get work order
        work_order = self.pa.input("Insert WORK ORDER") or 0
        
        # check if wo exists, add if not
        if work_order > 0:
            self.cur.execute("SELECT * FROM work_orders WHERE work_order = "+work_order)
            fetched_values = self.cur.fetchall()
            if len(fetched_values) == 0:
                self.pa.error("Work order dosen't exist")
                if self.pa.question("Add new work order?"):
                    # get product
                    product = self.pa.input("Insert PRODUCT PART NUMBER").upper() or "EMPTY"
                    self.cur.execute("SELECT * FROM products WHERE part_number = "+product)
                    fetched_values = self.cur.fetchall()
                    if len(fetched_values) == 0:
                        self.pa.error("Error! PRODUCT PART NUMBER is not in the database, please add it with Product Manager")
                        error = True
                    
                    if not error:
                        # make a new wo form
                        fields = {}
                        fields["work_order"] = FIELD("WORK ORDER", NUMBER, work_order)
                        fields["work_order"].disabled = True
                        fields["product"] = FIELD("PRODUCT PART NUMBER", TEXT, product)
                        fields["product"].disabled = True
                        fields["first_sn"] = FIELD("FIRST SERIAL NUMBER according to QMS", TEXT, "FLT0000-0000")
                        fields["qty"] = FIELD("WORK ORDER SIZE", NUMBER, 1)
                        fields["pr"] = FIELD("PR", TEXT, "00")

                        # submit new wo form
                        submit = self.pa.form(fields)
                        if submit:
                            self.cur.execute("INSERT INTO work_orders (work_order, product, first_sn, qty, pr) VALUES ("+submit["work_order"]+",'"+submit["product"]+"','"+submit["first_sn"]+"',"+submit["qty"]+",'"+submit["pr"]+"')")
                            self.con.commit()
                            self.pa.print("New WORK ORDER added")
                        else:
                            error = True
            if not error:
                self.cur.execute("SELECT * FROM work_orders WHERE work_order = "+work_order)
                fetched_values = self.cur.fetchall()
                if len(fetched_values) == 0:
                    # get values from database
                    data = fetched_values[0]
                    work_order = data[0]
                    product = data[1]

                    # check if tms script exist
                    tms_folder = self.tms_location+"/"+product
                    if not os.path.isdir(tms_folder):
                        os.makedirs(tms_folder)
                    script_location = tms_folder+"/script.txt"
                    if not os.path.isfile(script_location):
                        # create new script
                        self.pa.print("There is no script for this part number. Let's create it together")
                        
                        # make balloons
                        more = True
                        balloons = {}
                        balloons_options = []
                        self.pa.print("We will start from BALLOONS. Open the BOM and insert information accordingly")
                        while more:
                            balloon = self.pa.input("Insert BALLOON number") or "0"
                            tms_part_number = self.pa.input("What TMS part number is BALLOON #"+balloon+" ?")
                            self.cur.execute("SELECT * FROM tms WHERE part_number = "+tms_part_number)
                            fetched_values = self.cur.fetchall()
                            if len(fetched_values) == 0:
                                self.pa.error("This TMS is not in the database, Go to INVENTORY to add a new TMS part number")
                                error = True
                            if not error:
                                balloons[balloon] = tms_part_number
                                balloons_options.append(balloon)
                                more = self.pa.question("Is there another BALLOON?")
                            else:
                                more = False
                        
                        if not error:
                            # make labels
                            self.pa.print("Now lets make a list of CABLE MARKINGS")
                            tmss = {}
                            more = True
                            while more:
                                name = self.pa.input("Insert LABEL NAME [Or leave empty for MAIN LABEL]") or "MAIN LABEL"
                                balloon = self.pa.choose("Choose a BALLOON [Or leave empty for default value: "+balloons_options[0]+"]", balloons_options, balloons_options[0])
                                formatt = self.pa.input("Choose a LABEL FORMAT as a number between 1-12 [Or leave empty for default value: F00]") or "0"
                                try:
                                    formatt = int(formatt)
                                except:
                                    formatt = "0"
                                if not formatt in range(13):
                                    formatt = "0"
                                formatt = str(formatt)
                                formatt = "F"+formatt.zfill(2)
                                tmss[name] = (balloon, formatt)
                                more = self.pa.question("Is there another LABEL?")
                        
                        if not error:
                            # make script file
                            file = open(script_location, 'w')
                            file.write("BALLOONS\n")
                            for key, value in balloons.items():
                                file.write(key+":"+value+"\n")
                            file.write("LABELS\n")
                            for key, value in tmss.items():
                                file.write(key+":"+value[0]+":"+value[1]+"\n")
                            file.close()

                    # read script from existing file
                    file = open(script_location, 'r')
                    lines = file.readlines()
                    file.close()
                    collect = ""
                    balloons = {}
                    tmss = {}
                    for line in lines:
                        line = line.replace("\n", "")
                        if "BALLOONS" in line:
                            collect = "BALLOONS"
                        if "LABELS" in line:
                            collect = "LABELS"
                        if collect == "BALLOONS":
                            if ":" in line:
                                line = line.split(":")
                                if len(line) == 2:
                                    balloon = 
                                    tms_part_number = 
                                else:
                                    
                        if collect == "LABELS":
                            pass
            else:
                self.pa.error("Unexpected error")
        else:
            self.pa.error("Invalid WORK ORDER")
            error = True

        # Operation aborted 
        if error:
            self.pa.error("Operation aborted")
        
        # restart
        self.pa.restart()
    
    def inventory(self):
        ## INVENTORY
        pass

main()

# SCRIPT FUNCTIONS

# SETTINGS
# Database location --> The location of the user database. For example: database.db

# RELATED FILES
## users.csv - This is the file the app generates when clicking on EXPORT this file contains the following columns:
#- User Id
#- Name
#- Phone
#- Sex
#- Birth date
#- Photo