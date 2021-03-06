import string
import urllib.parse

from flask import Flask, request, jsonify
import random
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from requests import post
from sqlalchemy import or_, func
from sqlalchemy import create_engine, or_


eventTypes = { 'Technical': 1, 'Cultural': 2, 'Lectures': 3, 'Workshops': 4, 'Shows': 5 }
categories = {
  "NATYAMANCH": 1,
  "NRITYAMANCH": 2,
  "LITERARY ARTS": 3,
  "SPEAKING ARTS": 4,
  "DIGITAL DESIGN ART": 5,
  "FINE ARTS": 6,
  "MUSICAL ARTS": 7,
  "ENTREPRENEURICAL ARTS": 8,
}

################################################################

app = Flask(__name__)
CORS(app)

# params = urllib.parse.quote_plus("Driver={ODBC Driver 13 for SQL Server};Server=tcp:pecfest-storage.database.windows.net,1433;Database=Pecfest;Uid=maverick@pecfest-storage;Pwd=Pecfest2018;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")
#
# app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# # For running on local host
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sql12246172:7FrjTFAlQ2@sql12.freemysqlhosting.net/sql12246172'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

################################################################

from models.model import pass_param

pass_param(db)

from models.event import Event
from models.Registration import Participant
from models.pecfestIds import PecfestIds
from models.otps import OTPs
from models.event_registration import EventRegistration
from models.sent_sms import SentSMS
from models.notifications import Notifications

################################################################

def genPecfestId(name, length=6):
  done=False
  proposedId = ''
  while not done:
    proposedId = name + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    alreadyId = PecfestIds.query.filter_by(pecfestId=proposedId).first()
    if alreadyId == None:
      break
  return proposedId

db.create_all()

################################################################
#####################EVENT MANAGEMENT###########################

# Create event
@app.route('/event/create', methods=['POST'])
def createEvent():
  data = request.get_json()

  name = data["name"]
  coordinators = data["coordinators"]
  location = data["location"] if "location" in data else ''
  day = data["day"] if "day" in data else 0
  time = data["time"] if "time" in data else "0"
  prize = data["prize"] if "prize" in data else "0"
  minSize = data["minSize"] if "minSize" in data else 1
  maxSize = data["maxSize"] if "maxSize" in data else 1
  eventType = eventTypes[data["eventType"]]
  category = categories[data["category"]]
  clubId = data["clubId"] if "clubId" in data else "PEC"
  details = data["details"] if "details" in data else ""
  shortDescription = data["shortDescription"] if "shortDescription" in data else ""
  imageUrl = data["imageUrl"] if "imageUrl" in data else ""
  rulesList = data["rulesList"] if "rulesList" in data else ""
  pdfUrl = data["pdfUrl"] if "pdfUrl" in data else ""

  event =  Event(name=name,
          coordinators=coordinators,
          location=location,
          day=day,
          time=time,
          prize=prize,
          minSize=minSize,
          maxSize=maxSize,
          eventType=eventType,
          category=category,
          clubId=clubId,
          details=details,
          shortDescription=shortDescription,
          imageUrl=imageUrl,
          rulesList=rulesList,
          pdfUrl=pdfUrl)

  curr_session = db.session
  success = False
  try:
    curr_session.add(event)
    curr_session.commit()
    success = True
  except Exception as err:
    curr_session.rollback()
    curr_session.flush()


  if success:
    return jsonify({'ACK': 'SUCCESS'})
  return jsonify({'ACK': 'FAILED'})

# Get event details
@app.route('/event/<int:eventId>', methods=['GET'])
def getEventDetails(eventId):

  eventInfo = {}
  event = Event.query.filter_by(eventId=eventId).first()

  if event == None:
    eventInfo["ACK"] = "FAILED"
    return jsonify(eventInfo)

  eventInfo["ACK"] = "SUCCESS"
  eventInfo["id"] = event.eventId
  eventInfo["name"] = event.name
  eventInfo["coordinators"] = event.coordinators
  eventInfo["location"] = event.location
  eventInfo["day"] = event.day
  eventInfo["time"] = event.time
  eventInfo["prize"] = event.prize
  eventInfo["minSize"] = event.minSize
  eventInfo["maxSize"] = event.maxSize
  eventInfo["eventType"] = event.eventType
  eventInfo["category"] = event.category
  eventInfo["clubId"] = event.clubId
  eventInfo["details"] = event.details
  eventInfo["shortDescription"] = event.shortDescription
  eventInfo["imageUrl"] = event.imageUrl
  eventInfo["rulesList"] = event.rulesList
  eventInfo["pdfUrl"] = event.pdfUrl

  return jsonify(eventInfo)


