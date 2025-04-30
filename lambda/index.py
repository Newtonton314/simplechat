# lambda/index.py
import json
import os
import boto3
import urllib.request
import urllib.error
import urllib.parse
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError

API_URL = os.environ.get("LLM_API_URL", "")
if not API_URL:
    raise RuntimeError("接続できません")



def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        message = body["message"]
        conversation_history = body.get("conversationHistory", [])

        messages = conversation_history + [{"role": "user", "content": message}]

        # Colab API へ POST 
        payload = {
            "prompt": message,               # まずは直近の発言だけ渡す
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
        req = urllib.request.Request(
            urllib.parse.urljoin(API_URL, "/generate"),
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as res:
            res_json = json.loads(res.read())

        assistant_response = res_json.get("generated_text", "").strip()
        if not assistant_response:
            raise ValueError("generated_text が空です")

   
        messages.append({"role": "assistant", "content": assistant_response})

   
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    # 例外処理 
    except (urllib.error.HTTPError, urllib.error.URLError) as net_err:
        error_msg = f"外部API呼び出しに失敗: {net_err}"
    except Exception as err:
        error_msg = str(err)

    return {
        "statusCode": 500,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({"success": False, "error": error_msg})
    }