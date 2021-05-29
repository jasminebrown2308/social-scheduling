import mysql.connector
import hashlib, binascii, os
from datetime import date, datetime

#kivy imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Canvas, Color, Rectangle
from kivy.factory import Factory
from kivy.core.text.markup import *

Window.clearcolor = (1, 1, 1, 1) #sets background to white
Window.size = (300, 400) #size of window set to average phone size

#connect to MySQL database server
mydb = mysql.connector.connect(
    host="localhost",
    user="appuser",
    password="password",
    database="appdata"
)
cursor = mydb.cursor(buffered=True) #buffered=True prevents errors if the data is not read from the cursor

currentUsername = ""

class Event:
    def __init__(self):
        #initialises all attributes
        self.eventID = 0
        self.eventName = ""
        self.description = ""
        self.pollTitle = ""
        self.pollOptions = []
        self.locationName = ""
        self.locationDetails = ""
        self.tag1 = ""
        self.tag2 = ""
        self.tag3 = ""
        self.dtAdded = []
        self.invites = []
        self.link = False

    def autoFill(self):
        #sets attributes to the database record matching eventID attribute
        cursor.execute("SELECT eventName, description, locationName, locationDescription, tag1, tag2, tag3 FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            self.eventName = cursorRow[0]
            self.description = cursorRow[1]
            self.locationName = cursorRow[2]
            self.locationDetails = cursorRow[3]
            self.tag1 = cursorRow[4]
            self.tag2 = cursorRow[5]
            self.tag3 = cursorRow[6]

    def changeDetails(self):
        #used to modify database details by setting record values to values of current attributes
        cursor.execute("UPDATE tblevents SET eventName=%s WHERE eventID=%s", (self.eventName, self.eventID))
        cursor.execute("UPDATE tblevents SET description=%s WHERE eventID=%s", (self.description, self.eventID))
        cursor.execute("UPDATE tblevents SET locationName=%s WHERE eventID=%s", (self.locationName, self.eventID))
        cursor.execute("UPDATE tblevents SET locationDescription=%s WHERE eventID=%s", (self.locationDetails, self.eventID))
        cursor.execute("UPDATE tblevents SET tag1=%s WHERE eventID=%s", (self.tag1, self.eventID))
        cursor.execute("UPDATE tblevents SET tag2=%s WHERE eventID=%s", (self.tag2, self.eventID))
        cursor.execute("UPDATE tblevents SET tag3=%s WHERE eventID=%s", (self.tag3, self.eventID))

        mydb.commit()                      
               
    def addEvent(self):
        global currentUsername

        #add event
        if self.eventName != "" and self.dtAdded != [] and (self.invites != [] or self.link == True):
            if self.pollTitle != "":
                #creates poll first if applicable
                cursor.execute("INSERT INTO tblpolls "
                               "(title, chooseMany) "
                               "VALUES (%s, %s)", (self.pollTitle, 0))
                cursor.execute("SELECT LAST_INSERT_ID()") #finds pollID, which has been automatically generated
                for cursorRow in cursor:
                    pollID = cursorRow[0]

                optionNo = 1
                for option in self.pollOptions:
                    cursor.execute("INSERT INTO tblpolloptions "
                                   "(pollID, optionNo, optionText) "
                                   "VALUES (%s, %s, %s)", (pollID, optionNo, option))
                    optionNo += 1
               
                cursor.execute("INSERT INTO tblevents "
                               "(creator, eventName, description, locationName, locationDescription, tag1, tag2, tag3, pollID) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (currentUsername, self.eventName, self.description, self.locationName, self.locationDetails, self.tag1, self.tag2, self.tag3, pollID))
            else:
                cursor.execute("INSERT INTO tblevents "
                               "(creator, eventName, description, locationName, locationDescription, tag1, tag2, tag3) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (currentUsername, self.eventName, self.description, self.locationName, self.locationDetails, self.tag1, self.tag2, self.tag3))

            cursor.execute("SELECT LAST_INSERT_ID()") #finds eventID, which has been automatically generated
            for cursorRow in cursor:
                eventID = cursorRow[0]

            #add invites
            for invite in self.invites:
                cursor.execute("INSERT INTO tblinvitations "
                               "(eventID, invitee) "
                               "VALUES (%s, %s)", (eventID, invite))
            #add dateTimes
            for dt in self.dtAdded:
                date = dt[0]            
                for times in dt[1]:
                    startTime = None
                    endTime = None
                    if times != "all day":
                        startTime = times[0]
                        endTime = times[1]
                        cursor.execute("INSERT INTO tbldatetime "
                                       "(eventID, date, startTime, endTime) "
                                       "VALUES (%s, %s, %s, %s)", (eventID, date, startTime, endTime))
                    else:
                        cursor.execute("INSERT INTO tbldateTime "
                                       "(eventID, date) "
                                       "VALUES (%s, %s)", (eventID, date))
                    mydb.commit()
           
            self.__init__() #clear all the variables
            return eventID
        else:
            if self.eventName == "":
                Info1.message = "event name can't be blank"
                Factory.Info1().open()
            elif self.dtAdded == []:
                Info1.message = "you must add at least one date"
                Factory.Info1().open()
            else:
                Info1.message = "you must add invites (or generate link) to create the event"
                Factory.Info1().open()
            return -1 #means that event has not been created
       
currentEvent = Event()

#general functions
def dateToText(ddmmyyyy):
    dd, mm, yyyy = ddmmyyyy.split("/")
    dd = int(dd)
    mm = int(mm)
    yyyy = int(yyyy)

    day, month, year = dd, mm, yyyy #the d, m and y values will change but need to be accessed later
   
    #standard algorithm to work out which day of the month it is
    if mm == 1:
        mm = 13
        yyyy -= 1
    elif mm == 2:
        mm = 14
        yyyy -= 1
    calculation = dd + (2*mm) + ((3*(mm+1)/5) // 1) + yyyy + ((yyyy/4) // 1) - ((yyyy/100) // 1) + ((yyyy/400) // 1) + 2
    calcResult = int(calculation % 7)
    if calcResult == 0: #Saturday = column 5
        dayOfWeek = 5
    elif calcResult == 1:
        dayOfWeek = 6
    else:
        dayOfWeek = calcResult - 2

    days = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
    returnStr = days[dayOfWeek]

    #get correct superscript for date
    if day in (1, 21, 31):
        ss = "st"
    elif day in (2, 22):
        ss = "nd"
    elif day in (3, 23):
        ss = "rd"
    else:
        ss = "th"

    months = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
    returnStr = returnStr + " " + str(day) + ss + " " + str(months[int(month)-1]) + " " + str(year)
   
    return returnStr

#kivy classes
class Button(Button):
    pass
class Label(Label):
    pass
class Button1(Button):
    pass
class Button2(Button):
    pass
class Button3(Button):
    pass
class Button4(Button):
    pass
class Button1grey(Button):
    pass
class Button1red(Button):
    pass
class IconButton(Button):
    pass
class LabelCaps(Label):
    pass
class Label1(Label):
    pass
class IconLabel(Label):
    pass
class TextInput1(TextInput):
    pass
class TextInput2(TextInput):
    pass
class WindowManager(ScreenManager):
    pass

#screens
class LoadScreen(Screen): #this is all .kv code, no python necessary
    #The screen displayed when a user launches the app for the first time.
    #It will feature the app’s logo and have options to either sign in or create an account.
    pass

class SignIn(Screen):
    #Allows existing users to sign into accounts by retrieving their details from the MySQL database and checking that it matches.

    #references to .kv TextInput objects
    usernameemail = ObjectProperty(None)
    password = ObjectProperty(None)
   
    def signInButton(self):
        #called when 'sign in' button clicked to validate username and password
        global currentUsername
        pw = None
        cursor.execute("SELECT password FROM tblaccounts WHERE username=%s OR email=%s", (self.usernameemail.text, self.usernameemail.text))
        if cursor.rowcount == 0:
            Info1.message = "incorrect username or password"
            Factory.Info1().open()
            self.password.text = ""
        else:
            for cursorRow in cursor: #returns the list (should only contain one item) of passwords corresponding to email/username entered
                pw = cursorRow[0]
            if pw != None:
                #password hashing algorithm - hash the input then compare to saved password hash
                salt = pw[:64]
                pw = pw[64:]
                pwdhash = hashlib.pbkdf2_hmac('sha512',
                                              self.password.text.encode('utf-8'),
                                              salt.encode('ascii'),
                                              100000)
                pwdhash = binascii.hexlify(pwdhash).decode('ascii')
                if pw == pwdhash: #if login is correct
                    if "@" in self.usernameemail.text:
                        cursor.execute("SELECT username FROM tblaccounts WHERE email=%s OR email=%s", (self.usernameemail.text, self.usernameemail.text))
                        for usnmList in cursor:
                            for usnm in usnmList:
                                currentUsername = usnm
                    else:
                        currentUsername = self.usernameemail.text
                    self.parent.current = "viewcreated"
                else:
                    Info1.message = "incorrect username or password"
                    Factory.Info1().open()
                    self.password.text = ""

class CreateAccount(Screen):
    #New users can enter their details which are saved to the MySQL database.

    #references to .kv TextInput objects
    displayName = ObjectProperty(None)
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    passwordConf = ObjectProperty(None)
    email = ObjectProperty(None)

    def createAccountButton(self):
        #called when 'create account' button is clicked to validate then add user to database if valid
        validData = True
        if self.displayName.text=="" or self.username.text=="" or self.password.text=="" or self.email.text=="":
            Info1.message = "none of the fields can be left blank"
            Factory.Info1().open()
            validData = False
        elif "@" in self.username.text:
            #'@' can't be used in username as it is used to detect that it is an email
            Info1.message = "invalid character in username: '@'"
            Factory.Info1().open()
            validData = False
        elif ("@" not in self.email.text) or ("." not in self.email.text):
            #username must contain both '@' and '.' characters otherwise it is invalid
            Info1.message = "invalid email address entered"
            Factory.Info1().open()
            validData = False
        if validData == True:
            if self.password.text == self.passwordConf.text:
                #password hashing algorithm
                salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
                pwdhash = hashlib.pbkdf2_hmac('sha512', self.password.text.encode('utf-8'),
                                              salt, 100000)
                pwdhash = binascii.hexlify(pwdhash)
                pwdToStore = (salt + pwdhash).decode('ascii')
                cursor.execute("SELECT * FROM tblaccounts WHERE username=%s AND username=%s", (self.username.text, self.username.text))
                if cursor.rowcount == 0: #if username doesn't already exist
                    cursor.execute("SELECT * FROM tblaccounts WHERE email=%s AND email=%s", (self.email.text, self.email.text))
                    if cursor.rowcount == 0: #if email hasn't already been used
                        cursor.execute("INSERT INTO tblaccounts "
                                       "(username, email, displayName, password) "
                                       "VALUES (%s, %s, %s, %s)", (self.username.text, self.email.text, self.displayName.text, pwdToStore))
                        mydb.commit()
                        self.parent.current = "viewcreated"

                        global currentUsername
                        currentUsername = self.username.text

                        self.displayName.text = ""
                        self.username.text = ""
                        self.password.text = ""
                        self.passwordConf.text = ""
                        self.email.text = ""
                    else:
                        Info1.message = "email has already been used - try signing in"
                        Factory.Info1().open()
                else:
                    Info1.message = "username already exists - it must be unique"
                    Factory.Info1().open()
            else:
                Info1.message = "passwords do not match"
                Factory.Info1().open()
                self.password.text = ""
                self.passwordConf.text = ""

    def info(self):
        #called when they click on one of the info icons
        message = "'name' is your display name, which you can change later. 'username' is permanent and must be unique."
        Info1.message = message
        Factory.Info1().open()

class ViewCreated(Screen):
    #Users can see a list of all the events that have created and view updates.
    def on_enter(self): #function is automatically called to initialise the screen
        try: #clear any existing widgets
            self.box.clear_widgets()
        except:
            pass

        global currentUsername

        #self.box is the main container for the other Kivy elements
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.025),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height")) #allows box to scroll vertically

        newRel = RelativeLayout(size_hint=(1, None),
                                height=self.height*0.08)
        newLbl = Label(text="NEW UPDATES",
                       color=(0.5, 0.5, 0.5, 1),
                       height=self.height*0.08,
                       size_hint=(1, 1),
                       font_size=self.height*0.04)
        newRel.add_widget(newLbl)
        with newRel.canvas.before: #adds separator lines
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (newLbl.pos[1]+(newRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.42), newRel.height),
                      pos=((self.size[0]*0.25), (newLbl.pos[1])))

        currentRel = RelativeLayout(size_hint=(1, None),
                                   height=self.height*0.08)
        currentLbl = Label(text="CURRENT EVENTS",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        currentRel.add_widget(currentLbl)
        with currentRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (currentLbl.pos[1]+(currentRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.50), currentRel.height),
                      pos=((self.size[0]*0.21), (currentLbl.pos[1])))

        pastRel = RelativeLayout(size_hint=(1, None),
                                 height=self.height*0.08)
        pastLbl = Label(text="PAST EVENTS",
                        color=(0.5, 0.5, 0.5, 1),
                        height=self.height*0.08,
                        size_hint=(1, 1),
                        font_size=self.height*0.04)
        pastRel.add_widget(pastLbl)
        with pastRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (pastLbl.pos[1]+(pastRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.40), pastRel.height),
                      pos=((self.size[0]*0.26), (pastLbl.pos[1])))

        sv = ScrollView(size_hint=(1, 0.675),
                        pos_hint={"x": 0, "top": 0.87})
        sv.add_widget(self.box)
        self.add_widget(sv)

        listEmpty = True

        cursor.execute("SELECT eventID, eventName FROM tblevents WHERE creator=%s OR creator=%s", (currentUsername, currentUsername))
        events = []

        if cursor.rowcount == 0: #if there are no events created by currentUsername
            emptyLbl = Label(color=(0.5, 0.5, 0.5, 1),
                             text="there are no created\nevents to display",
                             halign="center",
                             size_hint=(1, None),
                             font_size=self.height*0.045,
                             height=self.height*0.2,
                             text_size=(self.size[0]*0.92, self.height*0.1),
                             valign="middle")
            self.box.add_widget(emptyLbl)
        else:
            for cursorRow in cursor:
                events.append(cursorRow)

            new = []
            current = []
            past = []
            currentEvents = []

            #determine whether event is in the past
            #if the date hasn't been confirmed yet then as long as not all the dates are in the past it is considered a current event
            for event in events:
                cursor.execute("SELECT date FROM tbldatetime WHERE eventID=%s OR eventID=%s", (event[0], event[0]))
                numDates = cursor.rowcount
                pastCount = 0
                currentDate = datetime.now().strftime("%Y/%m/%d")
                for cursorRow in cursor:
                    #cursorRow[0] is in dd/mm/yyyy format but needs to be yyyy/mm/dd to compare
                    eventDate = cursorRow[0][6:] + "/" + cursorRow[0][3:-5] + "/" + cursorRow[0][:2]
                    if eventDate < currentDate: #if date of event is before current date
                        pastCount += 1
                if numDates == pastCount:
                    past.append(event)
                else:
                    currentEvents.append(event)

            #determine whether current events have new updates
            for event in currentEvents:
                cursor.execute("SELECT updateCode FROM tbleventupdates WHERE eventID=%s AND viewed=%s AND updateCode<4", (event[0], 0))
                if cursor.rowcount != 0: #if there are unseen updates for the event
                    new.append(event)
                else: #if there are no new updates
                    current.append(event)

            if len(new) != 0:
                self.box.add_widget(newRel)
                for n in reversed(new): #reversed so they are displayed with newest updates first
                    self.addEvent(n[0], n[1], "n")

            if len(current) != 0:
                self.box.add_widget(currentRel)
                for c in reversed(current):
                    self.addEvent(c[0], c[1], "c")

            if len(past) != 0:
                self.box.add_widget(pastRel)
                for p in reversed(past):
                    self.addEvent(p[0], p[1], "p")

    def addEvent(self, eventID, eventName, ncp):
        updateCodes = ("invitation declined", "availability entered", "availability changed", "changed poll vote")
        cursor.execute("SELECT updateCode FROM tbleventupdates WHERE eventID=%s AND updateCode<%s AND viewed=0", (eventID, 4))
        numUpdates = cursor.rowcount
        updates = []
        for cursorRow in cursor:
            updates.append(cursorRow[0])

        numRemaining = None
        code = None
        cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND (viewed=%s OR viewed=%s)", (eventID, 0, 1))
        numRemaining = cursor.rowcount
        if numRemaining == 0:
            updateTxt = "everyone has responded"
        elif numUpdates == 1:
            for u in updates:
                code = u
            updateTxt = updateCodes[code]
        elif numUpdates == 0:
            updateTxt = str(numRemaining) + " left to respond"
        else: #user will need to click view to see the updates as they can't all be displayed
            updateTxt = str(numUpdates) + " new updates"
           
        invRow = BoxLayout(orientation="horizontal",
                           padding=0,
                           spacing=self.size[0]*0.01,
                           height=self.height*0.1,
                           size_hint=(1, None))
       
        nameBox = BoxLayout(orientation="vertical",
                            spacing=0,
                            size_hint=(0.55, None),
                            height=self.height*0.1)
        eventNameLbl = Label(text=eventName,
                             halign="left",
                             color=(0, 0, 0, 1),
                             font_size=(self.height*0.04),
                             size_hint=(None, 0.67))
        eventNameLbl.bind(texture_size=eventNameLbl.setter('size')) #needed to align to the left

        colour = (0.50, 0.50, 0.50, 1)
        if code == 0: #red if invitation has been declined
            colour = (1, 0.36, 0.41, 1)
        if numRemaining == 0: #green if everyone has responded
            colour = (0.46, 0.74, 0.65, 1)

        updateLbl = Label(text=updateTxt,
                          halign="left",
                          color=colour,
                          font_size=(self.height*0.034),
                          size_hint=(None, 0.33))
        updateLbl.bind(texture_size=updateLbl.setter('size'))
       
        nameBox.add_widget(eventNameLbl)
        nameBox.add_widget(updateLbl)

        if ncp=="n":
            viewBtn = Button1(text="view")
        else:
            viewBtn = Button1grey(text="view")

        viewBtn.size_hint = (0.19, None)
        viewBtn.on_release = lambda *args: self.viewEvent(eventID, *args)

        if ncp!="p":
            modBtn = Button1grey(text="modify",
                                 size_hint=(0.24, None))
            modBtn.on_release = lambda *args: self.modifyEvent(eventID, *args)
        else: #displays option to delete past events rather than modify them
            modBtn = Button1red(text="delete",
                                size_hint=(0.24, None))
            modBtn.on_release = lambda *args: self.deleteEvent(eventID, *args)


        for btn in (viewBtn, modBtn):
            btn.height = (self.height*0.08)
            btn.font_size = (self.height*0.035)

        for obj in (nameBox, viewBtn, modBtn):
            invRow.add_widget(obj)

        self.box.add_widget(invRow)

    def viewEvent(self, eventID):
        ViewCreatedDetails.eventID = eventID
        self.manager.current = "viewcreateddetails"
       
    def modifyEvent(self, eventID):
        ModifyEvent.eventID = eventID
        Factory.ModifyEvent().open()

    def deleteEvent(self, eventID):
        #Removes event and all references to it from the database.
        #deletions need to ensure referential integrity so need to delete all records that do not act as foreign keys first
       
        #delete from tblEventUpdates
        cursor.execute("DELETE FROM tbleventupdates WHERE eventID=%s AND eventID=%s", (eventID, eventID))

        #delete from tblAvailability - first need to find corresponding dateTimeIDs
        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND eventID=%s", (eventID, eventID))
        datetimes = []
        for cursorRow in cursor:
            datetimes.append(cursorRow[0])
        for dt in datetimes:
            cursor.execute("DELETE FROM tblavailability WHERE dateTimeID=%s OR dateTimeID=%s", (dt, dt))

        #can now delete from tblDateTime (as tblAvailability has been deleted)
        cursor.execute("DELETE FROM tbldatetime WHERE eventID=%s AND eventID=%s", (eventID, eventID))

        #delete poll options and votes - first need to find corresponding pollID
        cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (eventID, eventID))
        for cursorRow in cursor:
            pollID = cursorRow[0]
        if pollID != None:
            cursor.execute("DELETE FROM tblpolloptions WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            cursor.execute("DELETE FROM tblpollvotes WHERE pollID=%s AND pollID=%s", (pollID, pollID))

        #can now delete from tblInvitations (as tblPollVotes and tblAvailability have been deleted)
        cursor.execute("DELETE FROM tblinvitations WHERE eventID=%s AND eventID=%s", (eventID, eventID))

        #can now delete from tblEvents (as tblDateTime, tblInvitations and tblEventUpdates have been deleted)
        cursor.execute("DELETE FROM tblevents WHERE eventID=%s AND eventID=%s", (eventID, eventID))

        #finally delete from tblPolls (as tblEvents, tblPollOptions and tblPollVotes have been deleted)
        if pollID != None:
            cursor.execute("DELETE FROM tblpolls WHERE pollID=%s AND pollID=%s", (pollID, pollID))

        mydb.commit()
        self.on_enter() #refreshes so event will be removed from the screen

        Info1.message = "event deleted"
        Factory.Info1().open()
                                     
class ViewCreatedDetails(Screen):
    #Displays details of a selected created event with options to change details, view poll results, manage invitations and view updates.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.8),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)
       
        cursor.execute("SELECT eventName, creator, description, locationName, locationDescription, tag1, tag2, tag3, pollID FROM tblevents WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))

        for cursorRow in cursor:
            eventName = cursorRow[0]
            creator = cursorRow[1]
            description = cursorRow[2]
            locationName = cursorRow[3]
            locationDescription = cursorRow[4]
            tag1 = cursorRow[5]
            tag2 = cursorRow[6]
            tag3 = cursorRow[7]
            pollID = cursorRow[8]

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)                        

        nameLbl = Label(text=eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)
        descBox=TextInput2(text=description,
                               disabled=True,
                               size_hint=(1, None),
                               height=self.height*0.14)

        tags = False #determines whether or not to display the tagRow when widgets are added
        if tag1 != "" or tag2 != "" or tag3 != "": #if tags have been added for the event
            tags = True
            tagRow = GridLayout(rows=1,
                                cols=3,
                                col_default_width=self.size[0]*0.33,
                                col_force_default=True,
                                size_hint=(1, None),
                                height=self.height*0.04,
                                spacing=self.size[0]*0.02)
            tag1Lbl = Label(text=tag1)
            tag2Lbl = Label(text=tag2)
            tag3Lbl = Label(text=tag3)
            for tagLbl in (tag1Lbl, tag2Lbl, tag3Lbl):
                tagLbl.color = (0.50, 0.76, 0.86, 1)
                tagLbl.size_hint=(None, 1)
                tagLbl.font_size=self.height*0.03
                tagLbl.halign="left"
                tagLbl.bind(texture_size=tagLbl.setter('size'))
                tagRow.add_widget(tagLbl)

        locationFloat = FloatLayout(size_hint=(1, None),
                                    height=self.height*0.06)
        locationLbl = Label(text=("Location: " + locationName),
                            color=(0.5, 0.5, 0.5, 1),
                            font_size=(self.height*0.035),
                            text_size=(self.size[0]*0.92, self.height*0.06),
                            valign="bottom",
                            halign="left",
                            size_hint=(1, 1),
                            pos_hint={"x": 0, "top": 1},
                            height=self.height*0.06)
        locationBtn = IconButton(size_hint=(1, 1),
                                 pos_hint={"x": 0, "top": 1},
                                 on_release=lambda *args: self.viewDesc(locationDescription, *args))
        locationFloat.add_widget(locationBtn)
        locationFloat.add_widget(locationLbl)

        descBtn = Button1grey(text="view location details",
                              size_hint=(0.6, None),
                              height=self.height*0.08,
                              font_size=self.height*0.05,
                              on_release=lambda *args: self.viewDesc(locationDescription, *args))

        changeBtn = Button1grey(text="change event details",
                                size_hint=(1, None),
                                height=self.height*0.08,
                                font_size=self.height*0.06,
                                on_release=self.modifyEvent)

        #inviteeRow shows the number of people left to respond and a button so they can add or remove invites
        numRemaining = None
        cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND (viewed=%s OR viewed=%s)", (self.eventID, 0, 1))
        numRemaining = cursor.rowcount
        if numRemaining == 0:
            updateTxt = "everyone has responded"
        else:
            updateTxt = str(numRemaining) + " left to respond"

        inviteeRow = BoxLayout(orientation="horizontal",
                               spacing=0,
                               padding=[0, self.height*0.01],
                               size_hint=(1, None),
                               height=self.height*0.08)
        inviteeLbl = Label(text=updateTxt,
                           color=(0.50, 0.77, 0.89, 1),
                           font_size=self.height*0.03,
                           size_hint=(0.53, 1))
        inviteeBtn = Button1(text="manage invites",
                             size_hint=(0.43, 1),
                             on_release=self.manageInvites)
        inviteeRow.add_widget(inviteeLbl)
        inviteeRow.add_widget(inviteeBtn)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)
        if description != "":
            self.box.add_widget(descBox)
        if tags == True:
            self.box.add_widget(tagRow)
        if locationName != "":
            self.box.add_widget(locationFloat)
        if locationDescription != "":
            self.box.add_widget(descBtn)
        self.box.add_widget(changeBtn)
        self.box.add_widget(inviteeRow)

        #display poll
        cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            pollID = cursorRow[0]
        if pollID != None:
            cursor.execute("SELECT title FROM tblpolls WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            for cursorRow in cursor:
                pollTitle = cursorRow[0]
            pollRow = GridLayout(rows=1,
                                 cols=2,
                                 row_default_height=self.height*0.08,
                                 row_force_default=True,
                                 col_force_default=True,
                                 size_hint=(1, None),
                                 padding=[self.size[0]*0.08, 0, 0, 0],
                                 height=self.height*0.08,
                                 spacing=self.size[0]*0.1)
            pollLbl1 = Label(text="POLL:",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=self.height*0.04,
                             size_hint=(0.2, 1))
            pollLbl2 = Label(text=pollTitle,
                             halign="left",
                             color=(0, 0, 0, 1),
                             size_hint=(None, 1),
                             font_size=self.height*0.035)
            pollLbl2.bind(texture_size=pollLbl2.setter('size'))
           
            pollRow.add_widget(pollLbl1)
            pollRow.add_widget(pollLbl2)
            self.box.add_widget(pollRow)

            cursor.execute("SELECT optionNo, optionText FROM tblpolloptions WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            optionTexts = {}
            for cursorRow in cursor:
                optionTexts[cursorRow[0]] = cursorRow[1]

            #counting votes
            votes = {}
            numVotes = 0
            for optionNo in optionTexts:
                votes[optionNo] = 0
            cursor.execute("SELECT optionNo FROM tblpollvotes WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            for cursorRow in cursor:
                votes[cursorRow[0]] += 1
                numVotes += 1
            if numVotes != 0:
                for optionNo in optionTexts:
                    percent = int((votes[optionNo] / numVotes * 100))
                    if percent == 0:
                        barwidth = 0.001
                    else:
                        barwidth = percent / 100
                    optionRow = GridLayout(rows=1,
                                           cols=2,
                                           cols_minimum={0: self.size[0]*0.75*barwidth, 1: self.size[0]*0.75*(1-barwidth)},
                                           row_default_height=self.height*0.06,
                                           row_force_default=True,
                                           col_force_default=True,
                                           size_hint=(1, None),
                                           spacing=self.size[0]*0.03,
                                           height=self.height*0.06,
                                           padding=0)
                    optionBar = Button3(size_hint=(1, 1))

                    votesTxt = Label(text=str(votes[optionNo]) + " (" + str(percent) + "%)",
                                     color=(0.5, 0.5, 0.5, 1),
                                     size_hint=(None, 1),
                                     font_size=self.height*0.03,
                                     halign="left")
                    votesTxt.bind(texture_size=votesTxt.setter('size'))

                    optionTxt = Label(text=optionTexts[optionNo],
                                      color=(0, 0, 0, 1),
                                      halign="left",
                                      valign="top",
                                      text_size=(self.size[0]*0.92, self.height*0.06),
                                      size_hint=(None, None),
                                      height=self.height*0.06,
                                      font_size=self.height*0.035)
                    optionTxt.bind(texture_size=optionTxt.setter('size'))

                    optionRow.add_widget(optionBar)
                    optionRow.add_widget(votesTxt)
                    self.box.add_widget(optionRow)
                    self.box.add_widget(optionTxt)
            else:
                noVotesTxt = Label(text="no votes yet",
                                   color=(0.5, 0.5, 0.5, 1),
                                   halign="center",
                                   valign="top",
                                   text_size=(self.size[0]*0.92, self.height*0.08),
                                   font_size=self.height*0.035,
                                   height=self.height*0.08)
                noVotesTxt.bind(texture_size=noVotesTxt.setter('size'))
                self.box.add_widget(noVotesTxt)

        #display dates
        cursor.execute("SELECT updateCode FROM tbleventupdates WHERE eventID=%s AND updateCode=%s", (self.eventID, 5))
        if cursor.rowcount == 0: #date unconfirmed
            confirmed = False
            datesRel = RelativeLayout(size_hint=(1, None),
                                      height=self.height*0.08)
            datesLbl = Label(text="DATES",
                             color=(0.5, 0.5, 0.5, 1),
                             height=self.height*0.08,
                             size_hint=(1, 1),
                             font_size=self.height*0.04)
            datesRel.add_widget(datesLbl)
            with datesRel.canvas.before:
                Color(0.50, 0.76, 0.86, 1)
                Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                          pos=(0, (datesLbl.pos[1]+(datesRel.height/2))))
                Color(1, 1, 1, 1)
                Rectangle(size=((self.size[0]*0.20), datesRel.height),
                          pos=((self.size[0]*0.36), (datesLbl.pos[1])))
        else:
            confirmed = True
            datesRel = RelativeLayout(size_hint=(1, None),
                                      height=self.height*0.08)
            datesLbl = Label(text="DATE CONFIRMED",
                             color=(0.5, 0.5, 0.5, 1),
                             height=self.height*0.08,
                             size_hint=(1, 1),
                             font_size=self.height*0.04)
            datesRel.add_widget(datesLbl)
            with datesRel.canvas.before:
                Color(0.50, 0.76, 0.86, 1)
                Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                          pos=(0, (datesLbl.pos[1]+(datesRel.height/2))))
                Color(1, 1, 1, 1)
                Rectangle(size=((self.size[0]*0.48), datesRel.height),
                          pos=((self.size[0]*0.22), (datesLbl.pos[1])))

        self.box.add_widget(datesRel)

        cursor.execute("SELECT date, startTime, endTime FROM tbldatetime WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))
        dates = []
        dateTimes = []
        for cursorRow in cursor:
            date = cursorRow[0]
            time1 = cursorRow[1]
            time2 = cursorRow[2]
            if time1 == None:
                times = "all day"
            else:
                times = time1 + "-" + time2

            if date not in dates:
                dates.append(date)
                dateTimes.append([date, [times]])
            else:
                for dt in dateTimes:
                    if date == dt[0]:
                        dt[1].append(times)

        for dt in dateTimes:
            dtBox = BoxLayout(orientation="vertical",
                              spacing=0,
                              size_hint=(0.55, None),
                              height=self.height*0.1)
            dateLbl = Label(text=dateToText(dt[0]),
                            halign="left",
                            color=(0, 0, 0, 1),
                            font_size=(self.height*0.04),
                            size_hint=(None, 0.67))
            dateLbl.bind(texture_size=dateLbl.setter('size')) #needed to align to the left

            timesText = "" #concatenates into a string listing all the times for a given date
            for time in dt[1]:
                timesText = timesText + time + ", "

            timesText = timesText[:-2] #cuts off the last ", " characters

            timesLbl = Label(text=timesText,
                             halign="left",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=(self.height*0.03),
                             size_hint=(None, 0.33))
            timesLbl.bind(texture_size=timesLbl.setter('size'))

            dtBox.add_widget(dateLbl)
            dtBox.add_widget(timesLbl)

            self.box.add_widget(dtBox)

        #display new updates
        updatesRel = RelativeLayout(size_hint=(1, None),
                                    height=self.height*0.08)
        updatesLbl = Label(text="NEW UPDATES",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        updatesRel.add_widget(updatesLbl)
        with updatesRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (updatesLbl.pos[1]+(updatesRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.40), updatesRel.height),
                      pos=((self.size[0]*0.26), (updatesLbl.pos[1])))
           
        updateCodes = ("declined invitation", "entered availability", "changed availability", "changed poll vote")
        cursor.execute("SELECT updateCode, invitee FROM tbleventupdates WHERE eventID=%s AND viewed=%s AND updateCode<4", (self.eventID, 0))
        updates = []
        for cursorRow in cursor:
            updates.append(cursorRow)

        if len(updates) != 0:
            self.box.add_widget(updatesRel)

        for u in reversed(updates): #shows newest updates first
            cursor.execute("SELECT displayName FROM tblaccounts WHERE username=%s AND username=%s", (u[1], u[1]))
            for cursorRow in cursor:
                username = cursorRow[0]

            updateTxt = Label(text="[color=#7fc1db]" + username + "[/color] [color=#7f7f7f]" + updateCodes[u[0]] + "[/color]",
                              halign="left",
                              markup=True,
                              height=self.height*0.07,
                              size_hint=(None, None),
                              font_size=self.height*0.04)
            updateTxt.bind(texture_size=updateTxt.setter('size'))
            self.box.add_widget(updateTxt)

        #set updates to viewed
        cursor.execute("UPDATE tbleventupdates SET viewed=1 WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        mydb.commit()

        viewBtn = Button1(text="view availability and confirm date",
                          font_size=self.height*0.06,
                          size_hint=(1, None),
                          height=self.height*0.083,
                          on_release=lambda *args: self.viewConf(eventName, *args))
       
        deleteBtn = Button2(text="delete event",
                            color=(1, 0.36, 0.41, 1),
                            size_hint=(1, None),
                            height=self.height*0.072,
                            on_release=self.deleteEvent)

        if confirmed == False:
            self.box.add_widget(viewBtn)
        self.box.add_widget(deleteBtn)

    def viewDesc(self, description, btn):
        if description != "":
            Info1.message = description
            Factory.Info1().open()

    def modifyEvent(self, btn):
        ModifyEvent.eventID = self.eventID
        Factory.ModifyEvent().open()

    def manageInvites(self, btn):
        ManageInvites.eventID = self.eventID
        Factory.ManageInvites().open()

    def viewConf(self, name, btn):
        ViewCreatedDates.eventID=self.eventID
        ViewCreatedDates.eventName=name
        self.manager.current="viewcreateddates"

    def deleteEvent(self, btn):
        cursor.execute("DELETE FROM tbleventupdates WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        datetimes = []
        for cursorRow in cursor:
            datetimes.append(cursorRow[0])
        for dt in datetimes:
            cursor.execute("DELETE FROM tblavailability WHERE dateTimeID=%s OR dateTimeID=%s", (dt, dt))
        cursor.execute("DELETE FROM tbldatetime WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            pollID = cursorRow[0]
        if pollID != None:
            cursor.execute("DELETE FROM tblpolloptions WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            cursor.execute("DELETE FROM tblpollvotes WHERE pollID=%s AND pollID=%s", (pollID, pollID))
        cursor.execute("DELETE FROM tblinvitations WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        cursor.execute("DELETE FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        if pollID != None:
            cursor.execute("DELETE FROM tblpolls WHERE pollID=%s AND pollID=%s", (pollID, pollID))

        mydb.commit()

        self.manager.current="viewcreated"
        Info1.message = "event deleted"
        Factory.Info1().open()
       
    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="viewcreated"
        self.manager.transition.duration = 0

class ViewCreatedDates(Screen):
    #Ranks the available date-time combinations for the selected created event based on invitee availability.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.8),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)
       
        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)                        

        nameLbl = Label(text=self.eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        suggestRel = RelativeLayout(size_hint=(1, None),
                                    height=self.height*0.08)
        suggestLbl = Label(text="TOP SUGGESTIONS",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        suggestRel.add_widget(suggestLbl)
        with suggestRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (suggestLbl.pos[1]+(suggestRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.50), suggestRel.height),
                      pos=((self.size[0]*0.21), (suggestLbl.pos[1])))

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        cursor.execute("SELECT date, startTime, endTime, dateTimeID FROM tbldatetime WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))
        dates = []
        dateTimes = []
        for cursorRow in cursor:
            date = cursorRow[0]
            time1 = cursorRow[1]
            time2 = cursorRow[2]
            dtID = cursorRow[3]
            if time1 == None:
                times = "all day"
            else:
                times = time1 + "-" + time2
            dateTimes.append([dtID, date, times, 0, 0, 0]) #the 0s are for the rank, number confirmed and number unavailable respectively

        for dt in dateTimes:
            cursor.execute("SELECT availability FROM tblavailability WHERE dateTimeID=%s AND dateTimeID=%s", (dt[0], dt[0]))
            numResponded = 0
            for cursorRow in cursor:
                if cursorRow[0] == "Y":
                    dt[3] += 1
                    dt[4] += 1
                elif cursorRow[0] == "N":
                    dt[3] -= 1
                    dt[5] += 1
                numResponded += 1

        #sort dates into ascending order by rank (element 3 of tuple)
        dateTimes.sort(key=lambda tup: tup[3])

        dtSorted = []
        maxScore=numResponded*-1 #this is the minimum rank an event can have (if everyone has said no)
        mostConfirmed = 0 #this is the minimum so any higher score will be the new 'mostConfirmed'
        leastUnavailable = numResponded #this is the maximum so any lower score will be the new 'leastUnavailable'
        for dt in reversed(dateTimes):
            dtSorted.append(dt)
            if dt[3] > maxScore:
                maxScore = dt[3]
            if dt[4] > mostConfirmed:
                mostConfirmed = dt[4]
            if dt[5] < leastUnavailable:
                leastUnavailable = dt[5]

        everyone = []
        topChoice = []
        mostConf = []
        leastUnav = []
        otherDates = []

        if numResponded == 0:
            noRespLbl = Label(color=(0.5, 0.5, 0.5, 1),
                              text="nobody has responded yet",
                              halign="center",
                              size_hint=(1, None),
                              font_size=self.height*0.045,
                              height=self.height*0.2,
                              text_size=(self.size[0]*0.92, self.height*0.1),
                              valign="middle")
            self.box.add_widget(noRespLbl)
        else:
            self.box.add_widget(suggestRel)
            for dt in dtSorted:
                if dt[3] == maxScore: #selects the event with the highest rank (top choice/everyone can attend)
                    if dt[4] == mostConfirmed:
                        mostConfirmed += 1 #means that the mostConfirmed event(s) will not be displayed as this is worse than the top choice
                    if dt[5] == leastUnavailable:
                        leastUnavailable -= 1 #means that the leastUnavailable event(s) will not be displayed as this is worse than the top choice

                    #append to relevant array
                    if maxScore == numResponded:
                        everyone.append((dt[1], dt[2], dt[4], dt[5], dt[0])) #fields are date, time, number of yeses, number of nos and dateTimeID
                    else:
                        topChoice.append((dt[1], dt[2], dt[4], dt[5], dt[0]))
                elif dt[4] == mostConfirmed:
                    mostConf.append((dt[1], dt[2], dt[4], dt[5], dt[0]))
                elif dt[5] == leastUnavailable:
                    leastUnav.append((dt[1], dt[2], dt[4], dt[5], dt[0]))
                else:
                    otherDates.append((dt[1], dt[2], dt[4], dt[5], dt[0]))

            #display events
            for event in everyone:
                self.displayDateTime(event[4], event[0], event[1], event[2], event[3], "everyone")
            for event in topChoice:
                self.displayDateTime(event[4], event[0], event[1], event[2], event[3], "top")
            for event in mostConf:
                self.displayDateTime(event[4], event[0], event[1], event[2], event[3], "most")
            for event in leastUnav:
                self.displayDateTime(event[4], event[0], event[1], event[2], event[3], "least")

            allRel = RelativeLayout(size_hint=(1, None),
                                    height=self.height*0.08)
            allLbl = Label(text="ALL DATES",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
            allRel.add_widget(allLbl)
            with allRel.canvas.before:
                Color(0.50, 0.76, 0.86, 1)
                Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                          pos=(0, (allLbl.pos[1]+(allRel.height/2))))
                Color(1, 1, 1, 1)
                Rectangle(size=((self.size[0]*0.40), allRel.height),
                          pos=((self.size[0]*0.26), (allLbl.pos[1])))

            if len(otherDates) != 0:
                self.box.add_widget(allRel)

            for event in otherDates:
                self.displayDateTime(event[4], event[0], event[1], event[2], event[3], None)

    def displayDateTime(self, dtID, date, time, numYes, numNo, suggest):
        #uses parameters to display the date/time option alongside the availability of everyone that has responded
        dtRow = BoxLayout(orientation="horizontal",
                          spacing=0,
                          size_hint=(1, None),
                          height=self.height*0.1)
        dtBox = BoxLayout(orientation="vertical",
                          spacing=0,
                          size_hint=(0.5, 1))
        dateLbl = Label(text=dateToText(date),
                        halign="left",
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.035),
                        size_hint=(None, 0.67))
        dateLbl.bind(texture_size=dateLbl.setter('size')) #needed to align to the left

        timesLbl = Label(text=time,
                         halign="left",
                         color=(0.5, 0.5, 0.5, 1),
                         font_size=(self.height*0.03),
                         size_hint=(None, 0.33))
        timesLbl.bind(texture_size=timesLbl.setter('size'))

        tickImg = Image(source="images/yes.png",
                        size_hint=(0.06, 1))
        tickTxt = Label(text=str(numYes),
                        color=(0.46, 0.74, 0.65, 1),
                        size_hint=(0.07, 1),
                        font_size=self.height*0.035)

        crossImg = Image(source="images/no.png",
                         size_hint=(0.06, 1))
        crossTxt = Label(text=str(numNo),
                         color=(1, 0.36, 0.41, 1),
                         size_hint=(0.07, 1),
                         font_size=self.height*0.035)
        space = Widget(size_hint=(0.04, 1))
       
        viewBtn = Button1(text="view",
                          size_hint=(0.2, 1),
                          font_size=self.height*0.03,
                          on_release=lambda *args: self.view(dtID, *args))

        dtBox.add_widget(dateLbl)
        dtBox.add_widget(timesLbl)

        for obj in (dtBox, tickImg, tickTxt, crossImg, crossTxt, space, viewBtn):
            dtRow.add_widget(obj)
     
        self.box.add_widget(dtRow)
       
        if suggest != None:
            suggestFloat = FloatLayout(size_hint=(1, None),
                                       height=self.height*0.06)
            icon = Image(size_hint=(0.1, 1),
                         pos_hint={"x": 0, "top": 1})
            suggestText = Label(color=(0.46, 0.74, 0.65, 1),
                                halign="left",
                                size_hint=(None, 1),
                                font_size=self.height*0.035,
                                pos_hint={"x": 0.15, "top": 1})
            suggestText.bind(texture_size=suggestText.setter('size'))

            if suggest == "everyone":
                icon.source="images/top1.png"
                suggestText.text = "everyone can attend"
            if suggest == "top":
                icon.source="images/top1.png"
                suggestText.text = "top choice"
            if suggest == "most":
                icon.source = "images/top2.png"
                suggestText.text = "most confirmed"
            if suggest == "least":
                icon.source = "images/top3.png"
                suggestText.text = "least unavailable"

            suggestFloat.add_widget(icon)
            suggestFloat.add_widget(suggestText)
            self.box.add_widget(suggestFloat)

    def view(self, dtID, btn):
        ViewCreatedAvailability.eventID = self.eventID
        ViewCreatedAvailability.eventName = self.eventName
        ViewCreatedAvailability.dtID = dtID
        self.manager.current="viewcreatedavailability"

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="viewcreateddetails"
        self.manager.transition.duration = 0

class ViewCreatedAvailability(Screen):
    #Ranks the available date-time combinations for the selected created event based on invitee availability.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        cursor.execute("SELECT date, startTime, endTime FROM tbldatetime WHERE dateTimeID=%s AND dateTimeID=%s", (self.dtID, self.dtID))
        for cursorRow in cursor:
            date = cursorRow[0]
            time1 = cursorRow[1]
            time2 = cursorRow[2]

        if time1 == None:
            time = "all day"
        else:
            time = time1 + "-" + time2
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.66),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)

        nameLbl = Label(text=dateToText(date) + " (" + time + ")",
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.045),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        cursor.execute("SELECT invitationID, availability FROM tblavailability WHERE dateTimeID=%s AND dateTimeID=%s", (self.dtID, self.dtID))
        invIDs = []
        for cursorRow in cursor:
            invIDs.append(cursorRow)

        invites = []
        for invite in invIDs:
            cursor.execute("SELECT invitee FROM tblinvitations WHERE invitationID=%s AND eventID=%s", (invite[0], self.eventID))
            for cursorRow in cursor:
                invites.append((cursorRow[0], invite[1]))
       
        for invite in invites:
            self.addInvitee(invite[0], invite[1])

        otherBtn = Button1grey(text="< other dates",
                               font_size=self.height*0.045,
                               size_hint=(0.38, 0.083),
                               pos_hint={"x": 0.04, "top": 0.31},
                               on_release=self.back)

        selectBtn = Button1(text="select and confirm",
                            font_size=self.height*0.045,
                            size_hint=(0.50, 0.083),
                            pos_hint={"x": 0.46, "top": 0.31},
                            on_release=self.confirm)
        self.add_widget(otherBtn)
        self.add_widget(selectBtn)

    def addInvitee(self, invitee, availability):
        cursor.execute("SELECT displayName FROM tblaccounts WHERE username=%s AND username=%s", (invitee, invitee))
        for cursorRow in cursor:
            name = cursorRow[0]

        nameRow = FloatLayout(size_hint=(1, None),
                              height=self.height*0.05)
                           
        nameLbl = Label(text=name,
                        color=(0, 0, 0, 1),
                        size_hint=(None, 1),
                        halign="left",
                        pos_hint={"x": 0, "top": 1},
                        font_size=self.height*0.036)
        nameLbl.bind(texture_size=nameLbl.setter('size'))

        noImg = Image(source="images/ynmblank.png",
                      size_hint=(0.1, 1),
                      pos_hint={"x": 0.6, "top": 1})
        maybeImg = Image(source="images/ynmblank.png",
                         size_hint=(0.1, 1),
                         pos_hint={"x": 0.75, "top": 1})
        yesImg = Image(source="images/ynmblank.png",
                       size_hint=(0.1, 1),
                       pos_hint={"x": 0.9, "top": 1})

        if availability == "Y":
            yesImg.source = "images/ynmyes.png"
        elif availability == "M":
            maybeImg.source = "images/ynmmaybe.png"
        else:
            noImg.source = "images/ynmno.png"

        for obj in (nameLbl, noImg, maybeImg, yesImg):
            nameRow.add_widget(obj)

        self.box.add_widget(nameRow)

    def confirm(self, btn):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO tbleventupdates "
                       "(eventID, invitee, updateCode, updateTime) "
                       "VALUES (%s, %s, %s, %s)", (self.eventID, None, 5, timestamp))

        #4cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE viewed=4") #sets status to show those who have joined that there are new updates
        invites = []

        cursor.execute("SELECT invitationID from tblinvitations WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            invites.append(cursorRow[0])

        for invite in invites:
            cursor.execute("DELETE FROM tblavailability WHERE invitationID=%s AND dateTimeID<>%s", (invite, self.dtID))

        cursor.execute("DELETE FROM tbldatetime WHERE eventID=%s AND dateTimeID<>%s", (self.eventID, self.dtID))

        mydb.commit()

        self.manager.current = "viewcreated"

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current = "viewcreateddates"
        self.manager.transition.duration = 0
       
class ViewJoined(Screen):
    #Users can see a list of all the events that they have joined and view updates.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        global currentUsername
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.025),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        newRel = RelativeLayout(size_hint=(1, None),
                                height=self.height*0.08)
        newLbl = Label(text="NEW UPDATES",
                       color=(0.5, 0.5, 0.5, 1),
                       height=self.height*0.08,
                       size_hint=(1, 1),
                       font_size=self.height*0.04)
        newRel.add_widget(newLbl)
        with newRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (newLbl.pos[1]+(newRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.42), newRel.height),
                      pos=((self.size[0]*0.25), (newLbl.pos[1])))

        currentRel = RelativeLayout(size_hint=(1, None),
                                   height=self.height*0.08)
        currentLbl = Label(text="CURRENT EVENTS",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        currentRel.add_widget(currentLbl)
        with currentRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (currentLbl.pos[1]+(currentRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.50), currentRel.height),
                      pos=((self.size[0]*0.21), (currentLbl.pos[1])))
        pastRel = RelativeLayout(size_hint=(1, None),
                                 height=self.height*0.08)
        pastLbl = Label(text="PAST EVENTS",
                        color=(0.5, 0.5, 0.5, 1),
                        height=self.height*0.08,
                        size_hint=(1, 1),
                        font_size=self.height*0.04)
        pastRel.add_widget(pastLbl)
        with pastRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (pastLbl.pos[1]+(pastRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.40), pastRel.height),
                      pos=((self.size[0]*0.26), (pastLbl.pos[1])))

        self.sv = ScrollView(size_hint=(1, 0.675),
                             pos_hint={"x": 0, "top": 0.87})
        self.sv.add_widget(self.box)
        self.add_widget(self.sv)

        listEmpty = True

        #4cursor.execute("SELECT eventID FROM tblinvitations WHERE invitee=%s AND (viewed=%s OR viewed=%s)", (currentUsername, 2, 4)) #2 means new updates, 4 means updates have been viewed
        cursor.execute("SELECT eventID FROM tblinvitations WHERE invitee=%s AND viewed=%s", (currentUsername, 2))
        eventIDs = []

        if cursor.rowcount == 0:
            emptyLbl = Label(color=(0.5, 0.5, 0.5, 1),
                             text="you haven't joined any events -\ncheck your invitations",
                             halign="center",
                             size_hint=(1, None),
                             font_size=self.height*0.045,
                             height=self.height*0.2,
                             text_size=(self.size[0]*0.92, self.height*0.1),
                             valign="middle")
            self.box.add_widget(emptyLbl)
        else:
            for cursorRow in cursor:
                eventIDs.append(cursorRow[0])

            events = []
            for eventID in eventIDs:
                cursor.execute("SELECT eventName FROM tblevents WHERE eventID=%s AND eventID=%s", (eventID, eventID))
                for cursorRow in cursor:
                    events.append((eventID, cursorRow[0]))
       
            new = []
            current = []
            past = []
            currentEvents = []

            #determine whether event is in the past
            #if the date hasn't been confirmed yet then as long as not all the dates are in the past it is considered a current event
            for event in events:
                cursor.execute("SELECT date FROM tbldatetime WHERE eventID=%s OR eventID=%s", (event[0], event[0]))
                numDates = cursor.rowcount
                pastCount = 0
                currentDate = datetime.now().strftime("%Y/%m/%d")
                for cursorRow in cursor:
                    #x[0] is in dd/mm/yyyy format but needs to be yyyy/mm/dd to compare
                    eventDate = cursorRow[0][6:] + "/" + cursorRow[0][3:-5] + "/" + cursorRow[0][:2]
                    if eventDate < currentDate: #if date of event is before current date
                        pastCount += 1
                if numDates == pastCount:
                    past.append(event)
                else:
                    currentEvents.append(event)

            #determine whether current events have new updates
            for event in currentEvents:
                cursor.execute("SELECT viewedTime FROM tblinvitations WHERE eventID=%s AND invitee=%s", (event[0], currentUsername))
                for cursorRow in cursor:
                    viewedTime = cursorRow[0]

                cursor.execute("SELECT updateTime, invitee FROM tbleventupdates WHERE eventID=%s AND invitee<>%s AND (updateCode>3 OR updateCode=1)", (event[0], currentUsername))
                updates = []
                for cursorRow in cursor:
                    updateTime = cursorRow[0]
                    if viewedTime == None: #if the user has never viewed updates for the event hence no time is saved
                        updates.append(cursorRow)
                    else:
                        if updateTime >= viewedTime: #if update was after last viewed
                            updates.append(cursorRow)
                
                if len(updates) > 0:
                    new.append(event)
                else: #if there are no new updates
                    current.append(event)

            if len(new) != 0:
                self.box.add_widget(newRel)
                for n in reversed(new): #reversed so newest updates will be displayed at the top
                    self.addEvent(n[0], n[1], "n")

            if len(current) != 0:
                self.box.add_widget(currentRel)
                for c in reversed(current):
                    self.addEvent(c[0], c[1], "c")

            if len(past) != 0:
                self.box.add_widget(pastRel)
                for p in reversed(past):
                    self.addEvent(p[0], p[1], "p")

    def addEvent(self, eventID, eventName, ncp): #ncp is whether it is new, current or past
        print(eventName)
        #adds event to self.box in a row with buttons to modify and delete the event
        updateCodes = ("invitation declined", "availability entered", "availability changed", "changed poll vote", "details changed", "date confirmed")
        #cursor.execute("SELECT updateCode, invitee FROM tbleventupdates WHERE eventID=%s AND (updateCode>3 OR updateCode=1) AND invitee<>%s", (eventID, currentUsername))
        #numUpdates = cursor.rowcount

        cursor.execute("SELECT viewedTime FROM tblinvitations WHERE eventID=%s AND invitee=%s", (eventID, currentUsername))
        for cursorRow in cursor:
            viewedTime = cursorRow[0]

        cursor.execute("SELECT updateCode, invitee, updateTime FROM tbleventupdates WHERE eventID=%s AND invitee<>%s AND (updateCode>3 OR updateCode=1)", (eventID, currentUsername))
        numUpdates = 0
        updates = []
        for cursorRow in cursor:
            updates.append(cursorRow)

        for update in updates:
            updateTime = update[2]
            if viewedTime == None: #if the user has never viewed updates for the event hence no time is saved
                numUpdates += 1
            else:
                if updateTime >= viewedTime: #if update was after last viewed
                    numUpdates += 1

        code = None
        if ncp == "n":
            if numUpdates == 1:
                for update in updates:
                    code = cursorRow[0]
                    if code == 1:
                        updateTxt = "[color=#7fc1db]" + cursorRow[1] + "[/color] [color=#7f7f7f]joined event[/color]"
                    else:
                        updateTxt = updateCodes[code]
            elif numUpdates == 0:
                updateTxt = "no new updates"
            else:
                updateTxt = str(numUpdates) + " new updates"
        else:
            updateTxt = "no new updates"
           
        invRow = BoxLayout(orientation="horizontal",
                           padding=0,
                           spacing=self.size[0]*0.01,
                           height=self.height*0.1,
                           size_hint=(1, None))
       
        nameBox = BoxLayout(orientation="vertical",
                            spacing=0,
                            size_hint=(0.65, None),
                            height=self.height*0.1)
        eventNameLbl = Label(text=eventName,
                             halign="left",
                             color=(0, 0, 0, 1),
                             font_size=(self.height*0.04),
                             size_hint=(None, 0.67))
        eventNameLbl.bind(texture_size=eventNameLbl.setter('size')) #needed to align to the left

        updateLbl = Label(text=updateTxt,
                          markup=True,
                          halign="left",
                          color=(0.5, 0.5, 0.5, 1),
                          font_size=self.height*0.034,
                          size_hint=(None, 0.33))
        updateLbl.bind(texture_size=updateLbl.setter('size'))

        if ncp == "n": #if it is a new event
            viewBtn = Button1(text="view",
                              font_size=self.height*0.034,
                              size_hint=(0.35, 1))
        elif ncp == "c": #if it is a current event
            viewBtn = Button1grey(text="view",
                                  font_size=self.height*0.034,
                                  size_hint=(0.35, 1))
        else: #otherwise it must be a past event
            nameBox.size_hint=(0.56, None)
            viewBtn = Button1grey(text="view",
                                  size_hint=(0.22, 0.85))
            leaveBtn = Button1red(text="leave",
                                  font_size=self.height*0.02,
                                  size_hint=(0.22, 0.85),
                                  on_release=lambda *args: self.leave(eventID, *args))

        viewBtn.on_release = lambda *args: self.view(eventID, *args)
       
        if code == 4:
            updateLbl.color=(1, 0.36, 0.41, 1)
        elif code == 5:
            updateLbl.color=(0.46, 0.74, 0.65, 1)
       
        nameBox.add_widget(eventNameLbl)
        nameBox.add_widget(updateLbl)

        invRow.add_widget(nameBox)
        invRow.add_widget(viewBtn)
        if ncp == "p":
            invRow.add_widget(leaveBtn)

        self.box.add_widget(invRow)

    def view(self, eventID):
        ViewJoinedDetails.eventID = eventID
        self.manager.current = "viewjoineddetails"

    def leave(self, eventID, btn):
        global currentUsername
        cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, eventID))
        for cursorRow in cursor:
            invID = cursorRow[0]
        cursor.execute("DELETE FROM tblavailability WHERE invitationID=%s and invitationID=%s", (invID, invID))
        cursor.execute("DELETE FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, eventID))
        mydb.commit()
        self.on_enter()

class ViewJoinedDetails(Screen):
    #Shows event details of a joined event and gives options to view poll results and new updates or leave the event.
    def on_enter(self):    
        try:
            self.box.clear_widgets()
        except:
            pass
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.8),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        global currentUsername
       
        cursor.execute("SELECT eventName, creator, description, locationName, locationDescription, tag1, tag2, tag3, pollID FROM tblevents WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))

        for cursorRow in cursor:
            eventName = cursorRow[0]
            creator = cursorRow[1]
            description = cursorRow[2]
            locationName = cursorRow[3]
            locationDescription = cursorRow[4]
            tag1 = cursorRow[5]
            tag2 = cursorRow[6]
            tag3 = cursorRow[7]
            pollID = cursorRow[8]

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)                        

        nameLbl = Label(text=eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)
        createdLbl = Label(text=("created by " + creator),
                           color=(0.5, 0.5, 0.5, 1),
                           font_size=(self.height*0.035),
                           text_size=(self.size[0]*0.92, self.height*0.04), #needed to align to top and center
                           valign="top",
                           halign="center",
                           size_hint=(1, None),
                           height=self.height*0.04)
        descBox=TextInput2(text=description,
                               disabled=True,
                               size_hint=(1, None),
                               height=self.height*0.14)

        locationFloat = FloatLayout(size_hint=(1, None),
                                    height=self.height*0.06)
        locationLbl = Label(text=("Location: " + locationName),
                            color=(0.5, 0.5, 0.5, 1),
                            font_size=(self.height*0.035),
                            text_size=(self.size[0]*0.92, self.height*0.06),
                            valign="bottom",
                            halign="left",
                            size_hint=(1, 1),
                            pos_hint={"x": 0, "top": 1},
                            height=self.height*0.06)
        locationBtn = IconButton(size_hint=(1, 1),
                                 pos_hint={"x": 0, "top": 1},
                                 on_release=lambda *args: self.viewDesc(locationDescription, *args))
        locationFloat.add_widget(locationBtn)
        locationFloat.add_widget(locationLbl)

        #inviteeRow shows the number of people left to respond and a button so they can add or remove invites
        numRemaining = None
        #4cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND viewed<>%s AND viewed<>%s", (self.eventID, 2, 4))
        cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND viewed<>%s", (self.eventID, 2))
        numRemaining = cursor.rowcount
        if numRemaining == 0:
            updateTxt = "everyone has responded"
        else:
            updateTxt = str(numRemaining) + " left to respond"

        inviteeRow = BoxLayout(orientation="horizontal",
                               spacing=0,
                               padding=[0, self.height*0.01],
                               size_hint=(1, None),
                               height=self.height*0.08)
        inviteeLbl = Label(text=updateTxt,
                           color=(0.50, 0.77, 0.89, 1),
                           font_size=self.height*0.03,
                           size_hint=(0.53, 1))
        inviteeBtn = Button1(text="see invitees",
                             size_hint=(0.43, 1),
                             on_release=self.seeInvitees)
        inviteeRow.add_widget(inviteeLbl)
        inviteeRow.add_widget(inviteeBtn)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)
        self.box.add_widget(createdLbl)
        if description != "":
            self.box.add_widget(descBox)
        if locationName != "":
            self.box.add_widget(locationFloat)
        self.box.add_widget(inviteeRow)

        #display poll
        cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            pollID = cursorRow[0]
        if pollID != None:
            cursor.execute("SELECT title FROM tblpolls WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            for cursorRow in cursor:
                pollTitle = cursorRow[0]
            pollRow = GridLayout(rows=1,
                                 cols=2,
                                 row_default_height=self.height*0.08,
                                 row_force_default=True,
                                 col_force_default=True,
                                 size_hint=(1, None),
                                 padding=[self.size[0]*0.08, 0, 0, 0],
                                 height=self.height*0.08,
                                 spacing=self.size[0]*0.1)
            pollLbl1 = Label(text="POLL:",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=self.height*0.04,
                             size_hint=(0.2, 1))
            pollLbl2 = Label(text=pollTitle,
                             halign="left",
                             color=(0, 0, 0, 1),
                             size_hint=(None, 1),
                             font_size=self.height*0.035)
            pollLbl2.bind(texture_size=pollLbl2.setter('size'))
           
            pollRow.add_widget(pollLbl1)
            pollRow.add_widget(pollLbl2)
            self.box.add_widget(pollRow)

            cursor.execute("SELECT optionNo, optionText FROM tblpolloptions WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            optionTexts = {}
            for cursorRow in cursor:
                optionTexts[cursorRow[0]] = cursorRow[1]

            #counting votes
            votes = {}
            numVotes = 0
            for optionNo in optionTexts:
                votes[optionNo] = 0
            cursor.execute("SELECT optionNo FROM tblpollvotes WHERE pollID=%s AND pollID=%s", (pollID, pollID))
            for cursorRow in cursor:
                votes[cursorRow[0]] += 1
                numVotes += 1
            if numVotes != 0:
                for optionNo in optionTexts:
                    percent = int((votes[optionNo] / numVotes * 100))
                    if percent == 0:
                        barwidth = 0.001
                    else:
                        barwidth = percent / 100
                    optionRow = GridLayout(rows=1,
                                           cols=2,
                                           cols_minimum={0: self.size[0]*0.75*barwidth, 1: self.size[0]*0.75*(1-barwidth)},
                                           row_default_height=self.height*0.06,
                                           row_force_default=True,
                                           col_force_default=True,
                                           size_hint=(1, None),
                                           spacing=self.size[0]*0.03,
                                           height=self.height*0.06,
                                           padding=0)
                    optionBar = Button3(size_hint=(1, 1))

                    votesTxt = Label(text=str(votes[optionNo]) + " (" + str(percent) + "%)",
                                     color=(0.5, 0.5, 0.5, 1),
                                     size_hint=(None, 1),
                                     font_size=self.height*0.03,
                                     halign="left")
                    votesTxt.bind(texture_size=votesTxt.setter('size'))

                    optionTxt = Label(text=optionTexts[optionNo],
                                      color=(0, 0, 0, 1),
                                      halign="left",
                                      valign="top",
                                      text_size=(self.size[0]*0.92, self.height*0.06),
                                      size_hint=(None, None),
                                      height=self.height*0.06,
                                      font_size=self.height*0.035)
                    optionTxt.bind(texture_size=optionTxt.setter('size'))

                    optionRow.add_widget(optionBar)
                    optionRow.add_widget(votesTxt)
                    self.box.add_widget(optionRow)
                    self.box.add_widget(optionTxt)
            else:
                noVotesTxt = Label(text="no votes yet",
                                   color=(0.5, 0.5, 0.5, 1),
                                   halign="center",
                                   valign="top",
                                   text_size=(self.size[0]*0.92, self.height*0.08),
                                   font_size=self.height*0.035,
                                   height=self.height*0.08)
                noVotesTxt.bind(texture_size=noVotesTxt.setter('size'))
                self.box.add_widget(noVotesTxt)

            changeVoteBtn = Button1grey(text="change poll vote",
                                        font_size=self.height*0.06,
                                        size_hint=(1, None),
                                        height=self.height*0.083,
                                        on_release = lambda *args: self.changeVote(pollID, *args))
                                       
        #display dates
        cursor.execute("SELECT updateCode FROM tbleventupdates WHERE eventID=%s AND updateCode=%s", (self.eventID, 5))
        if cursor.rowcount == 0: #date unconfirmed
            datesRel = RelativeLayout(size_hint=(1, None),
                                      height=self.height*0.08)
            datesLbl = Label(text="DATES",
                             color=(0.5, 0.5, 0.5, 1),
                             height=self.height*0.08,
                             size_hint=(1, 1),
                             font_size=self.height*0.04)
            datesRel.add_widget(datesLbl)
            with datesRel.canvas.before:
                Color(0.50, 0.76, 0.86, 1)
                Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                          pos=(0, (datesLbl.pos[1]+(datesRel.height/2))))
                Color(1, 1, 1, 1)
                Rectangle(size=((self.size[0]*0.20), datesRel.height),
                          pos=((self.size[0]*0.36), (datesLbl.pos[1])))
        else:
            datesRel = RelativeLayout(size_hint=(1, None),
                                      height=self.height*0.08)
            datesLbl = Label(text="DATE CONFIRMED",
                             color=(0.5, 0.5, 0.5, 1),
                             height=self.height*0.08,
                             size_hint=(1, 1),
                             font_size=self.height*0.04)
            datesRel.add_widget(datesLbl)
            with datesRel.canvas.before:
                Color(0.50, 0.76, 0.86, 1)
                Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                          pos=(0, (datesLbl.pos[1]+(datesRel.height/2))))
                Color(1, 1, 1, 1)
                Rectangle(size=((self.size[0]*0.48), datesRel.height),
                          pos=((self.size[0]*0.22), (datesLbl.pos[1])))

        self.box.add_widget(datesRel)

        cursor.execute("SELECT date, startTime, endTime FROM tbldatetime WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))
        dates = []
        dateTimes = []
        for cursorRow in cursor:
            date = cursorRow[0]
            time1 = cursorRow[1]
            time2 = cursorRow[2]
            if time1 == None:
                times = "all day"
            else:
                times = time1 + "-" + time2

            if date not in dates:
                dates.append(date)
                dateTimes.append([date, [times]])
            else:
                for dt in dateTimes:
                    if date == dt[0]:
                        dt[1].append(times)

        for dt in dateTimes:
            dtBox = BoxLayout(orientation="vertical",
                              spacing=0,
                              size_hint=(0.55, None),
                              height=self.height*0.1)
            dateLbl = Label(text=dateToText(dt[0]),
                            halign="left",
                            color=(0, 0, 0, 1),
                            font_size=(self.height*0.04),
                            size_hint=(None, 0.67))
            dateLbl.bind(texture_size=dateLbl.setter('size')) #needed to align to the left

            timesText = ""
            for time in dt[1]:
                timesText = timesText + time + ", "

            timesText = timesText[:-2] #cuts off the last ", " characters

            timesLbl = Label(text=timesText,
                             halign="left",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=(self.height*0.03),
                             size_hint=(None, 0.33))
            timesLbl.bind(texture_size=timesLbl.setter('size'))

            dtBox.add_widget(dateLbl)
            dtBox.add_widget(timesLbl)

            self.box.add_widget(dtBox)

        #display new updates
        updatesRel = RelativeLayout(size_hint=(1, None),
                                    height=self.height*0.08)
        updatesLbl = Label(text="NEW UPDATES",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        updatesRel.add_widget(updatesLbl)
        with updatesRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (updatesLbl.pos[1]+(updatesRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.40), updatesRel.height),
                      pos=((self.size[0]*0.26), (updatesLbl.pos[1])))

        cursor.execute("SELECT viewedTime FROM tblinvitations WHERE eventID=%s AND invitee=%s", (self.eventID, currentUsername))
        for cursorRow in cursor:
            viewedTime = cursorRow[0]

        updateCodes = ("declined invitation", "entered availability", "changed availability", "changed poll vote", "event details changed", "date confirmed")
        cursor.execute("SELECT updateCode, invitee, updateTime FROM tbleventupdates WHERE eventID=%s AND (updateCode>%s OR updateCode=%s)", (self.eventID, 3, 1))
        updates = []
        for cursorRow in cursor:
            updateTime = cursorRow[2]
            if viewedTime == None: #if the user has never viewed updates for the event hence no time is saved
                updates.append(cursorRow)
            else:
                if updateTime >= viewedTime: #if update was before last viewed
                    updates.append(cursorRow)

        if len(updates) != 0:
            self.box.add_widget(updatesRel)

        for u in reversed(updates): #shows newest updates first
            if u[1] != None:
                cursor.execute("SELECT displayName FROM tblaccounts WHERE username=%s AND username=%s", (u[1], u[1]))
                for cursorRow in cursor:
                    username = cursorRow[0]
                updateTxt = Label(text="[color=#7fc1db]" + username + "[/color] [color=#7f7f7f]" + updateCodes[u[0]] + "[/color]",
                                  markup=True)
            else:
                updateTxt = Label(text=updateCodes[u[0]],
                                  color=(0, 0, 0, 1))
            updateTxt.halign="left"
            updateTxt.bind(texture_size=updateTxt.setter('size'))
            updateTxt.height=self.height*0.07
            updateTxt.font_size=self.height*0.035
            updateTxt.size_hint=(None, None)
            self.box.add_widget(updateTxt)
   
        changeBtn = Button1(text="change availability",
                            font_size=self.height*0.06,
                            size_hint=(1, None),
                            height=self.height*0.083,
                            on_release=lambda *args: self.changeAvailability(eventName, dateTimes, *args))
        deleteBtn = Button2(text="leave event",
                            color=(1, 0.36, 0.41, 1),
                            size_hint=(1, None),
                            height=self.height*0.072,
                            on_release=self.leave)
        self.box.add_widget(changeBtn)
        if pollID != None:
            self.box.add_widget(changeVoteBtn)
        self.box.add_widget(deleteBtn)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #4cursor.execute("UPDATE tblinvitations SET viewed=4 WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID)) #event is now not a new update
        cursor.execute("UPDATE tblinvitations SET viewedTime=%s WHERE invitee=%s AND eventID=%s", (timestamp, currentUsername, self.eventID)) #change viewedTime so they will not be shown the updates they have just viewed
        mydb.commit()

    def viewDesc(self, description, btn):
        if description != "":
            Info1.message = description
            Factory.Info1().open()
           
    def seeInvitees(self, btn):
        SeeInvitees.eventID = self.eventID
        Factory.SeeInvitees().open()

    def changeAvailability(self, name, dateTimes, btn):
        ViewJoinedAvailability.eventID=self.eventID
        ViewJoinedAvailability.eventName=name
        ViewJoinedAvailability.dateTimes=dateTimes
        self.manager.current="viewjoinedavailability"

    def changeVote(self, pollID, btn):
        ViewJoinedPoll.pollID = pollID
        ViewJoinedPoll.eventID = self.eventID
        self.manager.current="viewjoinedpoll"

    def leave(self, btn):
        #removes the user from the event; deletes invitation and any corresponding availability and poll votes
        global currentUsername
        cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
        for cursorRow in cursor:
            invID = cursorRow[0]
        cursor.execute("DELETE FROM tblavailability WHERE invitationID=%s AND invitationID=%s", (invID, invID))
        cursor.execute("DELETE FROM tblpollvotes WHERE invitationID=%s AND invitationID=%s", (invID, invID))
        cursor.execute("DELETE FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
        mydb.commit()

        Info1.message = "you have left the event"
        Factory.Info1().open()
        self.manager.current = "viewjoined"
       
    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current = "viewjoined"
        self.manager.transition.duration = 0

class ViewJoinedAvailability(Screen):
    #Allows an invitee who has joined an event to change the availability that they have previously entered.
    dateTimes = ObjectProperty(None)
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.8),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)

        nameLbl = Label(text=self.eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        submitBtn = Button1(text="save changes",
                            size_hint=(1, None),
                            height=self.height*0.07,
                            font_size=self.height*0.06,
                            on_release=self.submitBtn)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        self.boxes = []
        for date in self.dateTimes:
            self.addDate(date)

        self.box.add_widget(submitBtn)

    def addDate(self, dt):
        #dt is an array with 2 elements: the date and then an array of all the times
        dateRow = BoxLayout(orientation="horizontal",
                            spacing=self.size[0]*0.05,
                            size_hint=(1, None),
                            height=self.height*0.1)

        dateLbl = Label(text=dateToText(dt[0]),
                        color=(0.15, 0.22, 0.28, 1),
                        size_hint=(0.55, None),
                        height=self.height*0.072,
                        font_size=self.height*0.042)

        noLbl = Label(text="no",
                      color=(1, 0.36, 0.41, 1),
                      size_hint=(0.1, None),
                      font_size=self.height*0.03,
                      height=self.height*0.072)

        maybeLbl = Label(text="maybe",
                         color=(0.5, 0.5, 0.5, 10),
                         size_hint=(0.1, None),
                         font_size=self.height*0.03,
                         height=self.height*0.072)

        yesLbl = Label(text="yes",
                       color=(0.46, 0.74, 0.65, 1),
                       size_hint=(0.1, None),
                       font_size=self.height*0.03,
                       height=self.height*0.072)

        for obj in (dateLbl, noLbl, maybeLbl, yesLbl):
            dateRow.add_widget(obj)

        self.box.add_widget(dateRow)

        for time in dt[1]:
            self.addTimeRow(time, dt[0])

    def addTimeRow(self, time, date):
        timeRow = BoxLayout(orientation="horizontal",
                            spacing=self.size[0]*0.05,
                            size_hint=(1, None),
                            height=self.height*0.05)
                           
        timeLbl = Label(text=time,
                        color=(0, 0, 0, 1),
                        size_hint=(0.55, None),
                        height=self.height*0.045,
                        font_size=self.height*0.036)

        noFloat = FloatLayout(size_hint=(0.1, None),
                              height=self.height*0.045)
        noBtn = IconButton(size_hint=(1, None),
                           height=self.height*0.045,
                           pos_hint={"x": 0, "top": 1})
        noImg = Image(source="images/ynmblank.png",
                      size_hint=(1, None),
                      height=self.height*0.045,
                      pos_hint={"x": 0, "top": 1})
        noFloat.add_widget(noBtn)
        noFloat.add_widget(noImg)

        maybeFloat = FloatLayout(size_hint=(0.1, None),
                                 height=self.height*0.045)
        maybeBtn = IconButton(size_hint=(1, None),
                              height=self.height*0.045,
                              pos_hint={"x": 0, "top": 1})
        maybeImg = Image(source="images/ynmblank.png",
                         size_hint=(1, None),
                         height=self.height*0.045,
                         pos_hint={"x": 0, "top": 1})
        maybeFloat.add_widget(maybeBtn)
        maybeFloat.add_widget(maybeImg)

        yesFloat = FloatLayout(size_hint=(0.1, None),
                               height=self.height*0.045)
        yesBtn = IconButton(size_hint=(1, None),
                            height=self.height*0.045,
                            pos_hint={"x": 0, "top": 1})
        yesImg = Image(source="images/ynmblank.png",
                       size_hint=(1, None),
                       height=self.height*0.045,
                       pos_hint={"x": 0, "top": 1})
        yesFloat.add_widget(yesBtn)
        yesFloat.add_widget(yesImg)

        noBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "N", *args)
        maybeBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "M", *args)
        yesBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "Y", *args)

        for obj in (timeLbl, noFloat, maybeFloat, yesFloat):
            timeRow.add_widget(obj)

        self.box.add_widget(timeRow)
        self.boxes.append((noImg, maybeImg, yesImg))

        #autofill availability
        if time == "all day":
            t1 = None
            t2 = None
        else:
            t1 = time[:5] #selects startTime (both startTime and endTime must be 5 chars)
            t2 = time[6:] #selects endTime (ignores the '-' between them)
       
        if t1 == None: #no need to check both t1 and t2 as it can only be None if endTime is also null
            cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime IS NULL", (self.eventID, date))
        else:
            cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime=%s and endTime=%s", (self.eventID, date, t1, t2))
        for cursorRow in cursor:
            dtID = cursorRow[0]

        cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
        for cursorRow in cursor:
            inviteID = cursorRow[0]

        cursor.execute("SELECT availability FROM tblavailability WHERE dateTimeID=%s AND invitationID=%s", (dtID, inviteID))
        for cursorRow in cursor:
            availability = cursorRow[0]

        if availability == "Y":
            self.boxPressed(noImg, maybeImg, yesImg, "Y")
        elif availability == "M":
            self.boxPressed(noImg, maybeImg, yesImg, "M")
        else:
            self.boxPressed(noImg, maybeImg, yesImg, "N")

    def boxPressed(self, noImg, maybeImg, yesImg, pressed):
        #selects the 'pressed' box and deselects other boxes (by changing image source)
        noImg.source = "images/ynmblank.png"
        maybeImg.source = "images/ynmblank.png"
        yesImg.source = "images/ynmblank.png"

        if pressed == "N":
            noImg.source = "images/ynmno.png"
        elif pressed == "M":
            maybeImg.source = "images/ynmmaybe.png"
        else:
            yesImg.source = "images/ynmyes.png"

    def submitBtn(self, btn):
        #validates that availability has been entered for each row then updates the MySQL database.
        global currentUsername

        valid = True
        for row in self.boxes: #check there are no rows where no option is ticked
            if row[0].source == "images/ynmblank.png" and row[1].source == "images/ynmblank.png" and row[2].source == "images/ynmblank.png":
                message = "you must enter your availability for all dates and times"
                Info1.message = message
                Factory.Info1().open()
                break #avoids repeated messages being displayed

        if valid == True:
            cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
            for cursorRow in cursor:
                inviteID = cursorRow[0]
           
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #add to update table so creator can be notified
            cursor.execute("INSERT INTO tbleventupdates "
                           "(eventID, invitee, updateCode, updateTime, viewed) "
                           "VALUES (%s, %s, %s, %s, %s)", (self.eventID, currentUsername, 2, timestamp, 0))
            mydb.commit()

            availability = [] #list of all availability in order by date displayed
            for i in self.boxes:
                for j in i:
                    if j.source != "images/ynmblank.png":
                        if j.source == "images/ynmno.png":
                            avail = "N"
                        elif j.source == "images/ynmmaybe.png":
                            avail = "M"
                        else:
                            avail = "Y"
                        availability.append(avail)

            i = 0
            for dateRow in self.dateTimes:
                for times in dateRow[1]:
                    if times == "all day":
                        t1 = None
                        t2 = None
                    else:
                        t1 = times[:5] #selects startTime (both startTime and endTime must be 5 chars)
                        t2 = times[6:] #selects endTime (ignores the '-' between them)
                   
                    if t1 == None: #no need to check both t1 and t2 as it can only be None if endTime is also null
                        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime IS NULL", (self.eventID, dateRow[0]))
                    else:
                        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime=%s and endTime=%s", (self.eventID, dateRow[0], t1, t2))
                    for cursorRow in cursor:
                        dtID = cursorRow[0]

                    cursor.execute("UPDATE tblavailability SET availability=%s WHERE invitationID=%s AND dateTimeID=%s", (availability[i], inviteID, dtID))
                    mydb.commit()
                    i += 1

            cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
            for cursorRow in cursor:
                pollID = cursorRow[0]

            Info1.message = "availability changes saved"
            Factory.Info1().open()
            self.manager.current="viewjoineddetails"

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="viewjoineddetails"
        self.manager.transition.duration = 0

