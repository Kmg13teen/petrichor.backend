from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate, login, logout, get_user
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request, Empty
from resp import r500, r200
from .models import *
from userapi import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.

def home(request):
    return HttpResponse('This is the homepage!')

@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        data = request.data
        username = data['username'].strip()
        email = data['email']
        pass1 = data['password']
        phone = data['phone']
        insti_name = data['college']
        gradyear = data['gradyear']
        insti_type = data['institype']
        stream = data['stream']
        
        if User.objects.filter(email=email).first():
            return Response({
                'status': 404,
                "registered": False,
                'message': "Email already registered",
                "username": username
            })


        else:
            new_user = User(username=email)
            new_user.set_password(pass1)
            new_user.is_active = True
            new_user.save()
            

            institute = Institute.objects.get_or_create(instiName=insti_name, institutionType=insti_type)[0]
            # institute = Institute.objects.get(instiName=instituteID)

            print(institute.pk)


            user_profile = Profile.objects.create(username=username, 
                                                  email=email,
                                                  phone=phone,
                                                  instituteID=institute.pk,
                                                  gradYear=gradyear,
                                                  stream=stream)
            user_profile.save()

            return Response({
                'status': 200,
                "registered": True,
                'message': "Success",
                "username": username
            })


@api_view(['POST'])
def user_login(request):
    if request.method == 'POST':

        if request.data is None:
            return r500("invalid form")
        data=request.data

        username = data['username'].strip()
        print(username)
        password = data['password']
        print(password)
        my_user = authenticate(username = username, password = password)
        if my_user is not None:
            login(request, my_user)
            profile = Profile.objects.get(email=username)
            token = (request.session.session_key)
            print("OK")
            return Response({
                "ok": True,
                "username": profile.username,
                "token": token,
                "registrations": 0
            })
        print("Failed")
        return Response({
            "message": "The username or password is incorrect",
            "logged-in": "false"
        })

@api_view(['POST'])
def user_logout(request):
    logout(request)
    return Response(
        {
            "logged-in": "false",
            "message": "User has logged out"
        }
    )
    # return redirect('login')

@api_view(['POST'])
def getUserInfo(request):
    print(request.data,"p")
    user = get_user_from_session(request)
    if user:
        print("Passed",user,"p")
        profileUser=Profile.objects.get(email=user)
        if profileUser:
            response={
                "username":profileUser.username,
                "email":profileUser.email,
                "phone":profileUser.phone,
                "gradyear":profileUser.gradYear,
                "stream":profileUser.stream
            }
            instituteName=""
            try:
                instituteName=Institute.objects.get(pk=profileUser.instituteID).instiName
            except ObjectDoesNotExist:
                return r500("Oopss")
            response["college"]=instituteName

            events=[]
            eventEntries=EventTable.objects.all()
            for eventEntry in eventEntries:
                if str(user) in eventEntry.emails:
                    events.append({"eventId":eventEntry.eventId,"status":eventEntry.verified})
            response["events"]=events
            return Response({
                "status":200,
                "response":response
                })
    else:
        print("Auth failed")
        # return Response({
        #     "status":200,
        #     "response":{
        #         "username":"alonot",
        #         "email":"csk1@gmail.com",
        #         "phone":"1221211221",
        #         "instituteID":"11222",
        #         "college":"IIT PKD",
        #         "gradyear":2029,
        #         "stream":"Science",
        #         "events":[{"eventId":"TP00","status":"Payment Verified"},
        #                   {"eventId":"WP02","status":"Payment Pending"}]
        #     }
        # })
        return Response({
            "status":404,
            "response":None
        })


def get_user_from_session(request):
    print(request.data)
    session = Session.objects.get(session_key=request.data["token"])
    session_data = session.get_decoded()
    print(session_data)
    uid = session_data.get('_auth_user_id')
    user = User.objects.get(id=uid)
    if user:
        return user
    else:
        print(request.session.session_key)
        return None

