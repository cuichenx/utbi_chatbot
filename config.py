#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    QNA_KNOWLEDGEBASE_ID = "46d8f1d3-339c-4f15-a558-6cf72b7c231e" # os.environ.get("QnAKnowledgebaseId", "")
    QNA_ENDPOINT_KEY = "e80c3237-0cfa-4938-b147-53028185553e"  # os.environ.get("QnAEndpointKey", "")
    QNA_ENDPOINT_HOST = "https://talkingtree.azurewebsites.net/qnamaker" # os.environ.get("QnAEndpointHostName", "")