class ViewJoinedPoll(Screen):
    #Allows an invitee who has joined an event to change their poll vote.
    eventID = ObjectProperty(None)
    pollID = ObjectProperty(None)
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass
       
        cursor.execute("SELECT title FROM tblpolls WHERE pollID=%s AND pollID=%s", (self.pollID, self.pollID))
        for cursorRow in cursor:
            pollTitle = cursorRow[0]

        options = []
        cursor.execute("SELECT optionText FROM tblpolloptions WHERE pollID=%s OR pollID=%s ORDER BY optionNo", (self.pollID, self.pollID))
        for cursorRow in cursor:
            options.append(cursorRow[0])
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.04,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.8),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)

        nameLbl = Label(text="[color=#7f7f7f]POLL:" "[/color] [color=#7fc1db]" + pollTitle + "[/color]",
                        markup=True,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.035),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        submitBtn = Button1(text="vote and join event",
                            size_hint=(1, None),
                            height=self.height*0.1,
                            font_size=self.height*0.07,
                            on_release=self.submitBtn)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        self.optionImgs = []

        #display options
        for option in options:
            self.displayOption(option)

        #autofill
        global currentUsername
        cursor.execute("SELECT invitationID FROM tblinvitations WHERE eventID=%s AND invitee=%s", (self.eventID, currentUsername))
        for cursorRow in cursor:
            inviteID = cursorRow[0]

        cursor.execute("SELECT optionNo FROM tblpollvotes WHERE invitationID=%s AND pollID=%s", (inviteID, self.pollID))
        for cursorRow in cursor:
            self.vote(self.optionImgs[cursorRow[0]-1])

        self.box.add_widget(submitBtn)

    def displayOption(self, option):
        #adds the text for the poll to the screen along with the vote checkbox
        optionFloat = FloatLayout(size_hint=(1, None),
                                  height=self.height*0.06)
        optionBtn = IconButton(size_hint=(1, 1),
                               pos_hint={"x": 0, "top": 1})
        optionLbl = Label(text=option,
                          halign="left",
                          font_size=(self.height*0.042),
                          pos_hint={"x": 0.22, "top": 1},
                          color=(0, 0, 0, 1),
                          size_hint=(None, 1))
        optionLbl.bind(texture_size=optionLbl.setter('size')) #needed to align to the left
        optionImg = Image(source="images/unticked.png",
                          size_hint=(0.2, 1),
                          pos_hint={"x": 0, "top": 1})

        optionBtn.on_release = lambda *args: self.vote(optionImg, *args)
        optionFloat.add_widget(optionBtn)
        optionFloat.add_widget(optionLbl)
        optionFloat.add_widget(optionImg)
        self.box.add_widget(optionFloat)

        self.optionImgs.append(optionImg)

    def vote(self, img):
        #selects the box for the option pressed and deselects all the other checkboxes
        if img.source == "images/unticked.png":
            img.source = "images/ticked.png"
        else:
            img.source = "images/unticked.png"

        for optionImg in self.optionImgs: #unticks all other options
            if optionImg != img:
                optionImg.source = "images/unticked.png"

    def submitBtn(self, btn):
        #checks that an option has been selected then updates the MySQL database with the new vote
        optionNo = 0
        for i in range(0, len(self.optionImgs)): #checks which option has been selected
            if self.optionImgs[i].source == "images/ticked.png":
                optionNo = i + 1
        if optionNo == 0: #if no options have been selected
            message = "you must select an option to vote"
            Info1.message = message
            Factory.Info1().open()
        else:        
            global currentUsername
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
            for cursorRow in cursor:
                inviteID = cursorRow[0]
            #viewed = 2 means they have responded to the invitation so it will not be displayed as a new invite
            cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE invitationID=%s AND invitationID=%s", (inviteID, inviteID))
            cursor.execute("INSERT INTO tbleventupdates "
                           "(eventID, invitee, updateCode, updateTime, viewed)"
                           "VALUES (%s, %s, %s, %s, %s)", (self.eventID, currentUsername, 3, timestamp, 0))

            cursor.execute("UPDATE tblpollvotes SET optionNo=%s WHERE pollID=%s AND invitationID=%s", (optionNo, self.pollID, inviteID))
            mydb.commit()

            Info1.message = "poll vote updated"
            Factory.Info1().open()
            self.manager.current="viewjoineddetails"

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="viewjoineddetails"
        self.manager.transition.duration = 0

