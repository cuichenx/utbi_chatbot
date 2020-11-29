# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from botbuilder.ai.qna import QnAMaker, QnAMakerEndpoint
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, CardAction, ActionTypes, SuggestedActions
from response_strings import *
from config import DefaultConfig
search_method = 'google'
if search_method == 'google':
    from search_TB_on_google import get_search_results
else:
    from search_tableau_KB import get_search_results

import nltk

nltk.download(['stopwords', 'punkt'])
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import datetime

tokenizer = RegexpTokenizer(r'\w+')
stop = stopwords.words('english')
stop += ['michael', 'mike', 'thank', 'thanks', 'hi', 'hello', 'question', 'hey', 'could']
stop += ['assist', 'please', 'help']
stop += ['trying', 'try', 'figure', 'get', 'getting']
[stop.remove(w) for w in ['down', 'up']]

yes_response = ['y', 'yes', 'yeah', 'sure', 'of course', 'yep', 'ok']
no_response = ['n', 'no', 'nope', 'not really', 'not exactly', 'nah', 'nothing', 'nothing else']

class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(f"You said '{ turn_context.activity.text }'")

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

QUERY = 'how to add filter'
# SEARCH_URL = 'https://www.tableau.com/search#t=support'
OUT_FILE = "tableau_kb_search_test.txt"

