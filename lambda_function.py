# coding: UTF-8
from __future__ import print_function

import boto3,os
import json,logging,re
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Region指定しないと、デフォルトのUSリージョンが使われる
clientLambda = boto3.client('lambda', region_name='ap-northeast-1')

logger.info('Loading function')

def lambda_handler(event, context):

    logger.info("Received event: " + json.dumps(event, indent=2))
    lineMessage = json.loads(event["body"])
    logger.info( json.dumps(lineMessage, indent=2))
    
    messageText = lineMessage["events"][0]["message"]["text"]
    
    # 形態素解析サービスを利用して、MessageTextの形態素解析JSONを取得
    textAnalyzeJson = callTextAnalyze(messageText)
    
    # 登録されているサービス一覧から最も応答すべきメッセージを決定する
    ReplayMessage = priorProcess( lineMessage, textAnalyzeJson )
    
    # LINE側のメッセージAPIにリクエストを送ることで返信とする
    sendReplayMessage( ReplayMessage["message"], lineMessage["events"][0]["replyToken"] )
    
    # API-Gateway側へのレスポンス
    return returnOk()
    
# TextAnalyzeサービスを呼び出して結果のJsonを取得する
def callTextAnalyze( messageText) :
    
    # 形態素解析サービスを利用して、MessageTextの形態素解析を実施する
    textAnalyzeResponse = clientLambda.invoke(
        # Calleeのarnを指定
        FunctionName='arn:aws:lambda:ap-northeast-1:966887599552:function:cloud9-analyzeText-analyzeText-WPINCA1TJQE5',
        # RequestResponse = 同期、Event = 非同期 で実行できます
        InvocationType='RequestResponse',
        # byte形式でPayloadを作って渡す
        Payload=json.dumps({"message": messageText}).encode("UTF-8")
    )
    #実行結果を読みだして、JSONに変換
    textAnalyzeJson = json.loads( textAnalyzeResponse["Payload"].read().decode('utf-8') )
    logger.info( json.dumps( textAnalyzeJson , indent=2))
    return textAnalyzeJson


# 子サービスを呼び出して応答メッセージを決定する
def priorProcess( lineMessage, textAnalyzeJson ) :

    #リアクションサービスのリストは別途Jsonにて管理
    with open("reactionServices.json", "r") as file:
        reactionServices = json.load(file)
        
    childFunctionList = reactionServices["childFunctionList"]

    childEventSet = {
        "lineMessage": lineMessage ,
        "analysedMessage": textAnalyzeJson
    }
    
    logger.info("start prior Process")
    processPriorResponse = clientLambda.invoke(
        # Calleeのarnを指定
        FunctionName='cloud9-process-prior-1H48J191V1PVH',
        # RequestResponse = 同期、Event = 非同期 で実行できます
        InvocationType='RequestResponse',
        # byte形式でPayloadを作って渡す
        Payload=json.dumps( {"functions": childFunctionList, "event": childEventSet }).encode("UTF-8")
    )
    #実行結果を読みだして、JSONに変換
    res = processPriorResponse["Payload"].read().decode('utf-8')
    logger.info(res)
    #responseの形式がJSON Stringの二重エンコードになっているように見えるから↓のコード。いまいち
    priorJson = json.loads( res )
    priorJson = json.loads( priorJson )
    logger.info(priorJson)
    logger.info( json.dumps( priorJson , indent=2, ensure_ascii=False))
    
    return priorJson

# LINE側へ応答メッセージを返信する
def sendReplayMessage( replyMessage, replayToken ):

    logger.info( "startSendReplayMessage" )
    logger.info( replyMessage )
    logger.info( replayToken )
    
    url = "https://api.line.me/v2/bot/message/reply"
    method = "POST"
    # ヘッダ設定 LINE用認証トークンは別途管理(template.yamlにて管理)
    headers = {
        'Authorization':'Bearer ' + os.environ.get('LINE_LONGTIME_TOKEN') ,
        'Content-Type': 'application/json'
    }
    params = {
        "replyToken": replayToken ,
        "messages" : [
            {
                "type": "text" ,
                "text": replyMessage
            }
        ]
    }
    json_data = json.dumps(params).encode("utf-8")
    request = urllib.request.Request(url, data=json_data, headers=headers, method=method)

    with urllib.request.urlopen(request) as response:
        logger.info(response.read().decode("utf-8"))

    
def returnOk() :
    return  {
        'statusCode': 200,
        'body': "ok",
        'headers': {
            'Content-Type': 'application/json'
        }
    }
    
def returnNg( statusCode = 400  ) :
    return {
        'statusCode': statusCode,
        'body': "no response",
        'headers': {
            'Content-Type': 'application/json'
        }
    }