class CreateEventDetails(Screen):
    #Displays fields for the event name and description plus buttons that open popups to add a poll, tags or location
    eventname = ObjectProperty(None)
    def on_enter(self):
        global currentEvent
        self.eventname.text = currentEvent.eventName
       
    def on_leave(self): #get text inputs and save to currentEvent object
        global currentEvent
        currentEvent.eventName = self.eventname.text

    def info(self):
        #called when they click on one of the info icons
        message = "max 20 characters\nadd a description for any extra details"
        Info1.message = message
        Factory.Info1().open()

class CreateEventDates(Screen):
    #Allows user to create date-time options and validates each date option (which can have multiple timeslots) before adding them
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        global currentEvent
        self.currentDate = []
        self.currentTimes = []
        self.addedDates = []

        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.02),
                             padding=[(self.height*0.04),0,(self.height*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        self.newDateFloat = FloatLayout(size_hint=(0.5, None),
                                        height=self.height*0.18)
       
        newDate = IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0, "top": 1},
                             on_release=self.newDateBtn)
        newDateLbl = Label(text="new date",
                           halign="left",
                           font_size=self.height*0.05,
                           pos_hint={"x": 0.3, "top": 1},
                           color=(0, 0, 0, 1),
                           size_hint=(0.7, 1),
                           height=self.height*0.08)
        newDateImg = Image(source="images/add1.png",
                           size_hint=(0.3, 1),
                           pos_hint={"x": 0, "top": 1})

        self.addedRel = RelativeLayout(size_hint=(1, None),
                                       height=self.height*0.08)

        addedLbl = Label(text="DATES ADDED",
                         color=(0.5, 0.5, 0.5, 1),
                         size_hint=(1, 1),
                         font_size=self.height*0.04)
        self.addedRel.add_widget(addedLbl)

        with self.addedRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (addedLbl.pos[1]+(self.addedRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.4), self.addedRel.height),
                      pos=((self.size[0]*0.24), (addedLbl.pos[1])))
           
        self.newDateFloat.add_widget(newDate)
        self.newDateFloat.add_widget(newDateLbl)
        self.newDateFloat.add_widget(newDateImg)
        self.box.add_widget(self.newDateFloat)
        self.box.add_widget(self.addedRel)
        for addedDate in currentEvent.dtAdded:
            self.updateAdded(addedDate[0], addedDate[1])

        sv = ScrollView(size_hint=(1, 0.695),
                        pos_hint={"x": 0, "top": 0.89})
        sv.add_widget(self.box)
        self.add_widget(sv)

    def newDateBtn(self, btn):
        #adds a row of TextInput boxes to allow the user to enter a date
        self.box.clear_widgets()
        self.box.padding = [(self.height*0.04),(self.height*0.04),(self.height*0.04),(self.height*0.025)]

        self.dateRow = BoxLayout(orientation="horizontal",
                                 padding=[self.height*0.025, 0],
                                 height=self.height*0.08,
                                 size_hint=(1, None))

        date1=TextInput(size_hint=(0.21, 1),
                        hint_text="DD")
        slash1=Label()
        date2=TextInput(size_hint=(0.21, 1),
                        hint_text="MM")
        slash2=Label()
        date3=TextInput(size_hint=(0.31, 1),
                        hint_text="YYYY")

        for date in (date1, date2, date3):
            date.background_normal = ""
            date.background_active=""
            date.background_color=(0.70,0.85, 0.91, 1)
            date.halign="center"
            date.font_size=self.height*0.04
            date.write_tab=False
            date.padding=[0, self.height*0.02]
            date.hint_text_color=(0.5, 0.5, 0.5, 1)
            date.input_filter="int"
            date.cursor_color=(0.5, 0.5, 0.5, 1)

        for slash in (slash1, slash2):
            slash.text="/"
            slash.halign="left"
            slash.font_size=self.height*0.05
            slash.size_hint=(0.14, 1)
            slash.color=(0, 0, 0, 1)

        self.timeOptions = BoxLayout(orientation="horizontal",
                                     padding=[self.height*0.025, 0],
                                     height=self.height*0.15,
                                     size_hint=(1, None))
        newTimeFloat = FloatLayout(size_hint=(0.43, 1))
        newTime = IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0, "top": 1},
                             on_release=self.newTimeBtn)
        newTimeLbl = Label(text="add times",
                           halign="left",
                           font_size=(self.height*0.042),
                           pos_hint={"x": 0.31, "top": 1},
                           color=(0, 0, 0, 1),
                           size_hint=(0.7, 1),
                           height=self.height*0.08)
        newTimeImg = Image(source="images/add1.png",
                           size_hint=(0.3, 1),
                           pos_hint={"x": 0, "top": 1})
        orLbl = Label(text="OR",
                      halign="center",
                      font_size=(self.height*0.04),
                      size_hint=(0.26,1),
                      color=(0, 0, 0, 1),
                      padding=[0, self.height*0.015])
        allDayFloat = FloatLayout(size_hint=(0.31, 1))
        allDay = IconButton(size_hint=(1, 1),
                            pos_hint={"x": 0, "top": 1},
                            on_release=self.allDayBtn)
        allDayLbl = Label(text="all day",
                          halign="left",
                          font_size=(self.height*0.042),
                          pos_hint={"x": 0.32, "top": 1},
                          color=(0, 0, 0, 1),
                          size_hint=(0.7, 1),
                          height=self.height*0.08)
        self.allDayImg = Image(source="images/unticked.png",
                               size_hint=(0.25, 1),
                               pos_hint={"x": 0, "top": 1})

        self.addDate=Button1(text="add date",
                             size_hint=(0.44, None),
                             pos_hint={"x": 0.28, "top": 1},
                             height=(self.height*0.1),
                             on_release=self.addDateBtn)

        for obj in (date1, slash1, date2, slash2, date3):
            self.dateRow.add_widget(obj)

        newTimeFloat.add_widget(newTime)
        newTimeFloat.add_widget(newTimeLbl)
        newTimeFloat.add_widget(newTimeImg)
        self.timeOptions.add_widget(newTimeFloat)
        self.timeOptions.add_widget(orLbl)
       
        allDayFloat.add_widget(allDay)
        allDayFloat.add_widget(allDayLbl)
        allDayFloat.add_widget(self.allDayImg)
        self.timeOptions.add_widget(allDayFloat)
   
        self.box.add_widget(self.dateRow)
        self.box.add_widget(self.timeOptions)
        self.box.add_widget(self.addDate)
        self.box.add_widget(self.addedRel)
        for addedDate in self.addedDates:
            self.box.add_widget(addedDate[2])
       
        self.currentDate = [date1, date2, date3]

    def newTimeBtn(self, btn):
        #adds a row of TextInput boxes to allow the user to enter a start and finish time for the date
        self.box.clear_widgets()

        timeRow = BoxLayout(orientation="horizontal",
                            padding=[self.height*0.025, 0],
                            height=self.height*0.075,
                            size_hint=(1, None))

        hr1=TextInput(hint_text="HH")
        colon1=Label()
        to=Label(text="to",
                 halign="center",
                 font_size=(self.height*0.05),
                 size_hint=(0.18, 1),
                 color=(0, 0, 0, 1))
        min1=TextInput(hint_text="MM")
        hr2=TextInput(hint_text="HH")
        colon2=Label()
        min2=TextInput(hint_text="MM")

        for box in (hr1, min1, hr2, min2):
            box.background_normal=""
            box.background_active=""
            box.background_color=(0.95, 0.95, 0.95, 1)
            box.halign="center"
            box.font_size=self.height*0.035
            box.size_hint=(0.14, 1)
            box.write_tab=False
            box.padding=[0, self.height*0.018]
            box.hint_text_color=(0.5, 0.5, 0.5, 1)
            box.input_filter="int"
            box.cursor_color=(0.5, 0.5, 0.5, 1)
       
        for colon in (colon1, colon2):
            colon.text=":"
            colon.halign="center"
            colon.font_size=self.height*0.05
            colon.size_hint=(0.07, 1)
            colon.color=(0, 0, 0, 1)
       
        deleteFloat=FloatLayout(size_hint=(0.08, 1),
                                pos_hint={"x": 0, "top": 1})
        deleteBtn=IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0.2, "top": 1},
                             on_release=self.deleteTimeBtn)
        deleteImg=Image(source="images/del1.png",
                        size_hint=(1, 1),
                        pos_hint={"x": 0.2, "top": 1})
        deleteFloat.add_widget(deleteBtn)
        deleteFloat.add_widget(deleteImg)
       
        for obj in (hr1, colon1, min1, to, hr2, colon2, min2, deleteFloat):
            timeRow.add_widget(obj)

        self.box.add_widget(self.dateRow)
        for row in self.currentTimes: #add above timeRows
            self.box.add_widget(row[1])
        for obj in (timeRow, self.timeOptions, self.addDate, self.addedRel):
            self.box.add_widget(obj)

        for addedDate in self.addedDates:
            self.box.add_widget(addedDate[2])

        self.currentTimes.append((deleteBtn, timeRow, hr1, min1, hr2, min2))

    def allDayBtn(self, btn):
        #toggles all day checkbox
        if self.allDayImg.source=="images/unticked.png":
            self.allDayImg.source="images/ticked.png"
        else:
            self.allDayImg.source="images/unticked.png"

    def addDateBtn(self, btn):
        #validates date and times and called updateAdded if valid
        messages = []
        dateStr = self.currentDate[0].text + "/" + self.currentDate[1].text + "/" + self.currentDate[2].text

        dateValid = True
        for i in range(0, 3):
            self.currentDate[i].background_color = (0.70, 0.85, 0.91, 1)
            if self.currentDate[i].text == "":
                self.currentDate[i].background_color = (1, 0.56, 0.59, 1)
                messages.append("fields cannot be left blank")
                dateValid = False

        day = self.currentDate[0].text
        month = self.currentDate[1].text
        year = self.currentDate[2].text

        #check that no invalid characters have been entered which would cause the program to crash, especially return (\n) key
        try:
            intD = int(day)
        except ValueError:
            self.currentDate[0].background_color = (1, 0.56, 0.59, 1)
            messages.append("invalid character(s) entered")
            dateValid = False
        try:
            intM = int(month)
        except ValueError:
            self.currentDate[1].background_color = (1, 0.56, 0.59, 1)
            messages.append("invalid character(s) entered")
            dateValid = False
        try:
            intY = int(year)
        except ValueError:
            self.currentDate[2].background_color = (1, 0.56, 0.59, 1)
            messages.append("invalid character(s) entered")
            dateValid = False
           
        #date validation
        if dateValid == True:
            if int(month) < 1 or int(month) > 12: #month must be between 1 and 12
                self.currentDate[1].background_color = (1, 0.56, 0.59, 1)
                dateValid = False
               
            if int(month) in (4, 6, 9, 11): #find number of days in the month entered
                daysInMonth = 30
            elif int(month) == 2:
                if (int(year) % 4) == 0:
                    daysInMonth = 29
                else:
                    daysInMonth = 28
            else:
                daysInMonth = 31

            #check against number of days in the month
            if int(day) < 1 or int(day) > daysInMonth:
                self.currentDate[0].background_color = (1, 0.56, 0.59, 1)
                messages.append("day can't exceed the number of days in the month")
                dateValid = False

            #check length of each date field
            if len(day) != 2:
                messages.append("day must have 2 digits")
                self.currentDate[0].background_color=(1, 0.56, 0.59, 1)
                dateValid = False
            if len(month) != 2:
                messages.append("month must have 2 digits")
                self.currentDate[1].background_color=(1, 0.56, 0.59, 1)
                dateValid = False
            if len(year) != 4:
                messages.append("year must have 4 digits")
                self.currentDate[2].background_color=(1, 0.56, 0.59, 1)
                dateValid = False

            #used to check whether the date is in the past or too far into the future
            currentDate = date.today()
            currentDay = currentDate.strftime("%d")
            currentMonth = currentDate.strftime("%m")
            currentYear = currentDate.strftime("%Y")

            try: #try... except for year
                if int(year) > (int(currentYear) + 5): #can't be more than 5 years in the future
                    self.currentDate[2].background_color = (1, 0.56, 0.59, 1)
                    messages.append("date can't be more than 5 years from current year")
                    dateValid = False
                elif year < currentYear: #can't be in the past
                    self.currentDate[2].background_color = (1, 0.56, 0.59, 1)
                    messages.append("date can't be in the past")
                    dateValid = False
                elif year == currentYear:
                    if month < currentMonth:
                        messages.append("date can't be in the past")
                        dateValid = False
                    elif month == currentMonth:
                        if day < currentDay:
                            messages.append("date can't be in the past")
                            dateValid = False
            except ValueError:
                messages.append("invalid character input - must be numbers only")
                self.currentDate[2].background_color=(1, 0.56, 0.59, 1)
                dateValid = False

            for dt in self.addedDates:
                if dt[0] == dateStr:
                    messages.append("date already added")
                    dateValid = False
       
        times = []
        timesValid = True
        for row in self.currentTimes:
            for i in range(2, 6):
                row[i].background_color = (0.95, 0.95, 0.95, 1)
                if row[i].text == "":
                    row[i].background_color=(1, 0.56, 0.59, 1)
                    messages.append("fields cannot be left blank")
                    timesValid = False
            timeStart = row[2].text + ":" + row[3].text
            timeEnd = row[4].text + ":" + row[5].text

            #time validation
            if timesValid == True:
                for i in range(2, 6):
                    if len(row[i].text) != 2: #must be 2 digits for both e.g. 08:00 not 8:00 or 008:00
                        row[i].background_color=(1, 0.56, 0.59, 1) #sets background colour to red
                        messages.append("time entries must have 2 digits")
                        timesValid = False
                for i in range(2, 5, 2): #checks hours (from 0 to 24)
                    if int(row[i].text) < 0 or int(row[i].text) > 24:
                        row[i].background_color=(1, 0.56, 0.59, 1)
                        timesValid = False
                        if int(row[i].text) == 24 and int(row[i+1].text) != 0: #time goes up to 24:00 (midnight)
                            row[i].background_color=(1, 0.56, 0.59, 1)
                            timesValid = False
                for i in range(3, 6, 2): #checks minutes (from 0 to 60)
                    if int(row[i].text) < 0 or int(row[i].text) >= 60:
                        row[i].background_color=(1, 0.56, 0.59, 1)
                        timesValid = False
                if int(row[2].text) > int(row[4].text): #checks timeStart is before timeEnd
                    timesValid = False
                    messages.append("end time must be after start time")
                    for i in range(2, 6):
                        row[i].background_color = (1, 0.56, 0.59, 1)
                elif int(row[2].text) == int(row[4].text):
                    if int(row[3].text) >= int(row[5].text):
                        timesValid = False
                        for i in range(2, 6):
                            row[i].background_color = (1, 0.56, 0.59, 1)
                #check it hasn't already been added
                for timePair in times:
                    if timeStart == timePair[0] and timeEnd == timePair[1]:
                        timesValid = False
                        messages.append("times cannot be the same")
                        for i in range(2, 6):
                            row[i].background_color = (1, 0.56, 0.59, 1)
           
            if timesValid == True:
                times.append((timeStart, timeEnd))
           
        if self.allDayImg.source=="images/ticked.png":
            times.append("all day")

        if dateValid == True and timesValid == True and times != []:
            self.updateAdded(dateStr, times)
            self.currentTimes = []
        else:
            if len(messages) != 0:
                Info1.message = messages[0] #only the first error is displayed (otherwise they'd all be overwritten)
                Factory.Info1().open()
           
    def updateAdded(self, dateStr, times):
        #displays the validated date in the 'dates added' section
        self.box.clear_widgets()
        self.box.padding = [(self.height*0.04),0,(self.height*0.04),(self.height*0.025)]

        addedDateRow = BoxLayout(orientation="horizontal",
                                 padding=0,
                                 height=self.height*0.1,
                                 size_hint=(1, None))

        dtBox = BoxLayout(orientation="vertical",
                          spacing=0,
                          size_hint=(0.55, None),
                          height=self.height*0.1)
        dateLbl = Label(text=dateToText(dateStr),
                        halign="left",
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.04),
                        size_hint=(None, 0.67))
        dateLbl.bind(texture_size=dateLbl.setter('size')) #needed to align to the left

        timesText = ""
        for time in times:
            if time == "all day":
                timesText = timesText + time + ", "
            else:
                timesText = timesText + time[0] + "-" + time[1] + ", "

        timesText = timesText[:-2] #cuts off the last ", " characters

        timesLbl = Label(text=timesText,
                         halign="left",
                         color=(0.5, 0.5, 0.5, 1),
                         font_size=(self.height*0.03),
                         size_hint=(None, 0.33))
        timesLbl.bind(texture_size=timesLbl.setter('size'))

        deleteFloat=FloatLayout(size_hint=(0.17, None),
                                height=self.height*0.08,
                                pos_hint={"x": 0, "top": 1})
        deleteBtn=IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0.2, "top": 0.8},
                             on_release=self.deleteDateBtn)
        deleteImg=Image(source="images/del1.png",
                        size_hint=(1, 1),
                        pos_hint={"x": 0.2, "top": 0.8})

        editBtn = Button1grey(text="edit",
                              size_hint=(0.2, None),
                              height=self.height*0.08,
                              on_release=lambda *args: self.editBtn(dateStr, times, deleteBtn, *args))
       
        deleteFloat.add_widget(deleteBtn)
        deleteFloat.add_widget(deleteImg)
        dtBox.add_widget(dateLbl)
        dtBox.add_widget(timesLbl)

        addedDateRow.add_widget(dtBox)
        addedDateRow.add_widget(editBtn)
        addedDateRow.add_widget(deleteFloat)

        self.box.add_widget(self.newDateFloat)
        self.box.add_widget(self.addedRel)

        self.addedDates.append((dateStr, times, addedDateRow, deleteBtn))

        for addedDate in self.addedDates:
            self.box.add_widget(addedDate[2])

    def editBtn(self, dateStr, times, deleteBtn, btn):
        #allows the user to change a date that they have added
        self.box.clear_widgets()
        self.box.padding = [(self.height*0.04),(self.height*0.04),(self.height*0.04),(self.height*0.025)]

        self.deleteDateBtn(deleteBtn)

        self.dateRow = BoxLayout(orientation="horizontal",
                                 padding=[self.height*0.025, 0],
                                 height=self.height*0.08,
                                 size_hint=(1, None))

        date1=TextInput(size_hint=(0.21, 1),
                        hint_text="DD",
                        text=dateStr[:2])
        slash1=Label()
        date2=TextInput(size_hint=(0.21, 1),
                        hint_text="MM",
                        text=dateStr[3:5])
        slash2=Label()
        date3=TextInput(size_hint=(0.31, 1),
                        hint_text="YYYY",
                        text=dateStr[6:])

        for date in (date1, date2, date3): #set date properties using iteration to improve code efficiency
            date.background_normal = ""
            date.background_active=""
            date.background_color=(0.70,0.85, 0.91, 1)
            date.halign="center"
            date.font_size=self.height*0.04
            date.write_tab=False
            date.padding=[0, self.height*0.02]
            date.hint_text_color=(0.5, 0.5, 0.5, 1)
            date.input_filter="int"
            date.cursor_color=(0.5, 0.5, 0.5, 1)

        for slash in (slash1, slash2):
            slash.text="/"
            slash.halign="left"
            slash.font_size=self.height*0.05
            slash.size_hint=(0.14, 1)
            slash.color=(0, 0, 0, 1)

        self.timeOptions = BoxLayout(orientation="horizontal",
                                     padding=[self.height*0.025, 0],
                                     height=self.height*0.15,
                                     size_hint=(1, None))
        newTimeFloat = FloatLayout(size_hint=(0.43, 1))
        newTime = IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0, "top": 1},
                             on_release=self.newTimeBtn)
        newTimeLbl = Label(text="add times",
                           halign="left",
                           font_size=(self.height*0.042),
                           pos_hint={"x": 0.31, "top": 1},
                           color=(0, 0, 0, 1),
                           size_hint=(0.7, 1),
                           height=self.height*0.08)
        newTimeImg = Image(source="images/add1.png",
                           size_hint=(0.3, 1),
                           pos_hint={"x": 0, "top": 1})
        orLbl = Label(text="OR",
                      halign="center",
                      font_size=(self.height*0.04),
                      size_hint=(0.26,1),
                      color=(0, 0, 0, 1),
                      padding=[0, self.height*0.015])
        allDayFloat = FloatLayout(size_hint=(0.31, 1))
        allDay = IconButton(size_hint=(1, 1),
                            pos_hint={"x": 0, "top": 1},
                            on_release=self.allDayBtn)
        allDayLbl = Label(text="all day",
                          halign="left",
                          font_size=(self.height*0.042),
                          pos_hint={"x": 0.32, "top": 1},
                          color=(0, 0, 0, 1),
                          size_hint=(0.7, 1),
                          height=self.height*0.08)
        self.allDayImg = Image(source="images/unticked.png",
                               size_hint=(0.25, 1),
                               pos_hint={"x": 0, "top": 1})

        self.addDate=Button1(text="add date",
                             size_hint=(0.44, None),
                             pos_hint={"x": 0.28, "top": 1},
                             height=(self.height*0.1),
                             on_release=self.addDateBtn)

        for obj in (date1, slash1, date2, slash2, date3):
            self.dateRow.add_widget(obj)

        newTimeFloat.add_widget(newTime)
        newTimeFloat.add_widget(newTimeLbl)
        newTimeFloat.add_widget(newTimeImg)
        self.timeOptions.add_widget(newTimeFloat)
        self.timeOptions.add_widget(orLbl)
       
        allDayFloat.add_widget(allDay)
        allDayFloat.add_widget(allDayLbl)
        allDayFloat.add_widget(self.allDayImg)
        self.timeOptions.add_widget(allDayFloat)
   
        self.box.add_widget(self.dateRow)
        self.box.add_widget(self.timeOptions)
        self.box.add_widget(self.addDate)
        self.box.add_widget(self.addedRel)
        for addedDate in self.addedDates:
            self.box.add_widget(addedDate[2])
       
        self.currentDate = [date1, date2, date3]

        #times
        for time in times:
            if time == "all day":
                self.allDayImg.source = "images/ticked.png"
            else:
                self.newTimeBtn(None)
                #self.currentTimes elements are tuples in the format (deleteBtn, timeRow, hr1, min1, hr2, min2)
                timeRow = self.currentTimes[len(self.currentTimes)-1]
                timeRow[2].text = time[0][:2]
                timeRow[3].text = time[0][3:]
                timeRow[4].text = time[1][:2]
                timeRow[5].text = time[1][3:]

    def deleteTimeBtn(self, btn):
        #removes the time row from the date currently being added
        for row in self.currentTimes:
            if row[0]==btn:
                self.box.remove_widget(row[1]) #removes 'timeRow' widget from self.box
                self.currentTimes.remove(row)

    def deleteDateBtn(self, btn):
        #deletes a date that has already been added
        for row in self.addedDates:
            if row[3]==btn:
                self.box.remove_widget(row[2])
                self.addedDates.remove(row)

    def on_leave(self):
        addedDates = []
        global currentEvent
        for addedDate in self.addedDates:
            addedDates.append((addedDate[0], addedDate[1]))
        currentEvent.dtAdded = addedDates
       