class SuggestActionsBot(ActivityHandler):
    """
    This bot will respond to the user's input with suggested actions.
    Suggested actions enable your bot to present buttons that the user
    can tap to provide input.
    """
    def __init__(self, config: DefaultConfig):
        self.qna_maker = QnAMaker(
            QnAMakerEndpoint(
                knowledge_base_id=config.QNA_KNOWLEDGEBASE_ID,
                endpoint_key=config.QNA_ENDPOINT_KEY,
                host=config.QNA_ENDPOINT_HOST,
            )
        )
        self.initialize()

    def initialize(self):
        self.tableau = False
        self.multiturn_state = ''
        self.last_question = ''

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        """
        Send a welcome message to the user and tell them what actions they may perform to use this bot
        """
        self.initialize()
        return await self._send_welcome_message(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Respond to the users choice and display the suggested actions again.
        """

        text = turn_context.activity.text.lower()
        if text == '!init':
            self.initialize()
            return

        if self.multiturn_state.startswith('rate'):
            if text in yes_response:
                print('user rated yes')
                self.log_user_feedback('Y')
                self.multiturn_state = ''
                await turn_context.send_activity("Thank you for your feedback. Glad I could help!")
                return await self._send_suggested_actions(turn_context, first_time=False)

            elif text in no_response:
                print('user rated no')
                self.log_user_feedback('N')
                if self.multiturn_state == 'rate_QnA':
                    self.multiturn_state = ''
                    self.tableau = True
                    # await turn_context.send_activity("")
                    return await self._send_suggested_actions(turn_context, first_time=False, after_feedback=True)
                else:  # rate_SiteSearch
                    self.multiturn_state = ''
                    return await self._send_suggested_actions(turn_context, first_time=False,
                                                              custom_text=STR_NOT_HELPFUL)

            else:
                self.multiturn_state = ''  # user enters another question rather than rating. clear rating state


        if self.tableau and text in yes_response:
            await turn_context.send_activity("I'm looking for answers on the Tableau Site...")
            await self.search_tableau(turn_context, self.last_question)
            self.tableau = False
            self.multiturn_state = 'rate_SiteSearch'
            await self._send_suggested_actions(turn_context, first_time=False)
            return
        elif self.tableau:
            self.tableau = False
            if text.startswith('n'):
                return await self._send_suggested_actions(turn_context, first_time=False,
                            custom_text=STR_NOT_HELPFUL)


        # normal questions
        response_text = self._process_input1(text)
        if not response_text:
            print()
            await self._classify_request(turn_context, text)
            self.last_question = text
        else:

            await turn_context.send_activity(MessageFactory.text(response_text))
            await self._send_suggested_actions(turn_context, first_time=False)




    async def _send_welcome_message(self, turn_context: TurnContext):
        for member in turn_context.activity.members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    # MessageFactory.text(
                    #     f" Hello {member.name} :D ! Hope you are well\n\n"
                    #     f"I will do my best to answer your questions (ง •̀_•́)ง !"
                    # )
                    MessageFactory.text(
                    f" Hi there, welcome to the IRDG-BI chatbot!\n\n"
                    f"I will do my best to answer your questions!"
                )
                )

                await self._send_suggested_actions(turn_context)


    
    async def _classify_request(self, turn_context: TurnContext, intent:str):
        #intent = None  ### replace with classifier output later ??

        # if intent == 'hello':
        #     return await self._send_welcome_message(turn_context)
        if intent in no_response:
            return await turn_context.send_activity("Have a nice day!")
        # elif 'training' in intent:
        #     await turn_context.send_activity(
        #         f"To book a Tableau training session, please go to the [ticketing system]"
        #         f"(https://uthrprod.service-now.com/sp?id=sc_cat_item&sys_id=14e6cae9dbee501052e7f8f339961982) "
        #         f"and select \"Tableau Training\" in request type.")
        elif 'ticketing' in intent:
            await turn_context.send_activity(
                f"Are you looking for the [Tableau ticketing system]"
                f"(https://uthrprod.service-now.com/sp?id=sc_cat_item&sys_id=14e6cae9dbee501052e7f8f339961982) ?")

        else:
            # response = await self.qna_maker.get_answers(turn_context)
            result = await self.qna_maker.get_answers_raw(turn_context)
            response = result.answers

            if response and len(response) > 0 and response[0].score > 0.6 :
                if len(response) > 1:
                    print('MORE THAN ONE RESPONSE??')
                if response[0].source.startswith('qna_chitchat'):
                    txt = response[0].answer
                    return await self._send_suggested_actions(turn_context, first_time=False, custom_text=txt)
                else:  # serious question, not chitchat
                    question = response[0].questions[0]
                    txt = (f"**I think you are asking about this question:** \n\n "
                           f"{question} (score {response[0].score}) \n\n "
                           f"**The answer to that is:** \n\n {response[0].answer}")
                    self.multiturn_state = 'rate_QnA'
                await turn_context.send_activity(MessageFactory.text(txt))

            else:
                # await turn_context.send_activity("I didn't find any answer on the UTBI KB 🤔")

                if 'tableau' in intent.lower() or 'dashboard' in intent.lower():
                    await turn_context.send_activity("I'm looking for answers on the Tableau Forum...")
                    await self.search_tableau(turn_context, intent)
                else:
                    self.tableau = True
                    # ask use whether the question is about tableau

        await self._send_suggested_actions(turn_context, first_time=False)

    async def search_tableau(self, turn_context, intent):
        processed_query = self.process_query(intent)
        print('processed query', processed_query)
        
        # query_url = get_query_url(SEARCH_URL, processed_query, None)
        empty_res = True
        for res_title, res_url, res_summary in get_search_results(processed_query):
            empty_res = False
            await turn_context.send_activity(f"### [{res_title}]({res_url})  \n{res_summary}")
        # await turn_context.send_activity(f"[(Show more search results on Tableau site)]({query_url.replace(' ', '%20')})")
        if empty_res:
            await turn_context.send_activity(f"I didn't find anything on the Tableau Forum..")

    def process_query(self, query):


        tokens = [w for w in tokenizer.tokenize(query) if w not in stop]
        return ' '.join(tokens)


    def _process_input1(self, text: str):
        d = {
            "server_status": f"If you have not received any email, the server should be up! If you have trouble connecting to it, you might want to check your vpn connection?",
            # "cognos_status": f"Cognos server is currently down. We apologize for the inconvenience!",
           "access_form": STR_ACCESS_FORM,
            "vpn" : STR_VPN_INSTRUCTIONS,
        }

        return d.get(text, '')
        
    def log_user_feedback(self, feedback):
        solution = self.multiturn_state.split('_')[-1]
        with open('user_feedback_new.txt', 'a+') as f:
            log_row = ['user0', str(datetime.datetime.now()).split('.')[0], '"'+self.last_question+'"', solution, feedback]
            f.write(', '.join(log_row) + '\n')

    async def _send_suggested_actions(self, turn_context: TurnContext, first_time=True, after_feedback=False, custom_text=None):
        """
        Creates and sends an activity with suggested actions to the user. When the user
        clicks one of the buttons the text value from the "CardAction" will be displayed
        in the channel just as if the user entered the text. There are multiple
        "ActionTypes" that may be used for different situations.
        """

        if self.tableau: # Tableau multiturn
            if after_feedback:
                reply = MessageFactory.text("Thank you for your feedback, and sorry I couldn't help. Would you like to look this up on the tableau forum?")
            else:
                reply = MessageFactory.text("I didn't find any answers in the IRDG-BI knowledge base. Is this question about Tableau?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(
                        title="Yes",
                        type=ActionTypes.im_back,
                        value="yes",
                        # image="https://via.placeholder.com/20/FF0000?text=R",
                        # image_alt_text="R",
                    ),
                    CardAction(
                        title="No",
                        type=ActionTypes.im_back,
                        value="no",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                ]
            )

        elif self.multiturn_state.startswith('rate'):
            reply = MessageFactory.text("Did that help with your question?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(
                        title="Yes",
                        type=ActionTypes.im_back,
                        value="yes",
                    ),
                    CardAction(
                        title="No",
                        type=ActionTypes.im_back,
                        value="no",
                    ),
                ]
            )

        else:
            if custom_text is not None:
                msg = custom_text
            elif first_time:
                msg = "Do you need info on the following? If not, please let me know what I can help you with today?"
            else:
                msg = "Can I help you with anything else today?"
            reply = MessageFactory.text(msg)

            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(
                        title="Check Tableau/Cognos status",
                        type=ActionTypes.im_back,
                        value="server_status",
                        # image="https://via.placeholder.com/20/FF0000?text=R",
                        # image_alt_text="R",
                    ),
                    CardAction(
                        title="IRDG-BI Access forms",
                        type=ActionTypes.im_back,
                        value="access_form",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                    CardAction(
                        title="VPN Instructions",
                        type=ActionTypes.im_back,
                        value="vpn",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                ]
            )


        return await turn_context.send_activity(reply)


