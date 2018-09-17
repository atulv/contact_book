import json
from datamodel.models import ContactBook, UserProfile
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings

redis_connection = settings.REDIS_CONNECTION
name_trie = settings.NAME_TRIE
email_trie = settings.EMAIL_TRIE
queue = settings.REDIS_QUEUE

@csrf_exempt
def signin(request):
    try:
        email = request.POST['email']
    except KeyError:
        return create_response('email is required', 400)
    try:
        password = request.POST['password']
        password = password.strip()
        if not password:
            raise ValueError()

    except KeyError:
        return create_response('password is required', 400)
    except ValueError:
        return create_response('password cannot be blank', 400)
    try:
        validate_email(email)
    except validate_email.ValidationError:
        return create_response('invalid email', 400)

    user = authenticate(username=email, password=password)
    if not user:
        return create_response('wrong email or password', 400)

    auth_login(request, user)
    return create_response('sucess')

@csrf_exempt
@login_required
def signout(request):
    auth_logout(request)
    return create_response('success')
    
@csrf_exempt
def signup(request):
    try:
        name = request.POST['name']
        name = name.strip()
        if not name:
            raise ValueError
    except KeyError:
        return create_response('name is required', 400)
    except ValueError:
        return create_response('name cannot be blank', 400)

    try:
        email = request.POST['email']
    except KeyError:
        return create_response('email is required', 400)

    try:
        password = request.POST['password']
        password = password.strip()
        if not password:
            raise ValueError	
    except KeyError:
        return create_response('password is required', 400)
    except ValueError:
        return create_response('password cannot be blank', 400)

    try:
        validate_email(email)
    except validate_email.ValidationError:
        return create_response('email is not valid', 400)

    user, error = create_user(**{'name': name, 'email': email, 'password': password})
    if user:
        #create user profile then log user in
        user_profile = UserProfile(user = user, name = name, email = email)
        try:
            user_profile.save()
        except IntegrityError:
            user_profile = UserProfile.objects.get(email=email)
        except:
            return create_response('error in signup', 500)

    if not errors:
        user = authenticate(username=email, password=password)
        auth_login(request, user)
    else:
        return create_response(error, 400)

    return create_response('sucess')


def create_user(**params):
    '''
    Create new use if user is not present/registerd
    checks email
    returns User instance
    '''
    name = params.get('name')
    email = params.get('email')
    password = params.get('password')

    try:
        User.objects.get(username=email)
    except User.DoesNotExist:
        pass
    else:
        return None, 'This email is already registered'

    new_user = User(username=email)
    first_and_last_name = name.split(' ', 1)
    new_user.first_name = name
    if len(first_and_last_name)>1:
        new_user.first_name = first_and_last_name[0].strip()
        new_user.last_name = first_and_last_name[1].strip()
    new_user.set_password(password)
    new_user.email = email
    new_user.is_active = False
    
    try:
        new_user.save()
    except IntegrityError:
        new_user = User.objects.get(username=email)

    return new_user, None

@csrf_exempt
@login_required
def add_contact(request):
    """
    add contact to db, adds string to redis queue for
    insertion in trie
    """
    user_profile = request.user.profile
    try:
        email = request.POST['email']
    except KeyError:
        response = JsonResponse({'message': 'email is blank'})
        response.status_code = 400
        return response
    else:
        try:
            email = email.strip()
            validate_email(email)
        except validate_email.ValidationError:
            return create_response('email is invalid', 400)
    try:
        info = request.POST['info']
    except KeyError:
        return create_response('info is blank', 400)
        
    try:
        info_json = json.loads(info)
    except:
        return create_response('invalid format for info', 400)
    else:
        try:
            name = info_json['name'].strip()
            if not name:
                return create_response('name should not be blank', 400)
        except KeyError:
            return create_response('name is required in info', 400)

    contact = ContactBook(email=email, info=info, created_by=user_profile)
    try:
        contact.save()
    except IntegrityError:
        return create_response('email is already in use', 400)
    except:
        return create_response('error on adding contact', 400)
    if redis_connection:
        redis_connection.rpush(queue, ('add', 0, email, contact.id))
        redis_connection.rpush(queue, ('add', 1, name, contact.id))    
    #else:
        #log for retry   

    return create_response('contact added')

def edit_contact(request, _id=contact_id):
    """
    edits info, email cannot be edited
    if name is edited old name will be removed from trie
    new name will be added
    """
    try:
        info = request.POST['info']
    except KeyError:
        return create_response('info is required', 400)
    try:
        info_json = json.loads(info)
    except ValueError:
        return create_response('invalid format for info', 400)

    try:
        name = info_json['name'].strip()
        if not name:
            return create_response('name cannot be blank', 400)
    except KeyError:
        return create_response('name is required in info', 400)
    try:
        contact = ContactBook.objects.get(id=_id)
    except ContactBook.DoesNotExist:
        return create_response('invalid contact_id %s' % _id)

    old_name = json.loads(contact.info)['name']

    try:
        contact.info = info
        contact.save()
    except:
        return create_response('error updating contact', 500)

    if redis_connection:
        if old_name != name:
            redis_connection.rpush(queue, ('remove', 1, old_name, contact.id))
            redis_connection.rpush(query, ('add', 1, name, contact.id))
    #else:
        #log for retry   
    return create_response('contact updated successfully')

def delete_contact(request, _id=contact_id):
    try:
        contact = ContactBook.objects.get(id=_id)
    except ContactBook.DoesNotExist:
        return create_response('invalid contact_id')
    try:
        contact.is_active = False
        contact.save()
    except:
        return create_response('error in deleting contact', 500)

    if redis_connection:
        email = contact.email
        name = json.loads(contact.info)['name']
        redis_connection.rpush(queue, [('remove', 1, name, contact.id))
        redis_connection.rpush(queue, ('remove', 0, email, contact.id))
    return create_response('contact deleted successfully')


def find(request):
    'prefix search by name and email'
    try:
        query = request.GET['query_string']
        query = query.strip()
        if not query:
            raise ValueError

    except KeyError:
        return create_response('query string is required', 400)
    except ValueError:
        return create_response('query string cannot be blank', 400)

    try:
        query_type = request.GET['query_type']
        query_type = query_type.strip()
        if query_type not in ('email', 'name'):
            raise ValueError
             
    except KeyError:
        return create_response('query type is required email/name', 400)
    except ValueError:
        return create_response('query type must be email or name', 400)

    page_no = request.GET.get('page_no',1)
    try:
        page_no = int(page_no)
    except ValueError:
        return create_response('invalid value for page no', 400)
    start = (page_no-1)*10 + 1
    if query_type == 'name':
        contact_ids, total = name_trie.find(query_string, start, 10)
    else:
        contacts_ids, total = email_trie.find(query_string, start, 10)

    contacts = ContactBook.objects.filter(id__in=contacts_ids).order_by('id')
    resp = []
    for contact in contacts:
        resp.append(contact.to_json())

    return create_response(data={'contacts': resp, 'total': total})

def create_response(msg='success', status_code=200, data={}):
    response = JsonResponse({'message': msg, 'data': data})
    response.status_code = status_code
    return response