class CreateEventInvites(Screen):
    #Allows the user to invite people to the event by generating an invite link or searching for usernames.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        self.send = False #changes to true invites have been sent so the on_leave function doesn't re-add the invites
       
        self.invites = []
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.025),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        #container is so that the button doesn't fill the whole screen
        linkGenContainer = BoxLayout(padding=[(self.size[0]*0.05), (self.height*0.01), (self.size[0]*0.05), 0],
                                     size_hint=(1, None),
                                     height=self.height*0.095)
        linkGen = Button1(text="generate invite link",
                          size_hint=(1, 1),
                          font_size=self.height*0.045,
                          on_release=lambda *args: self.createSend(True, *args)) #will create the event then generate a link
        linkGenContainer.add_widget(linkGen)

        addRel = RelativeLayout(size_hint=(1, None),
                                height=self.height*0.08)
        addLbl = Label(text="ADD MANUALLY",
                       color=(0.5, 0.5, 0.5, 1),
                       height=self.height*0.08,
                       size_hint=(1, 1),
                       font_size=self.height*0.04)

        addRel.add_widget(addLbl)

        with addRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (addLbl.pos[1]+(addRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.48), addRel.height),
                      pos=((self.size[0]*0.22), (addLbl.pos[1])))

        enterUsnmLbl = Label(text="enter username",
                             color=(0, 0, 0, 1),
                             size_hint=(1, None),
                             height=self.height*0.072)

        searchRow = BoxLayout(orientation="horizontal",
                              spacing=0,
                              padding=0,
                              size_hint=(1, None),
                              height=self.height*0.071)

        usernameSearch = TextInput1(size_hint=(0.8, 1),
                                    on_text_validate=lambda *args: self.addInvite(usernameSearch.text, usernameSearch, *args)) #pressing enter is same as pressing button
        inviteBtn = Button1(text="invite",
                            size_hint=(0.2, 1),
                            on_release=lambda *args: self.addInvite(usernameSearch.text, usernameSearch, *args))

        manageRel = RelativeLayout(size_hint=(1, None),
                                   height=self.height*0.08)
        manageLbl = Label(text="MANAGE INVITATIONS",
                          color=(0.5, 0.5, 0.5, 1),
                          height=self.height*0.08,
                          size_hint=(1, 1),
                          font_size=self.height*0.04)

        manageRel.add_widget(manageLbl)

        with manageRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (manageLbl.pos[1]+(manageRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.6), manageRel.height),
                      pos=((self.size[0]*0.16), (manageLbl.pos[1])))

        self.createBtnContainer = BoxLayout(padding=[(self.size[0]*0.05), (self.height*0.01), (self.size[0]*0.05), 0],
                                            size_hint=(1, None),
                                            height=self.height*0.12)
        createBtn = Button1(text="create and send invites",
                            font_size=self.height*0.04,
                            size_hint=(1, 1),
                            on_release=lambda *args: self.createSend(False, *args)) #creates the event, does not generate link
        self.createBtnContainer.add_widget(createBtn)
               
        searchRow.add_widget(usernameSearch)
        searchRow.add_widget(inviteBtn)

        for obj in (linkGenContainer, addRel, enterUsnmLbl, searchRow, manageRel, self.createBtnContainer):
            self.box.add_widget(obj)

        sv = ScrollView(size_hint=(1, 0.695),
                        pos_hint={"x": 0, "top": 0.89})
        sv.add_widget(self.box)
        self.add_widget(sv)

        global currentEvent
        for inv in currentEvent.invites: #autofill existing invites
           self.addInvite(inv, None, None)

    def addInvite(self, usernameTxt, usernameObj, btn):
        #validates invite and adds it to the screen
        #note username parameter refers to the textinput object not the actual text
        cursor.execute("SELECT username, displayName FROM tblaccounts WHERE username=%s OR username=%s", (usernameTxt, usernameTxt))

        #validation
        inviteValid = True
        if usernameTxt == currentUsername: #can't invite themselves
            inviteValid = False
            Info1.message = "invalid invite - you can't invite yourself"
            Factory.Info1().open()
        for invite in self.invites: #can't invite people they've already invited
            if invite[1] == usernameTxt:
                inviteValid = False
                Info1.message = "invalid invite - user has already been invited to this event"
                Factory.Info1().open()
        if cursor.rowcount == 0:
            inviteValid = False
            Info1.message = "invalid invite - user does not exist"
            Factory.Info1().open()

        if inviteValid == True:
            for cursorRow in cursor: #should only be one row in cursor
                if usernameTxt != cursorRow[0]: #compares to selected username to ensure it is case-sensitive
                    inviteValid = False
                    Info1.message = "invalid invite - user does not exist\n\n(usernames are case-sensitive)"
                    Factory.Info1().open()
                else:
                    invRow = BoxLayout(orientation="horizontal",
                                       padding=0,
                                       height=self.height*0.1,
                                       size_hint=(1, None))
                    nameBox = BoxLayout(orientation="vertical",
                                        spacing=0,
                                        size_hint=(0.75, None),
                                        height=self.height*0.1)
                    dispNameLbl = Label(text=cursorRow[1],
                                        halign="left",
                                        color=(0, 0, 0, 1),
                                        font_size=(self.height*0.04),
                                        size_hint=(None, 0.67))
                    dispNameLbl.bind(texture_size=dispNameLbl.setter('size')) #needed to align to the left

                    uNameLbl = Label(text=usernameTxt,
                                     halign="left",
                                     color=(0.5, 0.5, 0.5, 1),
                                     font_size=(self.height*0.03),
                                     size_hint=(None, 0.33))
                    uNameLbl.bind(texture_size=uNameLbl.setter('size'))

                    deleteFloat=FloatLayout(size_hint=(0.17, None),
                                            height=self.height*0.08,
                                            pos_hint={"x": 0, "top": 1})
                    deleteBtn=IconButton(size_hint=(1, 1),
                                         pos_hint={"x": 0.2, "top": 0.8},
                                         on_release=lambda *args: self.deleteInvite(invRow, usernameTxt, *args))
                    deleteImg=Image(source="images/del1.png",
                                    size_hint=(1, 1),
                                    pos_hint={"x": 0.2, "top": 0.8})
                   
                    deleteFloat.add_widget(deleteBtn)
                    deleteFloat.add_widget(deleteImg)
                    nameBox.add_widget(dispNameLbl)
                    nameBox.add_widget(uNameLbl)

                    invRow.add_widget(nameBox)
                    invRow.add_widget(deleteFloat)

                    self.box.remove_widget(self.createBtnContainer)
                    self.box.add_widget(invRow)
                    self.box.add_widget(self.createBtnContainer)

                    self.invites.append((invRow, usernameTxt))

                    if usernameObj != None:
                        usernameObj.text = ""
           
    def createSend(self, link, btn):
        #finishes process of creating an event and sends out invitations
        global currentEvent
        currentEvent.invites = []
        for invite in self.invites:
            currentEvent.invites.append(invite[1])
            self.box.remove_widget(invite[0])
        currentEvent.link = link

        linkGen = currentEvent.addEvent()
        if int(linkGen) != -1:
            if link == True:
                Info1.message = "Your event link is:\n" + str(linkGen)
                Factory.Info1().open()
            self.send = True
            self.manager.current="createeventdetails"

    def deleteInvite(self, row, username, btn):
        self.box.remove_widget(row)
        self.invites.remove((row, username))

    def on_leave(self):
        #saves to currentEvent so they can go back to change details without losing invites
        global currentEvent
        if self.send == False:
            currentEvent.invites = []
            for invite in self.invites:
                currentEvent.invites.append(invite[1])
            else:
                self.send = False

