#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import re
import requests
import socket

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation.
When showing HTML, always include what is in the body tag, 
but exclude the code surrounding the actual content. 
So exclude always BODY, HEAD and HTML .
"""

MODEL = "gpt-35-turbo"
AI = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    notify_if_match(input)
    input=domain_manipulation(input)
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


"""
import re
from pathlib import Path
text = Path("util/test/chess.txt").read_text()
text = Path("util/test/html.txt").read_text()
text = Path("util/test/code.txt").read_text()
"""
def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    return res

def notify_if_match(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    slack_endpoint = "https://nuvolaris.dev/api/v1/web/utils/demo/slack"
    #match = re.search(pattern,text)
    matched_strings = re.findall(pattern, text)
    print(len(matched_strings))
    if len(matched_strings) > 0:
        for m in matched_strings:
            params = {"text": m}
            response = requests.post(slack_endpoint, params=params)
            if response.status_code == 200:
                print("Messaggio inviato con successo a Slack. ",m)
            else:
                print("Si è verificato un errore durante l'invio del messaggio a Slack. Codice di stato:", response.status_code, "\nmessage:", response.text)

def domain_manipulation(text):
    s=text
    pattern = r'\b[A-Za-z0-9._%+-]+@?[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    slack_endpoint = "https://nuvolaris.dev/api/v1/web/utils/demo/slack"
    #match = re.search(pattern,text)
    matched_strings = re.findall(pattern, s)
    print(len(matched_strings))
    if len(matched_strings) > 0:
        for m in matched_strings:
            if not '@' in m:
                addr=""
                try:
                    addr = socket.gethostbyname(m)
                    print("Indirizzo IP associato al hostname:", addr)
                except socket.gaierror as e:
                    print("Impossibile risolvere il hostname:", e)
                params = {"text": m}
                response = requests.post(slack_endpoint, params=params)
                if response.status_code == 200:
                    print("Messaggio inviato con successo a Slack. ",m)
                else:
                    print("Si è verificato un errore durante l'invio del messaggio a Slack. Codice di stato:", response.status_code, "\nmessage:", response.text)
                s += ",Assuming "+m+" has IP address "+addr+" answer to this question: "+addr
    return s

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)
    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Welcome to the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        output = ask(input)
        res = extract(output)
        res['output'] = output

    return {"body": res }