# Get event details
@app.route('/event/category/<int:eventCategory>', methods=['GET'])
def getEventFromCategory(eventCategory):

  eventsInfo = {}
  events = Event.query.filter_by(category=eventCategory)

  if events == None:
    eventsInfo["ACK"] = "FAILED"
    return jsonify(eventsInfo)

  eventsInfo["ACK"] = "SUCCESS"

  for event in events:
    eventInfo = {}

    eventInfo["id"] = event.eventId
    eventInfo["name"] = event.name
    eventInfo["coordinators"] = event.coordinators
    eventInfo["location"] = event.location
    eventInfo["day"] = event.day
    eventInfo["time"] = event.time
    eventInfo["prize"] = event.prize
    eventInfo["minSize"] = event.minSize
    eventInfo["maxSize"] = event.maxSize
    eventInfo["eventType"] = event.eventType
    eventInfo["category"] = event.category
    eventInfo["clubId"] = event.clubId
    eventInfo["details"] = event.details
    eventInfo["shortDescription"] = event.shortDescription
    eventInfo["imageUrl"] = event.imageUrl
    eventInfo["rulesList"] = event.rulesList
    eventInfo["pdfUrl"] = event.pdfUrl

    eventsInfo[event.name] = eventInfo

  return jsonify(eventsInfo)

################################################################
#####################USER INFO##################################

def sendOTP(name, mobile, otp):
  data = {}
  data['user'] = 'onlineteam.pecfest'
  data['password'] = 'onlinesms'
  data['sid'] = 'PECCHD'
  data['msisdn'] = '91' + mobile

  data['msg'] = "Hi " + name + "! Welcome to PECFEST, 2018. Your OTP is " + otp + ". Enter this OTP into the website/app to get your PECFEST ID. Happy participating!"
  data['gwid'] = 2
  data['fl'] = 2
  headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
  res = post('http://www.smslane.com//vendorsms/pushsms.aspx', data=data, headers=headers)
  if res.status_code is not 200:
    return False
  else:
    text = res.text
    if 'Message Id' in text:
      messageId = text.split(' : ')
      sms = SentSMS(smsId=messageId[1], mobile=mobile, smsType=1, status=1)
      otps = OTPs(mobile=mobile,otp=otp)
      session = db.session
      success = False
      try:
        session.add(sms)
        session.commit()
      except Exception as e:
        session.rollback()
        session.flush()
      try:
          session.add(otps)
          session.commit()
          success = True
      except Exception as e:
          session.rollback()
          session.flush()

      return True
    else:
      return False


# Create User
@app.route('/user/create', methods=['POST'])
def createUser():

    data = request.get_json()

    if data is None:
        return jsonify({'ACK': 'FAILED', 'message': 'Malformed Request'})

    firstName = data['firstName']
    lastName = data['lastName']
    pecfestId = genPecfestId(firstName[:4].strip().upper())
    college = data['college']
    email = data['email']
    mobile = data['mobile']
    gender = data['gender']
    password = data['password']

    accomodation = data['accomodation'] if "accomodation" in data else "no"
    verified = 0
    smsCounter = 0

    alreadyUser = db.session.query(Participant).filter(or_(Participant.emailId == email, Participant.mobileNumber == mobile)).first()
    if alreadyUser:
        if alreadyUser.verified == 1:
            return jsonify({'ACK': 'ALREADY', 'message': 'Phone number already registered.'})
        else:
            return jsonify({'ACK': 'ALREADY', 'message': 'Verifying phone number...'})

    user = Participant(pecfestId=pecfestId,
                       firstName=firstName,
                       lastName=lastName,
                       collegeName=college,
                       emailId=email,
                       mobileNumber=mobile,
                       gender=gender,
                       accomodation=accomodation,
                       verified=verified,
                       smsCounter=smsCounter)

    user.set_password(password)
    newPecfestId = PecfestIds(pecfestId=pecfestId)
    curr_session = db.session
    success = False
    try:
        curr_session.add(user)
        curr_session.add(newPecfestId)
        curr_session.commit()
        success = True
    except Exception as err:
        curr_session.rollback()
        curr_session.flush()

    if success:
        return jsonify({'ACK': 'SUCCESS'})
    return jsonify({'ACK': 'FAILED'})