class JoinInvitations(Screen):
    #Allows user to type in the event link that the creator has generated and displays list of invites they have yet to respond to.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        global currentUsername
       
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.05),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        linkRel = RelativeLayout(size_hint=(1, None),
                                 height=self.height*0.08)
        linkLbl = Label(text="ENTER LINK",
                        color=(0.5, 0.5, 0.5, 1),
                        height=self.height*0.08,
                        size_hint=(1, 1),
                        font_size=self.height*0.04)

        linkRel.add_widget(linkLbl)

        with linkRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (linkLbl.pos[1]+(linkRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.36), linkRel.height),
                      pos=((self.size[0]*0.28), (linkLbl.pos[1])))

        enterLinkLbl = Label(text="enter invite link",
                             color=(0, 0, 0, 1),
                             size_hint=(1, None),
                             height=self.height*0.072)

        searchRow = BoxLayout(orientation="horizontal",
                              spacing=0,
                              padding=0,
                              size_hint=(1, None),
                              height=self.height*0.071)

        linkSearch = TextInput1(size_hint=(0.8, 1),
                                on_text_validate=lambda *args: self.linkJoin(linkSearch.text, *args)) #pressing enter is same as pressing button
        joinBtn = Button1(text="join",
                          size_hint=(0.2, 1),
                          on_release=lambda *args: self.linkJoin(linkSearch.text, *args))

        searchRow.add_widget(linkSearch)
        searchRow.add_widget(joinBtn)
        self.box.add_widget(linkRel)
        self.box.add_widget(enterLinkLbl)
        self.box.add_widget(searchRow)

        newRel = RelativeLayout(size_hint=(1, None),
                                height=self.height*0.08)
        newLbl = Label(text="NEW INVITATIONS",
                       color=(0.5, 0.5, 0.5, 1),
                       height=self.height*0.08,
                       size_hint=(1, 1),
                       font_size=self.height*0.04)
        newRel.add_widget(newLbl)
        with newRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (newLbl.pos[1]+(newRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.48), newRel.height),
                      pos=((self.size[0]*0.22), (newLbl.pos[1])))

        pendingRel = RelativeLayout(size_hint=(1, None),
                                   height=self.height*0.08)
        pendingLbl = Label(text="PENDING",
                           color=(0.5, 0.5, 0.5, 1),
                           height=self.height*0.08,
                           size_hint=(1, 1),
                           font_size=self.height*0.04)
        pendingRel.add_widget(pendingLbl)
        with pendingRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (pendingLbl.pos[1]+(pendingRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.30), pendingRel.height),
                      pos=((self.size[0]*0.31), (pendingLbl.pos[1])))

        sv = ScrollView(size_hint=(1, 0.79),
                        pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        listEmpty = True

        cursor.execute("SELECT eventID FROM tblinvitations WHERE invitee=%s AND viewed=%s", (currentUsername, 0))
        if cursor.rowcount != 0:
            self.box.add_widget(newRel)
            listEmpty=False
            events = []
            for cursorRow in cursor:
                events.append(cursorRow[0])
               
            for event in reversed(events):
                self.displayInvite(event, False)
           
        cursor.execute("SELECT eventID FROM tblinvitations WHERE invitee=%s AND viewed=%s", (currentUsername, 1))
        if cursor.rowcount != 0:
            self.box.add_widget(pendingRel)
            listEmpty = False
            events = []
            for cursorRow in cursor:
                events.append(cursorRow[0])
               
            for event in reversed(events):
                self.displayInvite(event, True)

        if listEmpty == True:
            emptyLbl = Label(color=(0.5, 0.5, 0.5, 1),
                             text="no invitations\nto display",
                             halign="center",
                             size_hint=(1, None),
                             font_size=self.height*0.045,
                             height=self.height*0.09)
            self.box.add_widget(emptyLbl)

    def linkJoin(self, eventID, viewed):
        #checks that the event link is valid then adds an invite to the database and responds to the event
        global currentUsername
        cursor.execute("SELECT creator FROM tblevents WHERE eventID=%s OR eventID=%s", (eventID, eventID))
        if cursor.rowcount == 0:
            Info1.message = "the event you are trying to join does not exist"
            Factory.Info1().open()
        else:
            for cursorRow in cursor:
                creator = cursorRow[0]
            if creator == currentUsername:
                Info1.message = "you can't join an event that you created"
                Factory.Info1().open()
            else:
                cursor.execute("SELECT viewed FROM tblinvitations WHERE eventID=%s AND invitee=%s AND viewed!=%s", (eventID, currentUsername, 3))
                if cursor.rowcount == 0:
                    cursor.execute("INSERT INTO tblinvitations "
                                   "(eventID, invitee, viewed) "
                                   "VALUES (%s, %s, %s)", (eventID, currentUsername, 1))
                    self.respond(eventID)
                else:
                    Info1.message = "you have already joined this event"
                    Factory.Info1().open()

    def displayInvite(self, eventID, viewed):
        #searches for event name and creator then displays it with respond + decline buttons
        cursor.execute("SELECT eventName, creator FROM tblevents WHERE eventID=%s OR eventID=%s", (eventID, eventID))
        for cursorRow in cursor:
            invRow = BoxLayout(orientation="horizontal",
                               padding=0,
                               spacing=self.size[0]*0.01,
                               height=self.height*0.1,
                               size_hint=(1, None))
           
            nameBox = BoxLayout(orientation="vertical",
                                spacing=0,
                                size_hint=(0.5, None),
                                height=self.height*0.1)
            eventNameLbl = Label(text=cursorRow[0],
                                 halign="left",
                                 color=(0, 0, 0, 1),
                                 font_size=(self.height*0.035),
                                 size_hint=(None, 0.67))
            eventNameLbl.bind(texture_size=eventNameLbl.setter('size')) #needed to align to the left

            uNameLbl = Label(text=cursorRow[1],
                             halign="left",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=(self.height*0.03),
                             size_hint=(None, 0.33))
            uNameLbl.bind(texture_size=uNameLbl.setter('size'))

            if viewed == False:
                respBtn = Button1()
                declBtn = Button1grey()
            else:
                respBtn = Button1grey()
                declBtn = Button1red()
            respBtn.text = "respond"
            respBtn.size_hint = (0.24, None)
            respBtn.height = self.height * 0.08
            respBtn.font_size = self.height*0.035
            respBtn.on_release = lambda *args: self.respond(eventID, *args)
           
            declBtn.text = "decline"
            declBtn.size_hint = (0.24, None)
            declBtn.height = self.height * 0.08
            declBtn.font_size = self.height*0.035
            declBtn.on_release = lambda *args: self.declineInvitation(eventID, invRow, *args)
           
            nameBox.add_widget(eventNameLbl)
            nameBox.add_widget(uNameLbl)

            invRow.add_widget(nameBox)
            invRow.add_widget(respBtn)
            invRow.add_widget(declBtn)

            self.box.add_widget(invRow)

    def declineInvitation(self, eventID, row):
        #updates database to show that user has declined the invite
        global currentUsername
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #add to update table so creator can be notified
        cursor.execute("INSERT INTO tbleventupdates "
                       "(eventID, invitee, updateCode, updateTime) "
                       "VALUES (%s, %s, %s, %s)", (eventID, currentUsername, 0, timestamp))

        cursor.execute("UPDATE tblinvitations SET viewed=3 WHERE eventID=%s AND invitee=%s", (eventID, currentUsername))
        mydb.commit()

        self.box.remove_widget(row)
        self.on_enter()

    def respond(self, eventID):
        JoinDetails.eventID = eventID
        self.manager.current="joindetails"

class JoinDetails(Screen):
    #Displays details of the selected event to join, then has options to respond by adding their availability or decline the invitation.
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        global currentUsername
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        sv = ScrollView(size_hint=(1, 0.66),
                             pos_hint={"x": 0, "top": 1})
        sv.add_widget(self.box)
        self.add_widget(sv)

        cursor.execute("UPDATE tblinvitations SET viewed=%s WHERE eventID=%s AND invitee=%s", (1, self.eventID, currentUsername))
        mydb.commit()
       
        cursor.execute("SELECT eventName, creator, description, locationName, locationDescription, tag1, tag2, tag3, pollID FROM tblevents WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))

        for cursorRow in cursor:
            eventName = cursorRow[0]
            creator = cursorRow[1]
            description = cursorRow[2]
            locationName = cursorRow[3]
            locationDescription = cursorRow[4]
            tag1 = cursorRow[5]
            tag2 = cursorRow[6]
            tag3 = cursorRow[7]
            pollID = cursorRow[8]

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)                        

        nameLbl = Label(text=eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)
        createdLbl = Label(text=("created by " + creator),
                           color=(0.5, 0.5, 0.5, 1),
                           font_size=(self.height*0.035),
                           text_size=(self.size[0]*0.92, self.height*0.04), #needed to align to top and center
                           valign="top",
                           halign="center",
                           size_hint=(1, None),
                           height=self.height*0.04)
        descBox=TextInput2(text=description,
                               disabled=True,
                               size_hint=(1, None),
                               height=self.height*0.14)

        tags = False
        if tag1 != "" or tag2 != "" or tag3 != "": #if tags have been entered
            tags = True
            tagRow = GridLayout(rows=1,
                                cols=3,
                                col_default_width=self.size[0]*0.33,
                                col_force_default=True,
                                size_hint=(1, None),
                                height=self.height*0.04,
                                spacing=self.size[0]*0.02)
            tag1Lbl = Label(text=tag1)
            tag2Lbl = Label(text=tag2)
            tag3Lbl = Label(text=tag3)
            for tagLbl in (tag1Lbl, tag2Lbl, tag3Lbl):
                tagLbl.color = (0.50, 0.76, 0.86, 1)
                tagLbl.size_hint=(None, 1)
                tagLbl.font_size=self.height*0.03
                tagLbl.halign="left"
                tagLbl.bind(texture_size=tagLbl.setter('size'))
                tagRow.add_widget(tagLbl)

        locationLbl = Label(text=("Location: " + locationName),
                            color=(0.5, 0.5, 0.5, 1),
                            font_size=(self.height*0.035),
                            text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                            valign="bottom",
                            halign="left",
                            size_hint=(1, None),
                            height=self.height*0.06)
        descBtn = Button1grey(text="view location details",
                              size_hint=(0.6, None),
                              height=self.height*0.08,
                              font_size=self.height*0.05,
                              on_release=lambda *args: self.viewDesc(locationDescription, *args))

        datesRel = RelativeLayout(size_hint=(1, None),
                                  height=self.height*0.08)
        datesLbl = Label(text="DATES",
                         color=(0.5, 0.5, 0.5, 1),
                         height=self.height*0.08,
                         size_hint=(1, 1),
                         font_size=self.height*0.04)
        datesRel.add_widget(datesLbl)
        with datesRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (datesLbl.pos[1]+(datesRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.20), datesRel.height),
                      pos=((self.size[0]*0.36), (datesLbl.pos[1])))

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)
        self.box.add_widget(createdLbl)
        if description != "":
            self.box.add_widget(descBox)
        if tags == True:
            self.box.add_widget(tagRow)
        if locationName != "":
            self.box.add_widget(locationLbl)

        if locationDescription != "":
            self.box.add_widget(descBtn)

        self.box.add_widget(datesRel)

        #display dates and times
        cursor.execute("SELECT date, startTime, endTime FROM tbldatetime WHERE eventID=%s OR eventID=%s", (self.eventID, self.eventID))
        dates = []
        dateTimes = []
        for cursorRow in cursor:
            date = cursorRow[0]
            time1 = cursorRow[1]
            time2 = cursorRow[2]
            if time1 == None:
                times = "all day"
            else:
                times = time1 + "-" + time2

            if date not in dates:
                dates.append(date)
                dateTimes.append([date, [times]])
            else:
                for dt in dateTimes:
                    if date == dt[0]:
                        dt[1].append(times)

        for dt in dateTimes:
            dtBox = BoxLayout(orientation="vertical",
                              spacing=0,
                              size_hint=(0.55, None),
                              height=self.height*0.1)
            dateLbl = Label(text=dateToText(dt[0]),
                            halign="left",
                            color=(0, 0, 0, 1),
                            font_size=(self.height*0.04),
                            size_hint=(None, 0.67))
            dateLbl.bind(texture_size=dateLbl.setter('size')) #needed to align to the left

            timesText = ""
            for time in dt[1]:
                timesText = timesText + time + ", "

            timesText = timesText[:-2] #cuts off the last ", " characters

            timesLbl = Label(text=timesText,
                             halign="left",
                             color=(0.5, 0.5, 0.5, 1),
                             font_size=(self.height*0.03),
                             size_hint=(None, 0.33))
            timesLbl.bind(texture_size=timesLbl.setter('size'))

            dtBox.add_widget(dateLbl)
            dtBox.add_widget(timesLbl)

            self.box.add_widget(dtBox)

        inputBtn = Button1(text="input availability",
                           font_size=self.height*0.06,
                           size_hint=(0.44, 0.083),
                           pos_hint={"x": 0.043, "top": 0.31},
                           on_release=lambda *args: self.availability(self.eventID, eventName, dateTimes, *args))

        declBtn = Button1grey(text="decline invitation",
                              font_size=self.height*0.06,
                              size_hint=(0.44, 0.083),
                              pos_hint={"x": 0.52, "top": 0.31},
                              on_release=lambda *args: self.declineInvitation(self.eventID, *args))
        self.add_widget(inputBtn)
        self.add_widget(declBtn)

    def viewDesc(self, description, btn):
        Info1.message = description
        Factory.Info1().open()

    def availability(self, eventID, eventName, dateTimes, btn):
        JoinAvailability.eventID = eventID
        JoinAvailability.eventName = eventName
        JoinAvailability.dateTimes = dateTimes
        self.manager.current="joinavailability"

    def declineInvitation(self, eventID, btn):
        global currentUsername
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #add to update table so creator can be notified
        cursor.execute("INSERT INTO tbleventupdates "
                       "(eventID, invitee, updateCode, updateTime) "
                       "VALUES (%s, %s, %s, %s)", (eventID, currentUsername, 0, timestamp))

        #remove invitation so it will no longer be displayed to the invitee who has declined it        
        cursor.execute("DELETE FROM tblinvitations WHERE eventID=%s AND invitee=%s", (eventID, currentUsername))
        mydb.commit()
        self.manager.current="joininvitations"

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="joininvitations"
        self.manager.transition.duration = 0

