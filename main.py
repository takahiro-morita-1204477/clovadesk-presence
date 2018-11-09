# coding: utf-8

from flask import Flask, request, jsonify
import os, random
import cek

app = Flask(__name__)

clova = cek.Clova(
    application_id="com.heroku.kmiura.app",
    default_language="ja",
    debug_mode=True)

@app.route('/', methods=['GET', 'POST'])
def lambda_handler(event=None, context=None):
    app.logger.info('Lambda function invoked index()')
    return 'hello from Flask!'

# /clova に対してのPOSTリクエストを受け付けるサーバーを立てる
@app.route('/clova', methods=['POST'])
def my_service():
    body_dict = clova.route(body=request.data, header=request.headers)
    response = jsonify(body_dict)
    response.headers['Content-Type'] = 'application/json;charset-UTF-8'
    return response

# 起動時の処理
@clova.handle.launch
def launch_request_handler(clova_request):
    open_message = "こんにちは，サイコロに設定したい数字を指定してください"
    welcome_japanese = cek.Message(message=open_message, language="ja")
    response = clova.response([welcome_japanese])
    return response

# WifeStatusIntentの発火箇所
@clova.handle.intent("callNumber")
def wife_status_handler(clova_request):
    app.logger.info("Intent started")
    start_num = clova_request.slot_value("startNum")
    end_num = clova_request.slot_value('endNum')
    app.logger.info("startNum: {}, endNum: {}".format(str(start_num), str(end_num)))
    if start_num > end_num:
        res = decide_num(end_num, start_num)
    else:
        res = decide_num(start_num, end_num)
    message_japanese = cek.Message(message="結果は{}でした。".format(res), language="ja")
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

def decide_num(start_num, end_num):
    app.logger.info("decide_num started")
    try:
        sai_res = random.randint(int(start_num), int(end_num))
        return str(sai_res)
    except Exception as e:
        app.logger.error("Exception at decide_num: %s", e)
        return "分かりません"

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.debug = True
    app.run(host="0.0.0.0", port=port)