# Get user's details
@app.route('/user/<string:pecfestId>', methods=['GET'])
def getUserDetails(pecfestId):
    userInfo = {}
    user = Participant.query.filter_by(pecfestId=pecfestId).first()

    if user == None:
        userInfo["ACK"] = "FAILED"
        return jsonify(userInfo)

    userInfo["ACK"] = "SUCCESS"
    userInfo["pecfestId"] = user.pecfestId
    userInfo["firstName"] = user.firstName
    userInfo["lastName"] = user.lastName
    userInfo["college"] = user.collegeName
    userInfo["gender"] = user.gender
    userInfo["mobileNumber"] = user.mobileNumber
    userInfo["emailId"] = user.emailId

    return jsonify(userInfo)


# verify user
@app.route('/user/verify', methods=['POST'])
def verifyUser():
  userInfo = {}
  json = request.get_json()
  o = json['otp']
  mobile = json['mobile']
  otp = OTPs.query.filter_by(mobile=mobile,
                otp=o).first()
  if otp:
    curr_session = db.session
    user = Participant.query.filter_by(mobileNumber=mobile).update(dict(verified=1))
    curr_session.commit()
    user = Participant.query.filter_by(mobileNumber=mobile).first()
    if user:
      success = False
      try:
        curr_session.delete(otp)
        curr_session.commit()
        success = True
      except:
        curr_session.rollback()
        curr_session.flush()


      if success:
        userInfo["ACK"] = "SUCCESS"
        userInfo["firstName"] = user.firstName
        userInfo["lastName"] = user.lastName
        userInfo["pecfestId"] = user.pecfestId
        userInfo["college"] = user.collegeName
        userInfo["gender"] = user.gender
        return jsonify(userInfo)
      else:
        return jsonify({'ACK': 'FAILED' })
    else:
      return jsonify({ 'ACK': 'FAILED' })
  else:
    return jsonify({'ACK': 'FAILED', 'message': 'Wrong OTP'})

@app.route('/user/signIn', methods=['POST'])
def signIn():
    auth = {}
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = db.session.query(Participant).filter(or_(Participant.emailId == username , Participant.mobileNumber == username)).first()

    if user:
        try:
            if (user.check_password(password)):
                auth["ACK"] = "SUCCESS"
                auth["pecfestId"] = user.pecfestId
                auth["firstName"] = user.firstName
                auth["lastName"] = user.lastName
                auth["collegeName"] = user.collegeName
                auth["emailId"] = user.emailId
                auth["mobileNumber"] = user.mobileNumber
                auth["gender"] = user.gender
            else:
                auth["ACK"] = "FAILED"
                auth["message"] = "WRONG USERNAME/PASSWORD"
        except:
            auth["ACK"] = "FAILED"
            auth["message"] = "Something wrong happened"
    else:
        auth["ACK"] = "FAILED"
        auth["message"] = "User doesnot exist with this emailId"


    return jsonify(auth)


@app.route('/user/isVerified', methods=["POST"])
def getUserVerification() :
    userInfo = {}
    data = request.get_json()
    mobile = data['mobile']
    user = Participant.query.filter_by(mobileNumber=mobile).first()

    if user == None:
        userInfo["ACK"] = "FAILED"
        return jsonify(userInfo)

    if user.verified == 0:

        otp = OTPs.query.filter_by(mobile=mobile).first()
        session = db.session

        if otp:
            try:
                session.delete(otp)
                session.commit()
            except:
                session.rollback()
                session.flush()
        OTP = ''.join(random.choice(string.digits) for _ in range(6))
        status = sendOTP(user.firstName, user.mobileNumber, OTP)
        status = True
        if not status:
            return jsonify({'ACK': 'FAILED', 'message': 'Unable to send OTP.'})

    userInfo["ACK"] = "SUCCESS"
    userInfo['verified'] = user.verified
    return jsonify(userInfo)



################################################################
#####################REGISTRATION###############################