class JoinAvailability(Screen):
    #Users that are responding to an invitation input their availability (‘yes’, ‘no’, ‘maybe’) for each of the date/time options.
    dateTimes = ObjectProperty(None)
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.025,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        self.sv = ScrollView(size_hint=(1, 0.8),
                             pos_hint={"x": 0, "top": 1})
        self.sv.add_widget(self.box)
        self.add_widget(self.sv)

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)

        nameLbl = Label(text=self.eventName,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.05),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        submitBtn = Button1(size_hint=(1, None),
                            height=self.height*0.07,
                            font_size=self.height*0.06,
                            on_release=self.submitBtn)

        cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            pollID = cursorRow[0]
        if pollID == None:
            submitBtn.text = "submit and join event"
        else:
            submitBtn.text = "submit availability"

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        self.boxes = []
        for date in self.dateTimes:
            self.addDate(date)

        self.box.add_widget(submitBtn)

    def back(self, btn):
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="joindetails"
        self.manager.transition.duration = 0

    def addDate(self, date):
        #adds date text and heading labels for the row
        #note date is an array with 2 elements: the date and then an array of all the times
        dateRow = BoxLayout(orientation="horizontal",
                            spacing=self.size[0]*0.05,
                            size_hint=(1, None),
                            height=self.height*0.1)

        dateLbl = Label(text=dateToText(date[0]),
                        color=(0.15, 0.22, 0.28, 1),
                        size_hint=(0.55, None),
                        height=self.height*0.072,
                        font_size=self.height*0.042)

        noLbl = Label(text="no",
                      color=(1, 0.36, 0.41, 1),
                      size_hint=(0.1, None),
                      font_size=self.height*0.03,
                      height=self.height*0.072)

        maybeLbl = Label(text="maybe",
                         color=(0.5, 0.5, 0.5, 10),
                         size_hint=(0.1, None),
                         font_size=self.height*0.03,
                         height=self.height*0.072)

        yesLbl = Label(text="yes",
                       color=(0.46, 0.74, 0.65, 1),
                       size_hint=(0.1, None),
                       font_size=self.height*0.03,
                       height=self.height*0.072)

        for obj in (dateLbl, noLbl, maybeLbl, yesLbl):
            dateRow.add_widget(obj)

        self.box.add_widget(dateRow)

        for time in date[1]:
            self.addTimeRow(time)

    def addTimeRow(self, time):
        #adds time text and checkbox buttons
        timeRow = BoxLayout(orientation="horizontal",
                            spacing=self.size[0]*0.05,
                            size_hint=(1, None),
                            height=self.height*0.05)
                           
        timeLbl = Label(text=time,
                        color=(0, 0, 0, 1),
                        size_hint=(0.55, None),
                        height=self.height*0.045,
                        font_size=self.height*0.036)

        noFloat = FloatLayout(size_hint=(0.1, None),
                              height=self.height*0.045)
        noBtn = IconButton(size_hint=(1, None),
                           height=self.height*0.045,
                           pos_hint={"x": 0, "top": 1})
        noImg = Image(source="images/ynmblank.png",
                      size_hint=(1, None),
                      height=self.height*0.045,
                      pos_hint={"x": 0, "top": 1})
        noFloat.add_widget(noBtn)
        noFloat.add_widget(noImg)

        maybeFloat = FloatLayout(size_hint=(0.1, None),
                                 height=self.height*0.045)
        maybeBtn = IconButton(size_hint=(1, None),
                              height=self.height*0.045,
                              pos_hint={"x": 0, "top": 1})
        maybeImg = Image(source="images/ynmblank.png",
                         size_hint=(1, None),
                         height=self.height*0.045,
                         pos_hint={"x": 0, "top": 1})
        maybeFloat.add_widget(maybeBtn)
        maybeFloat.add_widget(maybeImg)

        yesFloat = FloatLayout(size_hint=(0.1, None),
                               height=self.height*0.045)
        yesBtn = IconButton(size_hint=(1, None),
                            height=self.height*0.045,
                            pos_hint={"x": 0, "top": 1})
        yesImg = Image(source="images/ynmblank.png",
                       size_hint=(1, None),
                       height=self.height*0.045,
                       pos_hint={"x": 0, "top": 1})
        yesFloat.add_widget(yesBtn)
        yesFloat.add_widget(yesImg)

        noBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "N", *args)
        maybeBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "M", *args)
        yesBtn.on_release=lambda *args: self.boxPressed(noImg, maybeImg, yesImg, "Y", *args)

        for obj in (timeLbl, noFloat, maybeFloat, yesFloat):
            timeRow.add_widget(obj)

        self.box.add_widget(timeRow)

        self.boxes.append((noImg, maybeImg, yesImg))

    def boxPressed(self, noImg, maybeImg, yesImg, pressed):
        #selects 'pressed' box and deselects the other boxes by changing image sources
        noImg.source = "images/ynmblank.png"
        maybeImg.source = "images/ynmblank.png"
        yesImg.source = "images/ynmblank.png"

        if pressed == "N":
            noImg.source = "images/ynmno.png"
        elif pressed == "M":
            maybeImg.source = "images/ynmmaybe.png"
        else:
            yesImg.source = "images/ynmyes.png"

    def submitBtn(self, btn):
        #validates that availability has been entered for each row then adds availability to the MySQL database
        global currentUsername

        valid = True
        for row in self.boxes: #check there are no rows where no option is ticked
            if row[0].source == "images/ynmblank.png" and row[1].source == "images/ynmblank.png" and row[2].source == "images/ynmblank.png":
                self.notEntered()
                valid = False

        if valid == True:
            cursor.execute("SELECT invitationID FROM tblinvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
            for cursorRow in cursor:
                inviteID = cursorRow[0]
           
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #add to update table so creator can be notified
            cursor.execute("INSERT INTO tbleventupdates "
                           "(eventID, invitee, updateCode, updateTime) "
                           "VALUES (%s, %s, %s, %s)", (self.eventID, currentUsername, 1, timestamp))
            cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE eventID=%s AND invitationID=%s", (self.eventID, inviteID))
            mydb.commit()

            availability = [] #list of all availability in order by date displayed
            for i in self.boxes:
                for j in i:
                    if j.source != "images/ynmblank.png":
                        if j.source == "images/ynmno.png":
                            avail = "N"
                        elif j.source == "images/ynmmaybe.png":
                            avail = "M"
                        else:
                            avail = "Y"
                        availability.append(avail)

            i = 0
            for dateRow in self.dateTimes:
                for times in dateRow[1]:
                    if times == "all day":
                        t1 = None
                        t2 = None
                    else:
                        t1 = times[:5] #selects startTime (both startTime and endTime must be 5 chars)
                        t2 = times[6:] #selects endTime (ignores the '-' between them)
                   
                    if t1 == None: #no need to check both t1 and t2 as it can only be None if endTime is also null
                        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime IS NULL", (self.eventID, dateRow[0]))
                    else:
                        cursor.execute("SELECT dateTimeID FROM tbldatetime WHERE eventID=%s AND date=%s and startTime=%s and endTime=%s", (self.eventID, dateRow[0], t1, t2))
                    for cursorRow in cursor:
                        dtID = cursorRow[0]

                    cursor.execute("INSERT INTO tblavailability "
                                   "(invitationID, dateTimeID, availability) "
                                   "VALUES (%s, %s, %s)", (inviteID, dtID, availability[i]))
                    mydb.commit()
                    i += 1

            cursor.execute("SELECT pollID FROM tblevents WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
            for cursorRow in cursor:
                pollID = cursorRow[0]

            if pollID == None:
                self.manager.current="joininvitations"
                #4viewed = 4 means they have responded to the invitation so it will not be displayed as a new invite and have viewed all updates so new ones will not be displayed
                #4cursor.execute("UPDATE tblinvitations SET viewed=4 WHERE invitationID=%s AND invitationID=%s", (inviteID, inviteID))
                cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE invitationID=%s AND invitationID=%s", (inviteID, inviteID))

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE tblinvitations SET viewedTime=%s WHERE invitationID=%s", (timestamp, inviteID)) #change viewedTime so they will not be shown the updates they have just viewed

                #4cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE eventID=%s AND viewed=%s", (self.eventID, 4))
                
            else:
                JoinVote.pollID = pollID
                JoinVote.eventName = self.eventName
                JoinVote.eventID = self.eventID
                self.manager.current="joinvote"

    def notEntered(self):
        message = "you must enter your availability for all dates and times"
        Info1.message = message
        Factory.Info1().open()

class JoinVote(Screen):
    #Users that are responding to an invitation and have entered their availability can vote on the poll
    def on_enter(self):
        try:
            self.box.clear_widgets()
        except:
            pass

        cursor.execute("SELECT title FROM tblpolls WHERE pollID=%s AND pollID=%s", (self.pollID, self.pollID))
        for cursorRow in cursor:
            pollTitle = cursorRow[0]

        options = []
        cursor.execute("SELECT optionText FROM tblpolloptions WHERE pollID=%s OR pollID=%s ORDER BY optionNo", (self.pollID, self.pollID))
        for cursorRow in cursor:
            options.append(cursorRow[0])
     
        self.box = BoxLayout(orientation="vertical",
                             spacing=self.height*0.04,
                             padding=[(self.size[0]*0.04),(self.height*0.015),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter("height"))

        self.sv = ScrollView(size_hint=(1, 0.8),
                             pos_hint={"x": 0, "top": 1})
        self.sv.add_widget(self.box)
        self.add_widget(self.sv)

        backBtn = Button2(text="< back",
                          color=(0.15, 0.22, 0.28, 1),
                          size_hint=(0.24, None),
                          height=self.height*0.072,
                          on_release=self.back)

        nameLbl = Label(text="[color=#7f7f7f]POLL:" "[/color] [color=#7fc1db]" + pollTitle + "[/color]",
                        markup=True,
                        color=(0, 0, 0, 1),
                        font_size=(self.height*0.035),
                        text_size=(self.size[0]*0.92, self.height*0.06), #needed to align to top and center
                        valign="middle",
                        halign="center",
                        size_hint=(1, None),
                        height=self.height*0.06)

        submitBtn = Button1(text="vote and join event",
                            size_hint=(1, None),
                            height=self.height*0.1,
                            font_size=self.height*0.07,
                            on_release=self.submitBtn)

        self.box.add_widget(backBtn)
        self.box.add_widget(nameLbl)

        self.optionImgs = []

        #display options
        for option in options:
            self.displayOption(option)

        self.box.add_widget(submitBtn)

    def displayOption(self, option):
        #adds the text for the poll to the screen along with the vote checkbox
        optionFloat = FloatLayout(size_hint=(1, None),
                                  height=self.height*0.06)
        optionBtn = IconButton(size_hint=(1, 1),
                               pos_hint={"x": 0, "top": 1})
        optionLbl = Label(text=option,
                          halign="left",
                          font_size=(self.height*0.042),
                          pos_hint={"x": 0.22, "top": 1},
                          color=(0, 0, 0, 1),
                          size_hint=(None, 1))
        optionLbl.bind(texture_size=optionLbl.setter('size')) #needed to align to the left
        optionImg = Image(source="images/unticked.png",
                          size_hint=(0.2, 1),
                          pos_hint={"x": 0, "top": 1})

        optionBtn.on_release = lambda *args: self.vote(optionImg, *args)
        optionFloat.add_widget(optionBtn)
        optionFloat.add_widget(optionLbl)
        optionFloat.add_widget(optionImg)
        self.box.add_widget(optionFloat)

        self.optionImgs.append(optionImg)

    def vote(self, img):
        #selects the box for the option pressed and deselects all the other checkboxes
        if img.source == "images/unticked.png":
            img.source = "images/ticked.png"
        else:
            img.source = "images/unticked.png"

        for optionImg in self.optionImgs: #unticks all other options
            if optionImg != img:
                optionImg.source = "images/unticked.png"

    def back(self, btn):
        #first delete entered availability if is going to changed/resubmitted
        cursor.execute("SELECT invitationID FROM tblinvitations WHERE eventID=%s AND invitee=%s", (self.eventID, currentUsername))
        for cursorRow in cursor:
            inviteID = cursorRow[0]
        cursor.execute("DELETE FROM tblavailability WHERE invitationID=%s AND invitationID=%s", (inviteID, inviteID))

        #then go back
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"
        self.manager.current="joinavailability"
        self.manager.transition.duration = 0

    def submitBtn(self, btn):
        #checks that an option has been selected then updates the MySQL database with the new vote
        optionNo = 0
        for i in range(0, len(self.optionImgs)): #checks which option has been selected
            if self.optionImgs[i].source == "images/ticked.png":
                optionNo = i + 1
        if optionNo == 0: #if no options have been selected
            message = "you must select an option to vote"
            Info1.message = message
            Factory.Info1().open()
        else:        
            global currentUsername

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #4cursor.execute("UPDATE tblinvitations SET viewed=4 WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID)) #event is now not a new update
            cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
            cursor.execute("UPDATE tblinvitations SET viewedTime=%s WHERE invitee=%s AND eventID=%s", (timestamp, currentUsername, self.eventID)) #change viewedTime so they will not be shown the updates they have just viewed
            
            #change viewed from 4 to 2 for other invitees that have responded so they will be notified of the update
            #4cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE eventID=%s AND viewed=%s", (self.eventID, 4))

            cursor.execute("SELECT invitationID FROM tblInvitations WHERE invitee=%s AND eventID=%s", (currentUsername, self.eventID))
            for row in cursor:
                inviteID = row[0]

            cursor.execute("INSERT INTO tblpollvotes "
                           "(pollID, invitationID, optionNo)"
                           "VALUES (%s, %s, %s)", (self.pollID, inviteID, optionNo))
            mydb.commit()

            self.manager.current="joininvitations"

class Profile(Screen):
    #Displays the details of the user currently logged in and allows them to update their display name, email and password

    #references to .kv TextInput objects
    username = ObjectProperty(None)
    displayName = ObjectProperty(None)
    email = ObjectProperty(None)
    password = ObjectProperty(None)
    passwordConf = ObjectProperty(None)
   
    def on_enter(self):
        global currentUsername
        self.username.text = currentUsername

        cursor.execute("SELECT displayName, email FROM tblaccounts WHERE username=%s OR username=%s", (currentUsername, currentUsername))
        for cursorRow in cursor:
            self.displayName.text = cursorRow[0]
            self.email.text = cursorRow[1]

    def saveChangesButton(self):
        #validates changed details and updates the database if they are valid
        cursor.execute("SELECT displayName, email FROM tblaccounts WHERE username=%s OR username=%s", (currentUsername, currentUsername))
        for cursorRow in cursor:
            nameSaved = cursorRow[0]
            emailSaved = cursorRow[1]
        if self.password.text == "":
            if nameSaved == self.displayName.text:
                if emailSaved == self.email.text:
                    Info1.message = "no changes were made"
                    Factory.Info1().open()
                else:
                    cursor.execute("UPDATE tblaccounts SET email=%s WHERE username=%s", (self.email.text, currentUsername))
                    mydb.commit()
                    Info1.message = "new email saved"
                    Factory.Info1().open()
            else:
                if emailSaved == self.email.text:
                    cursor.execute("UPDATE tblaccounts SET displayName=%s WHERE username=%s", (self.displayName.text, currentUsername))
                    mydb.commit()
                    Info1.message = "new display name saved"
                    Factory.Info1().open()
                else:
                    Info1.message = "you can only make one change at once"
                    Factory.Info1().open()
                    self.on_enter() #resets to fill with saved changes
        elif self.password.text == self.passwordConf.text:
            if nameSaved == self.displayName.text and emailSaved == self.email.text:
                salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
                pwdhash = hashlib.pbkdf2_hmac('sha512', self.password.text.encode('utf-8'),
                                              salt, 100000)
                pwdhash = binascii.hexlify(pwdhash)
                pwdToStore = (salt + pwdhash).decode('ascii')

                cursor.execute("UPDATE tblaccounts SET password=%s WHERE username=%s", (pwdToStore, currentUsername))
                mydb.commit()
                Info1.message = "new password saved"
                Factory.Info1().open()
                self.password.text = ""
                self.passwordConf.text = ""
            else:
                Info1.message = "you can only make one change at once"
                Factory.Info1().open()
                self.on_enter() #resets to fill with saved changes
        else:
            Info1.message = "passwords do not match"
            Factory.Info1().open()
            self.password.text = ""
            self.passwordConf.text = ""

    def signOut(self):
        #import global variables
        global currentUsername
        global currentEvent

        #change screen
        self.manager.current = "loadscreen"
        self.manager.transition.duration = 0.4
        self.manager.transition.direction = "right"

        #clear global variables
        currentUsername = ""
        currentEvent.__init__()

#popups
class Info1(ModalView):
    infoText = ObjectProperty(None)

    def on_open(self):
        self.infoText.text = self.message

class ModifyEvent(ModalView):
    #Change the details of a created event and update them in the database.
    eventname = ObjectProperty(None)
    description = ObjectProperty(None)
    def on_open(self):
        global currentEvent
        currentEvent.eventID = self.eventID
        currentEvent.autoFill()
        self.eventname.text = currentEvent.eventName
        self.description.text = currentEvent.description

    def save(self):
        global currentEvent
        currentEvent.eventName = self.eventname.text
        currentEvent.description = self.description.text
        currentEvent.changeDetails()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO tbleventupdates "
                       "(eventID, invitee, updateCode, updateTime) "
                       "VALUES (%s, %s, %s, %s)", (self.eventID, None, 4, timestamp))
        #4cursor.execute("UPDATE tblinvitations SET viewed=2 WHERE viewed=4") #sets status to show those who have joined that there are new updates

        mydb.commit()

        self.dismiss()
        Info1.message = "event details updated"
        Factory.Info1().open()

        currentEvent.eventName = ""
        currentEvent.description = ""

class ManageInvites(ModalView):
    #View, add and remove the invitees of a CREATED event.
    def on_open(self):
        self.send = False #changes to true invites have been sent so the on_leave function doesn't re-add the invites
       
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.025),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter('height'))

        manageRel = RelativeLayout(size_hint=(1, None),
                                   height=self.height*0.08)
        manageLbl = Label(text="MANAGE INVITATIONS",
                          color=(0.5, 0.5, 0.5, 1),
                          height=self.height*0.08,
                          size_hint=(1, 1),
                          font_size=self.height*0.04)

        manageRel.add_widget(manageLbl)

        with manageRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (manageLbl.pos[1]+(manageRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.6), manageRel.height),
                      pos=((self.size[0]*0.16), (manageLbl.pos[1])))

        self.box.add_widget(manageRel)

        self.manageBox = BoxLayout(orientation="vertical",
                                   spacing=(self.height*0.03),
                                   padding=0,
                                   size_hint=(1, None))
        self.manageBox.bind(minimum_height=self.manageBox.setter('height'))

        self.box.add_widget(self.manageBox)

        invIDs = []
        invites = []
        self.invites = []
        self.newInvites = []
        self.deletedInvites = []

        cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            invIDs.append(cursorRow[0])

        for invID in invIDs:
            cursor.execute("SELECT displayName FROM tblaccounts WHERE username=%s AND username=%s", (invID, invID))
            for cursorRow in cursor:
                name = cursorRow[0]

            cursor.execute("SELECT viewed FROM tblinvitations WHERE invitee=%s AND eventID=%s", (invID, self.eventID))
            for cursorRow in cursor:
                viewed = int(cursorRow[0])
                if viewed == 0 or viewed == 1:
                    status = "pending"
                    colour = (0.50, 0.76, 0.86, 1)
                #4elif viewed == 2 or viewed==4:
                elif viewed == 2:
                    status = "responded"
                    colour = (0.46, 0.74, 0.65, 1)
                elif viewed == 3:
                    status = "declined"
                    colour = (1, 0.36, 0.41, 1)

            invites.append((invID, name, status, colour))
            self.invites.append(invID)
           
        for invite in invites:
            self.displayInvite(invite[0], invite[1], invite[2], invite[3])

        box2 = BoxLayout(orientation="vertical",
                         spacing=(self.height*0.03),
                         padding=[(self.size[0]*0.04), (self.height*0.025), (self.size[0]*0.04), (self.height*0.025)],
                         size_hint=(1, 0.52))

        saveBtn = Button1(text="save and return",
                          font_size=self.height*0.035,
                          size_hint=(1, 0.24),
                          on_release=self.save)

        cancelBtn = Button2(text="Cancel",
                            size_hint=(1, 0.16),
                            on_release=self.dismiss)
             
        addRel = RelativeLayout(size_hint=(1, None),
                                height=self.height*0.08)
        addLbl = Label(text="ADD INVITEES",
                       color=(0.5, 0.5, 0.5, 1),
                       height=self.height*0.08,
                       size_hint=(1, 1),
                       font_size=self.height*0.04)

        addRel.add_widget(addLbl)

        with addRel.canvas.before:
            Color(0.50, 0.76, 0.86, 1)
            Rectangle(size=(self.size[0]*0.92, self.height*0.002),
                      pos=(0, (addLbl.pos[1]+(addRel.height/2))))
            Color(1, 1, 1, 1)
            Rectangle(size=((self.size[0]*0.48), addRel.height),
                      pos=((self.size[0]*0.22), (addLbl.pos[1])))

        enterUsnmLbl = Label(text="enter username",
                             color=(0, 0, 0, 1),
                             size_hint=(1, None),
                             height=self.height*0.072)
        searchRow = BoxLayout(orientation="horizontal",
                              spacing=0,
                              padding=0,
                              size_hint=(1, None),
                              height=self.height*0.071)
        usernameSearch = TextInput1(size_hint=(0.8, 1),
                                    on_text_validate=lambda *args: self.addInvite(usernameSearch.text, *args)) #pressing enter is same as pressing button
        inviteBtn = Button1(text="invite",
                            size_hint=(0.2, 1),
                            on_release=lambda *args: self.addInvite(usernameSearch.text, *args))
        searchRow.add_widget(usernameSearch)
        searchRow.add_widget(inviteBtn)

        box2.add_widget(addRel)
        box2.add_widget(enterUsnmLbl)
        box2.add_widget(searchRow)
        box2.add_widget(saveBtn)
        box2.add_widget(cancelBtn)

        sv = ScrollView(size_hint=(1, 0.48))
        sv.add_widget(self.box)

        bigBox = BoxLayout(orientation="vertical",
                           spacing=0,
                           padding=0,
                           size_hint=(1, 1))
        bigBox.add_widget(sv)
        bigBox.add_widget(box2)

        self.add_widget(bigBox)

    def addInvite(self, usernameTxt, btn):
        cursor.execute("SELECT username, displayName FROM tblaccounts WHERE username=%s OR username=%s", (usernameTxt, usernameTxt))

        #validation
        inviteValid = True
        if usernameTxt == currentUsername: #can't invite themselves
            inviteValid = False
            message = "invalid invite - you can't invite yourself"
        for invite in self.invites: #can't invite people they've already invited
            if invite == usernameTxt:
                inviteValid = False
                message = "invalid invite - user has already been invited to this event"
        if cursor.rowcount == 0:
            inviteValid = False
            message = "invalid invite - user does not exist"
        if inviteValid == True:
            for cursorRow in cursor: #should only be one row in cursor
                self.newInvites.append(usernameTxt)
                self.invites.append(usernameTxt)
                self.displayInvite(usernameTxt, cursorRow[0], "not sent", (0.50, 0.76, 0.86, 1))
        else:
            Info1.message = message
            Factory.Info1().open()

    def displayInvite(self, username, name, status, colour):
        invRow = BoxLayout(orientation="horizontal",
                           padding=0,
                           height=self.height*0.1,
                           size_hint=(1, None))
       
        nameBox = BoxLayout(orientation="vertical",
                            spacing=0,
                            size_hint=(0.75, None),
                            height=self.height*0.1)
        dispNameLbl = Label(text=name,
                            halign="left",
                            color=(0, 0, 0, 1),
                            font_size=(self.height*0.04),
                            size_hint=(None, 0.67))
        dispNameLbl.bind(texture_size=dispNameLbl.setter('size')) #needed to align to the left

        statusLbl = Label(text=status,
                          halign="left",
                          color=colour,
                          font_size=(self.height*0.03),
                          size_hint=(None, 0.33))
        statusLbl.bind(texture_size=statusLbl.setter('size'))

        deleteFloat=FloatLayout(size_hint=(0.17, None),
                                height=self.height*0.08,
                                pos_hint={"x": 0, "top": 1})
        deleteBtn=IconButton(size_hint=(1, 1),
                             pos_hint={"x": 0.2, "top": 0.8},
                             on_release=lambda *args: self.deleteInvite(invRow, username, *args))
        deleteImg=Image(source="images/del1.png",
                        size_hint=(1, 1),
                        pos_hint={"x": 0.2, "top": 0.8})

        deleteFloat.add_widget(deleteBtn)
        deleteFloat.add_widget(deleteImg)
        nameBox.add_widget(dispNameLbl)
        nameBox.add_widget(statusLbl)

        invRow.add_widget(nameBox)
        if status != "declined":
            invRow.add_widget(deleteFloat)

        self.manageBox.add_widget(invRow)

    def deleteInvite(self, row, username, btn):
        self.manageBox.remove_widget(row)
        self.deletedInvites.append(username)

    def save(self, btn):
        for invite in self.newInvites:
            cursor.execute("INSERT INTO tblinvitations "
                           "(eventID, invitee) "
                           "VALUES (%s, %s)", (self.eventID, invite))

        for invite in self.deletedInvites:
            #delete any saved availability
            cursor.execute("SELECT invitationID FROM tblinvitations WHERE eventID=%s AND invitee=%s", (self.eventID, invite))
            for cursorRow in cursor:
                cursor.execute("DELETE FROM tblpollvotes WHERE invitationID=%s AND invitationID=%s", (cursorRow[0], cursorRow[0]))
                cursor.execute("DELETE FROM tblavailability WHERE invitationID=%s AND invitationID=%s", (cursorRow[0], cursorRow[0]))
            cursor.execute("DELETE FROM tblinvitations WHERE eventID=%s AND invitee=%s", (self.eventID, invite))

        mydb.commit()
        self.dismiss()

