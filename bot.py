# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from botbuilder.ai.qna import QnAMaker, QnAMakerEndpoint
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, CardAction, ActionTypes, SuggestedActions

from config import DefaultConfig
from search_tableau_KB import get_search_results, get_query_url

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
SEARCH_URL = 'https://www.tableau.com/search#t=support'
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
        self.tableau = ''

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        """
        Send a welcome message to the user and tell them what actions they may perform to use this bot
        """

        return await self._send_welcome_message(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Respond to the users choice and display the suggested actions again.
        """

        text = turn_context.activity.text.lower()
        if self.tableau and text.startswith('y'):
            await self.search_tableau(turn_context, self.tableau)
            self.tableau = ''
            await self._send_suggested_actions(turn_context, first_time=False)
            return
        elif self.tableau:
            self.tableau = ''
            await turn_context.send_activity(r"If it's not about Tableau then idk what to do")
            await self._send_suggested_actions(turn_context, first_time=False)
            return

        response_text = self._process_input1(text)
        if not response_text:
            print()
            await self._classify_request(turn_context, text)
        else:

            await turn_context.send_activity(MessageFactory.text(response_text))
            await self._send_suggested_actions(turn_context, first_time=False)

            #await self.on_message_activity
            #await self._classify_request(turn_context, turn_context.activity.text)

    async def _send_welcome_message(self, turn_context: TurnContext):
        for member in turn_context.activity.members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        f" Hello {member.name} :D ! Hope you are well\n\n"
                        f"I will do my best to answer your questions (ง •̀_•́)ง !"
                    )
                )

                await self._send_suggested_actions(turn_context)

    
    async def _classify_request(self, turn_context: TurnContext, intent:str):
        #intent = None  ### replace with classifier output later ??

        # if intent == 'hello':
        #     return await self._send_welcome_message(turn_context)
        if intent == 'nothing else':
            return await turn_context.send_activity("cool cool cool, bye!")
        elif any(x in intent.lower() for x in ('license', 'training', 'ticketing')):
            await turn_context.send_activity(f"This is the link to the Tableau ticketing system: https://uthrprod.service-now.com")

        else:
            # response = await self.qna_maker.get_answers(turn_context)
            result = await self.qna_maker.get_answers_raw(turn_context)
            response = result.answers

            if response and len(response) > 0 and response[0].score > 0.5 :
                await turn_context.send_activity(MessageFactory.text(response[0].answer+f" (score {response[0].score})"))
            else:
                await turn_context.send_activity("I didn't find any answer on the UTBI KB 🤔")

                if 'tableau' in intent.lower():
                    await self.search_tableau(turn_context, intent)
                else:
                    self.tableau = intent
                    # google search?
                    ...


        await self._send_suggested_actions(turn_context, first_time=False)

    async def search_tableau(self, turn_context, intent):
        await turn_context.send_activity("I'm looking for answers on the Tableau Forum...")
        query_url = get_query_url(SEARCH_URL, intent, None)
        for res_title, res_url in get_search_results(query_url):
            await turn_context.send_activity(f"[{res_title}]({res_url})")

    def _process_input1(self, text: str):

        if text == "tableau_status":
            return f"Tableau server is up!"

        if text == "cognos_status":
            return f"Cognos server is currently down. We apologize for the inconvenience! T___T"

        if text == "access_form":
            return "Please fill out this form and email it to UTBI"

        else:
            return ""
        

        

    async def _send_suggested_actions(self, turn_context: TurnContext, first_time=True):
        """
        Creates and sends an activity with suggested actions to the user. When the user
        clicks one of the buttons the text value from the "CardAction" will be displayed
        in the channel just as if the user entered the text. There are multiple
        "ActionTypes" that may be used for different situations.
        """
        if not self.tableau:
            if first_time:
                msg = "Do you need info on the following? If not, please lemme know what I can help you with today?"
            else:
                msg = "Can I help you with anything else today?"
            reply = MessageFactory.text(msg)

            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(
                        title="Check tableau status",
                        type=ActionTypes.im_back,
                        value="tableau_status",
                        # image="https://via.placeholder.com/20/FF0000?text=R",
                        # image_alt_text="R",
                    ),
                    CardAction(
                        title="Check cognos status",
                        type=ActionTypes.im_back,
                        value="cognos_status",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                    CardAction(
                        title="UTBI Access forms",
                        type=ActionTypes.im_back,
                        value="access_form",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                ]
            )

        else: # Tableau multiturn
            reply = MessageFactory.text("Is this question about Tableau?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(
                        title="Yes",
                        type=ActionTypes.im_back,
                        value="yes tableau",
                        # image="https://via.placeholder.com/20/FF0000?text=R",
                        # image_alt_text="R",
                    ),
                    CardAction(
                        title="No",
                        type=ActionTypes.im_back,
                        value="not tableau",
                        # image="https://via.placeholder.com/20/FFFF00?text=Y",
                        # image_alt_text="Y",
                    ),
                ]
            )


        return await turn_context.send_activity(reply)


