import requests
import time
import json
import logging
from flask import Flask, request, render_template, jsonify
from markupsafe import escape
import os
import re

app = Flask(__name__)

'''
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scanner.log"),
        logging.StreamHandler()
    ]
)
'''

LLM_API_URL = "http://10.147.20.151:8000/generate"


def send_request(method, url, headers=None, params=None, data=None, content_type="application/x-www-form-urlencoded"):
    try:
        start = time.time()
        if content_type == "application/json":
            data = json.dumps(params)
        elif method.upper() == "GET":
            data = None
        response = requests.request(method=method, url=url, headers=headers, params=params if method.upper() == "GET" else None, data=data)
        latency = time.time() - start
        result = {
            "status_code": response.status_code,
            "length": len(response.content),
            "latency": latency,
            "body": response.text
        }
        return result
    
    except Exception as e:
        return {"error": str(e), "status_code": 0, "length": 0, "latency": 0, "body": ""}




def call_llm_for_payload(prompt: str):
    payload = {
        "model": "gemma3:4b-it-qat",
        "prompt": prompt,
        "num_predict": -1
    }
    response = requests.post(LLM_API_URL, headers={"Content-Type": "application/json"}, json=payload)
    content = response.json().get("response", "")
    print("\n\n\n\n + payload content \n\n " + content + "\n\n\n")
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    #content = content.strip()
    content = content.strip() + "]}"
    try:
      
        clean_json = json.loads(content)
        return clean_json

    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        return None




def generate_prompt(parameters, normal_values, baseline_response, vuln_type):


    param_lines = "\n".join([
        f"- {k}: {normal_values[k]} (type: {parameters.get(k, 'string')})"
        for k in normal_values
    ]) 

    prompt = f"""
                    You are a vulnerability payload generator. Based on the HTTP parameters and the server’s behavior, generate exactly one new malicious payload for the following vulnerability type: {vuln_type}. Use the context of previous payloads and server responses to generate a more effective payload. Focus on behavior changes, error messages, or other anomalies.

                    Additional Rules:
                    - Do NOT repeat any payload that was already used in previous attempts.
                    - Aim to bypass known filters, provoke different server behavior, or reveal more information.

                    Baseline Server Response:
                    - Status code: {baseline_response['status_code']}
                    - Length: {baseline_response['length']}
                    - Latency: {baseline_response['latency']:.2f}s
                    - Body (first 300 chars):  
                    {baseline_response['body']}

                    Current HTTP Parameters:
                    {param_lines}

                    Respond ONLY with raw JSON in a **single line** (minified).  
                    Do NOT include any markdown formatting, explanation, or code block markers (like ```json).  
                    Example format:
                """ + """
                    {"payloads":[{"param1":"parameter_name","value":"malicious_payload"}]}

                    Create payload for each parameter! All answer must be parsable by json dump. Observe parenthezis.
                """

    print("prompt \n\n\n" + prompt + "\n\n\n")
    return prompt.strip()


def fuzz_target(url, method, headers, parameters, normal_values, content_type, vuln_type, iterations=3):
    results = []
    baseline_response = send_request(method, url, headers, normal_values, normal_values,content_type)
#send_request(method, url, headers=None, params=None, data=None, content_type="application/x-www-form-urlencoded"):
    for i in range(iterations):
        prompt = generate_prompt(parameters, normal_values, baseline_response, vuln_type)
        injection = call_llm_for_payload(prompt)
        fuzzed_params = dict()
        if injection:
            for item in injection.get("payloads", []):
                fuzzed_params[item["param"]] = item["value"]
            print("fuzzed params \n\n\n" +str(fuzzed_params) + "\n\n\n")
            resp = send_request(method, url, headers, fuzzed_params, fuzzed_params, content_type)
            results.append({
                "injection": item,
                "response": resp
            })

    return generate_report(vuln_type, url, results)


def generate_report(vuln_type, target_url, results):
    prompt = f"""
            Based on our dialog and scanning results, summarize the scan results for vulnerability type: {vuln_type} on target: {target_url}.
            Provide a concise, professional security analysis based on the above. Provide also payloads that triggered the vulnerablity and 
            based on what you made decision that the target url is vulnerable (may be on specials words in answer and etc.)
            Answer with html insert, because your answer will be injected into html page.

            Scanning reults:
            {results}
        """
    print(results)
    payload = {
        "model": "gemma3:4b-it-qat",
        "prompt": prompt,
        "num_predict": -1
    }
    response = requests.post(LLM_API_URL, headers={"Content-Type": "application/json"}, json=payload)
    return response.json().get("response", "")[7:-3]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        method = request.form.get("method")
        cookie = request.form.get("cookie")
        content_type = request.form.get("content_type")
        iterations = int(request.form.get("iterations", 1))
        vuln_type = request.form.get("vuln_type")

        param_names = request.form.getlist("param_names")
        param_values = request.form.getlist("param_values")
        param_types = request.form.getlist("param_types")

        headers = {"Content-Type": content_type}
        if cookie:
            headers["Cookie"] = cookie

        try:
            params = {}
            types = {}
            for name, val, typ in zip(param_names, param_values, param_types):
                if name.strip():
                    params[name.strip()] = val.strip()
                    types[name.strip()] = typ.strip()

            report = fuzz_target(
                url=url,
                method=method,
                headers=headers,
                parameters=types,
                normal_values=params,
                content_type=content_type,
                vuln_type=vuln_type,
                iterations=iterations
            )
            return render_template("result.html", report=report, url=url, vuln_type=vuln_type)

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
