from .models import Session
from .menus import *

class UssdLib():

    def __init__(self, telephone):
        self.api = None
        self.telephone = telephone


    def check_user_session(self, validated_data, phone):
        user_history = Session.objects.filter(phone=phone, session_id=validated_data.get("sessionId"))

        if len(user_history)> 0:
            current_session = user_history[0]
            current_menu = user_history[0].current_menu

            print("0000000000000000000000000000000000")
            print(current_menu)

            if not current_menu:
                return self.start_session(validated_data, phone)

            # previous_menu = current_session.previous_menu ? current_session.previous_menu : current_menu
            previous_menu = current_session.previous_menu if current_session.previous_menu else current_menu
            current_session.current_menu = 'resume_session'
            # current_session.previous_menu = str(current_menu) + '-'+ str(previous_menu)
            current_session.previous_menu = previous_menu
            current_session.save()
            menu = WELCOME_MENU.get('welcome_to_finwise')
            # return menu['text']
            return self.make_response(menu['text'].format(header='Welcome to finwise'), previous_menu, menu['callback'])

        return self.start_session(validated_data, phone)


    def start_session(self, validated_data, phone):
        menu = ''
        last_menu = ''
        is_all = ''
        token = None

        menu = WELCOME_MENU.get('welcome_to_finwise')
        last_menu = 'welcome_to_finwise'

        self.new_session(last_menu, validated_data, phone)
        return self.make_response(menu['text'].format(header='Welcome to finwise'), last_menu, menu['callback'])



    def new_session(self, menu_code, validated_data, phone, token=None):
        user_history = Session.objects.filter(phone=phone, session_id=validated_data.get("sessionId"))
        if len(user_history)>0:
            session = user_history[0]
            session.token = token
            session.save()
            print("000000000000000000000000000000000 1.  ")
            print((session))
        else:
            session = Session(
                session_id = validated_data.get("sessionId"),
                phone=phone,
                current_menu = menu_code,
                token=token
            )
            session.save()
            print("000000000000000000000000000000000 2.  ")
            print((session))
        return session


    def make_response(self, response, last_menu, action):
        # if last_menu != 'resume_session' and response.startswith('CON'):
        #     self.api.add_get_items_cache(self.telephone + 'menu', response, "set")
        #     self.api.add_get_items_cache(self.telephone + 'callback', action, "set")            

        # if not response.startswith('CON'):
        #     # self.api.delete_all_key_cache(self.telephone)
        #     user_history = Session.objects.filter(phone=self.telephone)
        #     current_session = user_history[0]
        #     current_session.delete()

        return response

    def process_welcome(self, ussd_response, validated_data, current_session):
        option = ussd_response.split('*')
        if option[len(option)-1] in ["1"]:
            if option[len(option)-1] == '1':
                current_session.previous_menu = current_session.current_menu
                current_session.current_menu = 'welcome_to_finwise'
                current_session.save()
                menu = WELCOME_MENU.get('welcome_to_finwise')
                return menu['text'].format(header='Welcome To FinWise')
        else:
            return "Error Occured At FinWise".format(header="Invalid Request")



    def process_menu(self, validated_data, current_session):
        ussd_response = validated_data.get('text')
        menu_process_funcs = {
            'welcome_to_finwise': self.process_welcome,
        }
        process_menu_func = menu_process_funcs.get(
            current_session.current_menu, self.process_invalid_session
        )

        next_response = process_menu_func(
            ussd_response, validated_data, current_session
        )

        return next_response

    def process_invalid_session(self, ussd_response=None, validated_data=None, current_session=None):
        return {'END Invalid session terminated'}