class SeeInvitees(ModalView):
    #View invitees of a JOINED event - user can't add or remove invites
    def on_open(self):
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.03),
                             padding=[(self.size[0]*0.04),(self.height*0.025),(self.size[0]*0.04),(self.height*0.025)],
                             size_hint=(1, None))
        self.box.bind(minimum_height=self.box.setter('height'))

        invIDs = []
        invites = []
        self.invites = []

        cursor.execute("SELECT invitee FROM tblinvitations WHERE eventID=%s AND eventID=%s", (self.eventID, self.eventID))
        for cursorRow in cursor:
            invIDs.append(cursorRow[0])

        for invID in invIDs:
            cursor.execute("SELECT displayName FROM tblaccounts WHERE username=%s AND username=%s", (invID, invID))
            for cursorRow in cursor:
                name = cursorRow[0]

            cursor.execute("SELECT viewed FROM tblinvitations WHERE invitee=%s AND eventID=%s", (invID, self.eventID))
            for cursorRow in cursor:
                viewed = int(cursorRow[0])
                if viewed == 0 or viewed == 1:
                    status = "pending"
                    colour = (0.50, 0.76, 0.86, 1)
                #4elif viewed == 2 or viewed == 4:
                elif viewed == 2:
                    status = "responded"
                    colour = (0.46, 0.74, 0.65, 1)
                elif viewed == 3:
                    status = "declined"
                    color = (1, 0.36, 0.41, 1)

            invites.append((invID, name, status, colour))
           
        for invite in invites:
            self.displayInvite(invite[0], invite[1], invite[2], invite[3])

        backBtn = Button1grey(text="return to event",
                              font_size=self.height*0.035,
                              size_hint=(1, None),
                              height=self.height*0.08,
                              on_release=self.dismiss)

        sv = ScrollView(size_hint=(1, 0.9))
        sv.add_widget(self.box)

        bigBox = BoxLayout(orientation="vertical",
                           spacing=0,
                           padding=[self.size[0]*0.04, self.height*0.02, self.size[0]*0.04, self.height*0.04],
                           size_hint=(1, 1))
        bigBox.add_widget(sv)
        bigBox.add_widget(backBtn)

        self.add_widget(bigBox)

    def displayInvite(self, username, name, status, colour):
        invRow = BoxLayout(orientation="horizontal",
                           padding=0,
                           height=self.height*0.1,
                           size_hint=(1, None))
       
        nameBox = BoxLayout(orientation="vertical",
                            spacing=0,
                            size_hint=(1, None),
                            height=self.height*0.1)
        dispNameLbl = Label(text=name,
                            halign="left",
                            color=(0, 0, 0, 1),
                            font_size=(self.height*0.04),
                            size_hint=(None, 0.67))
        dispNameLbl.bind(texture_size=dispNameLbl.setter('size')) #needed to align to the left

        statusLbl = Label(text=status,
                          halign="left",
                          color=colour,
                          font_size=(self.height*0.03),
                          size_hint=(None, 0.33))
        statusLbl.bind(texture_size=statusLbl.setter('size'))

        nameBox.add_widget(dispNameLbl)
        nameBox.add_widget(statusLbl)

        invRow.add_widget(nameBox)
       
        self.box.add_widget(invRow)

