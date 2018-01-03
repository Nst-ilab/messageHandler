# coding: UTF-8
from __future__ import print_function

import boto3,os
import json,logging,re
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info('Loading function')

def lambda_handler(event, context):

    logger.info("Received event: " + json.dumps(event, indent=2))
    
    '''
    body_object = json.loads(event["body"])
    messageText = body_object["events"][0]["message"]["text"]
    
    if messageText.find("天気") >= 0 :
        # boto3でLambdaを使う宣言をします
        clientLambda = boto3.client('lambda')
        # Calleeを実行します
        clientLambda.invoke(
            # Calleeのarnを指定
            FunctionName='i-lab-weather-service',
            # RequestResponse = 同期、Event = 非同期 で実行できます
            InvocationType='Event',
            # 引数をJSON形式で渡します
            Payload=json.dumps(event).encode("UTF-8")
        )
    '''
    
    # LINE側のメッセージAPIにリクエストを送ることで返信とする
    
    lineMessage = json.loads(event["body"])
    logger.info( json.dumps(lineMessage, indent=2))
    
    url = "https://api.line.me/v2/bot/message/reply"
    method = "POST"
    # ヘッダ設定 LINE用認証トークンは別途管理
    headers = {
        'Authorization':'Bearer ' + os.environ.get('LINE_LONGTIME_TOKEN') ,
        'Content-Type': 'application/json'
    }

    params = {
        "replyToken": lineMessage["events"][0]["replyToken"] ,
        "messages" : [
            {
                "type": "text" ,
                "text": lineMessage["events"][0]["message"]["text"]
            }
        ]
    }
    json_data = json.dumps(params).encode("utf-8")
    request = urllib.request.Request(url, data=json_data, headers=headers, method=method)

    with urllib.request.urlopen(request) as response:
        logger.info(response.read().decode("utf-8"))

    
    # API-Gateway側へのレスポンス
    return {
        'statusCode': 200,
        'body': "応答受けたよ！",
        'headers': {
            'Content-Type': 'application/json'
        },
    }