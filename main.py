# coding: utf-8

from flask import Flask, request, jsonify
import os, random
import cek
from elasticsearch import Elasticsearch

app = Flask(__name__)

clova = cek.Clova(
    application_id="com.example.tutorial.test",
    default_language="ja",
    debug_mode=True)

@app.route('/', methods=['GET', 'POST'])
def lambda_handler(event=None, context=None):
    app.logger.info('Lambda function invoked index()')
    return 'hello from Flask!'

# /clova に対してのPOSTリクエストを受け付けるサーバーを立てる
@app.route('/clova', methods=['POST'])
def my_service():
    print(request.headers)
    body_dict = clova.route(body=request.data, header=request.headers)
    response = jsonify(body_dict)
    response.headers['Content-Type'] = 'application/json;charset-UTF-8'
    return response

# 起動時の処理
@clova.handle.launch
def launch_request_handler(clova_request):
    open_message = "知りたい情報を教えてください"
    welcome_japanese = cek.Message(message=open_message, language="ja")
    response = clova.response([welcome_japanese])
    return response

# callNumberIntentが解析されたら実行
@clova.handle.intent("callStatus")
def number_handler(clova_request):
    app.logger.info("Intent started")
    status = clova_request.slot_value("status")
    app.logger.info("status: {}".format(str(status)))
    res = get_status(status)

    message_japanese = cek.Message(message="森田さんの{}は{}です。".format(str(status),res), language="ja")
    response = clova.response([message_japanese])
    return response

# 終了時
@clova.handle.end
def end_handler(clova_request):
    # Session ended, this handler can be used to clean up
    app.logger.info("Session ended.")

# 認識できなかった場合
@clova.handle.default
def default_handler(request):
    return clova.response("Sorry I don't understand! Could you please repeat?")


def get_status(status):
    app.logger.info("get_status started")
    try:
        resjson = client.search(index="mindwavemobile2", size=1, body={"query": {"match_all": {}}, "sort": {"@timestamp": "desc"}})
        if status == "集中度":
            return str(resjson["hits"]["hits"][0]["_source"]["attention"])
        elif status == "リラックス度":
            return str(resjson["hits"]["hits"][0]["_source"]["meditation"])
        else:
            return "不明"
    except Exception as e:
        app.logger.error("Exception at get_status: %s", e)
        return "不明"

if __name__ == '__main__':
    client = Elasticsearch("218.45.184.148:59200")
    port = int(os.getenv("PORT", 5000))
    app.debug = True
    app.run(host="0.0.0.0", port=port)
