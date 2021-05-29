# A Level Coursework
## Social Scheduling Python App
*Helps groups of people find an optimal time to meet up.*

### To run the app, set-up is a little complicated as I don't have a server:
* Use pip to install MySQL connector and Kivy.
* Download MySQL if you haven't already, and create a new database called 'appdata'.
* In the command line, where the project files are downloaded, type `mysql -u username -p appdata < schema.sql` to setup the database.
* You may need to change the password at the top of the *appcode.py* file.

**APP FEATURES:**
* Login and register
* Create an event, with optional description, tags, location 
* Optionally add a poll where you can ask a question connected to the event (e.g. preferences on what to eat) with options for invitees to vote on
* Add possible date and time options
* Invite other users - either with an invite link that can easily be shared via social media, or directly by entering their usernames
* Respond to events by inputting availability and voting on the poll
* View updates to created and joined events - the creator can see how many are left to respond, change some details and add or remove invitees
* The creator can see an overview of everyone's availability, with the app indicating optimal dates (top choice, most confirmed, least unavailable)
* The creator can also see a breakdown of who can attend before confirming the date
* Profile screen to change settings e.g. email and password