@api_view(['POST'])
def whoami(request: Request):
    user = get_user_from_session(request)
    events=[]
    if user is not None:
        eventEntries=EventTable.objects.all()
        for eventEntry in eventEntries:
            if str(user) in eventEntry.emails:
                events.append(eventEntry.eventId)
    print({
        'user': str(user) if user else None, # type: ignore
        # 'user': str(user) if user else None , # type: ignore
        'events': events,
        'email': user.email #type: ignore
    })
    return Response({
        'user': str(user) if user else None, # type: ignore
        # 'user': str(user) if user else None , # type: ignore
        'events': events,
        'email': str(user) #type: ignore
    })


# @login_required
@api_view(['POST'])
def apply_event_paid(request: Request):
    data=request.data
    if data is None:
        return r500("invalid form")
    try:
        user=get_user_from_session(request)
        if user is None:
            return r500('login')
        user_email = user.username # type: ignore
        participants = data['participants'] # type: ignore
        event_id = data['eventID'].strip() # type: ignore
        transactionId = data['transactionId'].strip() # type: ignore

    except KeyError:
        return r500("participants, eventid and transactionId required. send all.'")
# try:
    verified=False
    if user_email.endswith("smail.iitpkd.ac.in"):
        verified=True
        transactionId="IIT Palakkad Student"
        
    eventTableObject = EventTable.objects.create(eventId=event_id,
                                                 emails=EventTable.serialise_emails(participants), #type: ignore
                                                 transactionId=transactionId,verified=verified)
    eventTableObject.save()
    return r200("Event applied")
    # except Exception:
    #     print(user_id,event_id,transactionId,verified)
    #     return r500("Oopsie Doopsie")


# @login_required
@api_view(['POST'])
def apply_event_free(request):
    data=request.data
    print(data)
    if data is None:
        return r500("invalid form")
    try:
        # user=get_user_from_session(request)
        # if user is None:
        #     return r500('login')
        user_email = user.username # type: ignore
        # user_email="csk1@gmail.com"
        participants = data['participants'] # type: ignore
        event_id = data['eventId'].strip() # type: ignore

    except KeyError as e:
        print(e)
        return r500("participants and eventid required. send both.'")

    try:
        transactionId = "pp"
        if user_email.endswith("smail.iitpkd.ac.in"):
            transactionId="IIT Palakkad Student"
            
        eventTableObject = EventTable.objects.create(eventId=event_id,
                                                    emails=EventTable.serialise_emails(participants), #type: ignore
                                                    transactionId=transactionId, verified=True)
        eventTableObject.save()
        return r200("Event applied")
    except Exception as e:
        print(e)
        return r500("Something went wrong "+str(e))


# @login_required # limits the calls to this function ig
@api_view(['POST'])
def get_event_data(request):
    data=request.data
    print(data)
    if data is None:
        return r500("invalid form")
    try:
        event_id = data["eventId"]
        print(data)
    except KeyError:
        return r500("Send an eventID")
    
    event = Event.objects.filter(eventId = event_id).first()
    if event is None:
        return Response({
        "name": "Its nothing",
        "fee": 0,
        "minMemeber": 0,
        "maxMemeber": 0
    })
        return r500(f"Invalid Event ID = {event_id}")
    return Response({
        "name": event.name,
        "fee": event.fee,
        "minMemeber": event.minMember,
        "maxMemeber": event.maxMember
    })


@api_view(['POST'])
def send_grievance(request: Request):
    try:
        data = request.data
        if isinstance(data, Empty) or data is None:
            return r500("Invalid Form")
        
        name = data['name'] # type: ignore
        email = data['email'] # type: ignore
        content = data['content'] # type: ignore

        send_mail(
            subject=f"WEBSITE MAIL: Grievance from '{name}'",
            message=f"From {name} ({email}).\n\n{content}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["112201015@smail.iitpkd.ac.in", "petrichor@iitpkd.ac.in"]
        )
        print("grievance email sent")
        return Response({
                'status':200,
                'success': True
            })

    except Exception as e:
        return Response({
                'status':400,
                'success': False
            })