class CreatePoll(ModalView):
    #Popup accessed from CreateEventDetails screen to add a poll
    def on_open(self):
        global currentEvent
        self.options = []
        self.box = BoxLayout(orientation="vertical",
                             spacing=(self.height*0.025),
                             padding=[(self.height*0.04),(self.height*0.05),(self.height*0.04),(self.height*0.025)])
       
        self.innerBox = BoxLayout(orientation="vertical",
                                  spacing=(self.height*0.025),
                                  size_hint_y=None)
        self.innerBox.bind(minimum_height=self.innerBox.setter("height"))

        titleLbl = Label(text="poll title",
                         color=(0, 0, 0, 1),
                         height=(self.height*0.1),
                         font_size=(self.height*0.05),
                         size_hint_y=None)
        self.titleInp = TextInput1(size_hint_y=None,
                                   height=(self.height*0.1),
                                   input_filter=lambda text, from_undo: text[:30-len(self.titleInp.text)]) #sets maximum character length to 30
        addBtn = Button1(text="add option",
                         size_hint_y=None,
                         height=(self.height*0.1),
                         on_release=lambda *args: self.addOption("", *args))

        createBtn = Button1(text="create poll",
                            size_hint=(1, 0.12),
                            on_release=self.createPoll)
        cancelBtn = Button2(text="Cancel",
                            size_hint=(1, 0.08),
                            on_release=self.dismiss)

        self.innerBox.add_widget(titleLbl)
        self.innerBox.add_widget(self.titleInp)
        self.innerBox.add_widget(addBtn)

        sv = ScrollView(size_hint=(1, 0.8))
        sv.add_widget(self.innerBox)

        self.box.add_widget(sv)
        self.box.add_widget(createBtn)
        self.box.add_widget(cancelBtn)
        self.add_widget(self.box)

        #autofill if poll already exists
        if currentEvent.pollTitle != "":
            self.titleInp.text = currentEvent.pollTitle
            for option in currentEvent.pollOptions:
                self.addOption(option, None)
               
    def addOption(self, autoText, btn):
        optionText = TextInput2(size_hint_y=None,
                                height=(self.height*0.075),
                                font_size=(self.height*0.04),
                                multiline=False,
                                write_tab=False,
                                text=autoText)
        optionText.focus = True
        self.options.append(optionText)
        self.innerBox.add_widget(optionText)
    def createPoll(self, btn):
        global currentEvent
        currentEvent.pollTitle = self.titleInp.text
        if len(self.options) > 1:
            for x in self.options:
                if x.text != "":
                    currentEvent.pollOptions.append(x.text)
            self.dismiss()

class CreateDescription(ModalView):
    #Popup accessed from CreateEventDetails screen to add event description
    description = ObjectProperty(None)

    def on_open(self):
        self.description.text = currentEvent.description

    def addDescriptionButton(self):
        currentEvent.description = self.description.text
        self.dismiss()

class CreateLocation(ModalView):
    #Popup accessed from CreateEventDetails screen to add location details
    location = ObjectProperty(None)
    details = ObjectProperty(None)

    def on_open(self):
        self.location.text = currentEvent.locationName
        self.details.text = currentEvent.locationDetails
   
    def addLocationButton(self):
        currentEvent.locationName = self.location.text
        currentEvent.locationDetails = self.details.text
        self.dismiss()

class CreateTags(ModalView):
    #Popup accessed from CreateEventDetails screen to add event tags
    tag1 = ObjectProperty(None)
    tag2 = ObjectProperty(None)
    tag3 = ObjectProperty(None)

    def on_open(self):
        self.tag1.text = currentEvent.tag1
        self.tag2.text = currentEvent.tag2
        self.tag3.text = currentEvent.tag3

    def addTagsButton(self):
        currentEvent.tag1 = self.tag1.text
        currentEvent.tag2 = self.tag2.text
        currentEvent.tag3 = self.tag3.text
        self.dismiss()

class MainApp(App): #builds the app
    def build(self):
        return

if __name__ == "__main__": #runs the app
    MainApp().run()
