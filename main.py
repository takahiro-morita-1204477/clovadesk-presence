import os
import logging
import random

import boto3
from boto3.dynamodb.conditions import Key, Attr

from flask import (
    Flask, request, jsonify
)
from cek import (
    Clova, SpeechBuilder, ResponseBuilder
)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Flask
app = Flask(__name__)

# Clova
application_id = os.environ.get('CLOVA_APPLICATION_ID')
clova = Clova(
    application_id=application_id,
    default_language='ja',
    debug_mode=False)
speech_builder = SpeechBuilder(default_language='ja')
response_builder = ResponseBuilder(default_language='ja')

@app.route('/', methods=['GET', 'POST'])
def lambda_handler(event=None, context=None):
    logger.info('Lambda function invoked index()')

    return 'hello from Flask!'

@app.route('/clova', methods=['POST'])
def clova_service():
    resp = clova.route(request.data, request.headers)
    resp = jsonify(resp)
    # make sure we have correct Content-Type that CEK expects
    resp.headers['Content-Type'] = 'application/json;charset-UTF-8'
    return resp

@clova.handle.intent('CallNumberIntent')
def find_gourmet_by_prefecture_intent_handler(clova_request):
    logger.info('find_gourmet_by_prefecture_intent_handler method called!!')
    prefecture = clova_request.slot_value('prefecture')
    logger.info('Prefecture: %s', prefecture)
    response = None
    if prefecture is not None:
        try:
            response = decide_num(end_num)
        except Exception as e:
            # 処理中に例外が発生した場合は、最初からやり直してもらう
            logger.error('Exception at make_gourmet_info_message_for: %s', e)
            text = '処理中にエラーが発生しました。もう一度はじめからお願いします。'
            response = response_builder.simple_speech_text(text)
    else:
        # 都道府県名を判別できなかった場合
        text = 'もう一度数を指定してください'
        response = response_builder.simple_speech_text(text)
        response_builder.add_reprompt(response,
            'いくつからいくつまでの範囲で振って欲しいですか？')
    # retrun
    return response

def decide_num(end_num):
    logger.info("decide_num started")
    try:
        sai_res = saikoro(end_num)
        message = "サイコロの目は{}".format()
        end_session = True
        response = response_builder.simple_speech_text(message, end_session=end_session)
        return response
    except Exception as e:
        logger.error("Exception at decide_num: %s", e)

def saikoro(end_num):
    return random.randint(0, end_num)

def make_gourmet_info_message_by_name(gourmet_name):
    '''
    ご当地グルメ名に応じたメッセージを生成する
    Parameters
    ----------
    gourmet_name : str
        ご当地グルメ名

    Returns
    -------
    builder : Response
        ご当地グルメ名に応じたご当地グルメ情報メッセージを含めたResponse
    '''
    logger.info('make_gourmet_info_message_by_name method called!!')
    try:
        gourmet_info = get_gourmet_info_for(gourmet_name)
        message = ''
        reprompt = None
        end_session = False
        if gourmet_info is None:
            # ご当地グルメ情報が見つからない場合
            message = '{} という名前のご当地グルメ情報が見つかりませんでした。もう一度教えてください。'.format(
                gourmet_name
            )
            reprompt = '調べたいご当地グルメの名前を教えてください。'
        else:
            # ご当地グルメ情報が見つかった場合
            gourmet_info_detail = gourmet_info['detail']
            if gourmet_info_detail.endswith('。') == False:
                gourmet_info_detail += 'です。'
            message = '{} は、{} のご当地グルメです。{}'.format(
                gourmet_info['yomi'],
                gourmet_info['prefecture'],
                gourmet_info_detail
            )
            end_session = True
        # build response
        response = response_builder.simple_speech_text(message, end_session=end_session)
        if reprompt is not None:
            response = response_builder.add_reprompt(response, reprompt)
        return response
    except Exception as e:
        logger.error('Exception at make_gourmet_info_message_by_name: %s', e)
        raise e


def inquiry_gourmet_info_list_for(prefecture):
    logger.info('inquiry_gourmet_info_list_for method called!!')
    if prefecture is None or '' == prefecture:
        raise ValueError('prefecture is None or empty...')
    # query
    try:
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT', None)
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        table = dynamodb.Table(os.environ.get('TABLE_GOURMET_INFO', '') )
        response = table.scan(
            FilterExpression=Attr('prefecture').eq(prefecture)
        )
        gourmet_info_list = response.get('Items', None)
        if gourmet_info_list is None or len(gourmet_info_list) <= 0:
            gourmet_info_list = None
        return gourmet_info_list
    except Exception as e:
        logger.error('Exception at inquiry_gourmet_info_list_for: %s', e)
        raise e


def get_gourmet_info_for(gourmet_name):
    logger.info('get_gourmet_info_for method called!! [Gourmet:%s]', gourmet_name)
    logger.info('inquiry_gourmet_info_list_for method called!!')
    if gourmet_name is None or '' == gourmet_name:
        raise ValueError('gourmet_name is None or empty...')
    try:
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT', None)
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        table = dynamodb.Table(os.environ.get('TABLE_GOURMET_INFO', '') )
        response = table.get_item(
            Key={
                'name': gourmet_name
            }
        )
        result = None
        item = response.get('Item', None)
        if item:
            result = item
        return result
    except Exception as e:
        logger.error('Exception at get_gourmet_info_for: %s', e)
        raise e

if __name__ == '__main__':
    app.run(debug=True)