@app.route('/event/register', methods=['POST'])
def registerEvent():
  try:
    json = request.get_json()

    eventId = json['eventId']
    event = Event.query.filter_by(eventId=eventId).first()

    team = [ member for member in json['team'] ]
    teamLeaderId = json['leader']

    if teamLeaderId not in team:
      return jsonify({ 'ACK': 'FAILED', 'message': 'Leader not from team' })

    for pecfestId in team:
      user = Participant.query.filter_by(pecfestId=pecfestId).first()
      if not user:
        return jsonify({ 'ACK': 'FAILED', 'message': 'Invalid members' })

    ## check whether users are already registered or not
    for pecfestId in team:
      reg = EventRegistration.query.filter_by(memberId=pecfestId, eventId=eventId).first()
      if reg:
        return jsonify({ 'ACK': 'FAILED', 'message': pecfestId + ' is already registered to this event.'})

    ## register this team in the database
    regs = []
    for pecfestId in team:
      reg = EventRegistration(
              eventId=eventId,
              memberId=pecfestId,
              leaderId=teamLeaderId)
      regs.append(reg)

    session = db.session
    success = False
    try:
      for reg in regs:
        session.add(reg)

      session.commit()
      success = True
    except Exception as err:
      session.rollback()
      session.flush()

    if success:
      return jsonify({ 'ACK': 'SUCCESS' })
    else:
      return jsonify({ 'ACK': 'FAILED' })
  except:
    return jsonify({ 'ACK': 'FAILED' })


## Get user's registered event's details
@app.route('/user/registeredEvents', methods=['GET'])
## eg /user/registeredEvents?id=AAKPYC1TV
def getUserRegisteredEvents():

  pecfestId = request.args['id']
  #############################################################################################
  # get the user's registered events using eventregistrations where memberId = user's pecfestId or leaderId = user's pecfestId
  # Eventregistration.eventId_relation is the relation between the foreign key of Event registration and primary key 'eventId' of Event
  # and is defined in /models/event_registration.py
  
  events = db.session.query(Event).\
  join(EventRegistration.eventId_relation).\
  filter(or_(EventRegistration.memberId == pecfestId , EventRegistration.leaderId == pecfestId)).all()
  
  #### Also try :- 
  '''events = db.session.query(Event).\
  filter(or_(EventRegistration.memberId == pecfestId , EventRegistration.leaderId == pecfestId)).\
  join(EventRegistration.eventId_relation).all()'''

  registeredEvents = []      ## a list of dicts, each entry of the list stores information of the registered event

  for i in range(0, len(events)):
    events_dict = {}
    events_dict["name"] = events[i].Name
    events_dict["day"] = events[i].day
    events_dict["venue"] = events[i].Location
    events_dict["time"] = events[i].time
    registeredEvents += [events_dict]

  return jsonify(registeredEvents)




@app.route('/user/notifications', methods=['GET'])
## eg /user/notifications?id=AAKPYC1TV
def getUserNotifications():

  pecfestId = request.args['id']
  #################################################################################################
  ## get the notifications pertaining to user's registered events using Notifications and EventRegistration table 
  ## filtered by memberId = user's pecfestId or leaderId = user's pecfestId

  ## notif_ rel is the relation between the foreign key 'Notifications.eventId' and primary key 'eventId' of Event
  ## This has been used to get the name of the event using the eventId in notifications

  notifs = db.session.query(Notifications, Event).\
  join(EventRegistration, Notifications.eventId == EventRegistration.eventId).\
  join(Notifications.notif_rel).\
  filter(or_(EventRegistration.memberId == pecfestId , EventRegistration.leaderId == pecfestId)).\
  all()

  ## Also try
  '''notifs = db.session.query(Notifications, event).\
  filter(or_(EventRegistration.memberId == pecfestId , EventRegistration.leaderId == pecfestId)).\
  join(EventRegistration, Notifications.eventId == EventRegistration.eventId).\
  join(Notifications.notif_rel).\
  all()'''

  user_notifications = []         ## a list of dicts, each entry of the list stores notification of a registered event

  for i in range(0, len(notifs)):
    notif_dict = {}
    notif_dict["eventName"] = notifs[i][1].Name
    notif_dict["notificationTitle"] = notifs[i][0].notificationTitle
    notif_dict["notificationDetails"] = notifs[i][0].notificationDetails
    user_notifications += [notif_dict]
  
  return jsonify(user_notifications)


@app.route('/', methods=['GET'])
def homePage():
    return "Server is Running"

################################################################
################################################################

if __name__ == '__main__':
    app.run()
    # For Local Host ( Over LAN )