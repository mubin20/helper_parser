from flask import Flask, request, render_template_string
import fitz  # PyMuPDF
import re

app = Flask(__name__)

# ===== Helper Functions =====
def extract_text_from_pdf(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return re.sub(r"\s+", " ", text)

def regex_search(pattern, text, default="Not Found"):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default

def extract_fields(text):
    fields = {}
    fields["Name"] = regex_search(r"NAME NAMA\s*:\s*(.*?)\s*TEMPAT,? TGL LAHIR", text)
    fields["Birthplace & DOB"] = regex_search(r"TEMPAT,? TGL LAHIR\s*:\s*(.*?)\s*AGE UMUR", text)
    fields["Age"] = regex_search(r"AGE UMUR\s*:\s*(.*?)\s*GENDER JENIS KELAMIN", text)
    fields["Gender"] = regex_search(r"GENDER JENIS KELAMIN\s*:\s*(.*?)\s*HEIGHT", text)
    fields["Education"] = regex_search(r"EDUCATION PENDIDIKAN\s*:\s*(.*?)\s*GRADUATION", text)
    fields["Religion"] = regex_search(r"RELIGIONA? AGAMA\s*:\s*(.*?)\s*LANGUAGE", text)
    fields["Language"] = regex_search(r"LANGUAGE BAHASA\s*:\s*(.*?)\s*PARENT ORANG TUA", text)
    fields["Marital Status"] = regex_search(r"STATUS PERKAWINAN\s*:\s*(.*?)\s*CHILD", text)
    
    # Children
    boys = regex_search(r"BOY LAKI-LAKI\s*:?\s*AGE UMUR\s*:\s*(\d+)", text, default="")
    girls = regex_search(r"GIRL PEREMPUAN\s*:?\s*AGE UMUR\s*:\s*(\d+)", text, default="")
    count = 0
    if boys: count += 1
    if girls: count += 1
    fields["No. of Children"] = str(count)

    # Work Experience
    work_block = regex_search(r"WORK EXPERIENCE PENGALAMAN KERJA(.*?)EMPLOYMENT HISTORY", text, default="")
    work_lines = re.findall(r"(INDONESIAN|SINGAPORE)\s+(\d{4})\s*Y\s*-\s*(\d{4})\s*Y", work_block)

    experience_output = []
    is_ex_sg = False
    for country, start, end in work_lines:
        if country.upper() == "SINGAPORE":
            is_ex_sg = True
        try:
            years = int(end) - int(start)
        except:
            years = "?"
        experience_output.append(f"{start}-{end} ({years} yrs) - {country.title()}")

    fields["Work Experience"] = "<br>".join(experience_output) if experience_output else "Not Found"
    fields["Ex-Singapore Status"] = "Yes" if is_ex_sg else "No"

    return fields

# ===== HTML Template =====
HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>Helper Biodata Parser</title></head>
<body style="font-family:Arial;padding:40px;">
<h2>Upload Helper Biodata PDF</h2>
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="pdf" accept=".pdf" required><br><br>
  <input type="submit" value="Upload & Extract">
</form>
</body>
</html>
"""

HTML_RESULT = """
<!DOCTYPE html>
<html>
<head><title>Parsed Biodata</title></head>
<body style="font-family:Arial;padding:40px;">
<h2>✅ Extracted Helper Biodata</h2>
<ul>
{% for k, v in fields.items() %}
  <li><strong>{{ k }}:</strong> {{ v|safe }}</li>
{% endfor %}
</ul>
<a href="/">⬅️ Back to upload another file</a>
</body>
</html>
"""

# ===== Routes =====
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files["pdf"]
        text = extract_text_from_pdf(file)
        fields = extract_fields(text)
        return render_template_string(HTML_RESULT, fields=fields)
    return HTML_FORM

# ===== Main =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
