from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
import random, string, datetime, hashlib, os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Genesis block
genesis_ref = db.collection("blockchain").document("genesis_block")
if not genesis_ref.get().exists:
    genesis_block = {
        "system_id": "CERTCHAIN_SYS",
        "created_at": datetime.datetime.now().isoformat(),
        "previous_hash": None,
        "block_hash": hashlib.sha256(b"CERTCHAIN_GENESIS").hexdigest()
    }
    genesis_ref.set(genesis_block)

# Helpers
def generate_hex_code(length=12):
    return ''.join(random.choices(string.hexdigits.upper(), k=length))

def generate_cert_serial(student_id):
    date = datetime.datetime.now().strftime("%Y%m")
    return f"{student_id}-{date}"

def hash_block(data):
    block_string = str(data).encode()
    return hashlib.sha256(block_string).hexdigest()

# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("home.html")

# Admin Login
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "")

        admin_doc = db.collection("admins").document(admin_id).get()
        if not admin_doc.exists:
            flash("Admin not found.", "danger")
            return render_template("admin_login.html")
        admin = admin_doc.to_dict()
        role = (admin.get("role") or "").lower()
        if admin.get("password") != password:
            flash("Invalid password.", "danger")
            return render_template("admin_login.html")

        session['admin_id'] = admin_id
        session['role'] = role
        flash(f"Welcome, {role.capitalize()} Admin!", "success")

        # Redirect to role dashboard
        if role == "entry":
            return redirect(url_for("entry_dashboard"))
        elif role == "editor":
            return redirect(url_for("editor_dashboard"))
        elif role == "chief":
            return redirect(url_for("chief_dashboard"))
        else:
            flash("Unknown role assigned. Contact admin.", "danger")
            session.clear()
            return render_template("admin_login.html")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

# ---------------- Dashboards ----------------
@app.route("/admin/entry_dashboard", methods=["GET"])
def entry_dashboard():
    if session.get('role') != "entry":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("admin_login"))
    drafts = [d.to_dict() for d in db.collection("students_draft").stream()]
    finals = [f.to_dict() for f in db.collection("students_final").stream()]
    students = drafts + finals
    return render_template("dashboard.html", students=students, role="entry")

@app.route("/admin/editor_dashboard", methods=["GET"])
def editor_dashboard():
    if session.get('role') != "editor":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("admin_login"))
    drafts = [d.to_dict() for d in db.collection("students_draft").stream()]
    finals = [f.to_dict() for f in db.collection("students_final").stream()]
    students = drafts + finals
    return render_template("dashboard.html", students=students, role="editor")

@app.route("/admin/chief_dashboard", methods=["GET"])
def chief_dashboard():
    if session.get('role') != "chief":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("admin_login"))
    drafts = [d.to_dict() for d in db.collection("students_draft").stream()]
    finals = [f.to_dict() for f in db.collection("students_final").stream()]
    students = drafts + finals
    return render_template("dashboard.html", students=students, role="chief")

# ---------------- Add Student ----------------
@app.route("/admin/add_student", methods=["GET", "POST"])
def add_student():
    if 'admin_id' not in session:
        flash("Please login first", "danger")
        return redirect(url_for("admin_login"))

    role = session.get('role')
    if role not in ["entry", "chief"]:
        flash("Only Entry or Chief Admin can add students", "danger")
        if role == "editor":
            return redirect(url_for("editor_dashboard"))
        return redirect(url_for("home"))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        major = request.form.get("major", "").strip()

        # Build student doc (entry shouldn't set birth_date/cgpa)
        student = {
            "student_id": student_id,
            "name": name,
            "major": major,
            "admin_chain": [
                {
                    "admin_id": session.get("admin_id"),
                    "role": role,
                    "actions": ["added student"],
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ],
            "timestamp": datetime.datetime.now().isoformat(),
            "finalized": False  # explicitly set finalized flag
        }

        # If chief uses add_student and included birth/cgpa, accept them
        if role == "chief":
            birth_date = request.form.get("birth_date", "").strip()
            cgpa = request.form.get("cgpa", "").strip()
            if birth_date:
                student["birth_date"] = birth_date
            if cgpa:
                try:
                    student["cgpa"] = float(cgpa)
                except:
                    pass

        db.collection("students_draft").document(student_id).set(student)
        flash("Student added to drafts", "success")
        return redirect(url_for(f"{role}_dashboard"))

    return render_template("add_student.html", role=role)

# ---------------- Edit Student (editor & chief) ----------------
@app.route("/admin/edit_student/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if 'admin_id' not in session or session.get('role') not in ["editor", "chief"]:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("admin_login"))

    role = session.get('role')

    # Prefer draft (non-finalized) document; fallback to final
    draft_doc = db.collection("students_draft").document(student_id).get()
    final_doc = db.collection("students_final").document(student_id).get()

    student = None
    is_finalized = False
    if draft_doc.exists:
        student = draft_doc.to_dict()
        is_finalized = False
        student_doc_ref = db.collection("students_draft").document(student_id)
    elif final_doc.exists:
        student = final_doc.to_dict()
        is_finalized = True
        student_doc_ref = db.collection("students_final").document(student_id)
    else:
        flash("Student not found!", "danger")
        return redirect(url_for(f"{role}_dashboard"))

    # Editors & Chief should NOT be allowed to edit finalized records
    if request.method == "POST":
        if is_finalized:
            flash("Cannot edit a finalized student.", "danger")
            return redirect(url_for(f"{role}_dashboard"))

        # Editor cannot change student_id; name editable by chief only
        if role == "editor":
            # editor edits major, birth_date, cgpa
            student["major"] = request.form.get("major", student.get("major","")).strip()
            student["birth_date"] = request.form.get("birth_date", student.get("birth_date","")).strip()
            cgpa = request.form.get("cgpa", "")
            if cgpa:
                try:
                    student["cgpa"] = float(cgpa)
                except:
                    pass
        else:  # chief
            student["name"] = request.form.get("name", student.get("name","")).strip()
            student["major"] = request.form.get("major", student.get("major","")).strip()
            student["birth_date"] = request.form.get("birth_date", student.get("birth_date","")).strip()
            cgpa = request.form.get("cgpa", "")
            if cgpa:
                try:
                    student["cgpa"] = float(cgpa)
                except:
                    pass

        # append to admin_chain
        admin_chain = student.get("admin_chain", [])
        admin_chain.append({
            "admin_id": session.get("admin_id"),
            "role": role,
            "actions": ["edited student"],
            "timestamp": datetime.datetime.now().isoformat()
        })
        student["admin_chain"] = admin_chain

        # Save to draft (should be in draft if not finalized)
        student_doc_ref.set(student)
        flash("Student updated successfully!", "success")
        return redirect(url_for(f"{role}_dashboard"))

    # GET: render edit form
    return render_template("edit_student.html", student=student, role=role, is_finalized=is_finalized)

# ---------------- Chief view (full) ----------------
@app.route("/admin/view_student/<student_id>", methods=["GET"])
def view_student(student_id):
    if 'admin_id' not in session or session.get('role') != "chief":
        flash("Only Chief Admin can view full details", "danger")
        return redirect(url_for("admin_login"))

    draft_doc = db.collection("students_draft").document(student_id).get()
    final_doc = db.collection("students_final").document(student_id).get()
    student = None
    if draft_doc.exists:
        student = draft_doc.to_dict()
    elif final_doc.exists:
        student = final_doc.to_dict()

    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("chief_dashboard"))

    return render_template("view_student.html", student=student)

# ---------------- Finalize (chief) ----------------
@app.route("/admin/finalize/<student_id>", methods=["GET"])
def finalize_student(student_id):
    if 'admin_id' not in session or session.get('role') != "chief":
        flash("Only Chief Admin can finalize", "danger")
        return redirect(url_for("admin_login"))

    draft_ref = db.collection("students_draft").document(student_id)
    draft_doc = draft_ref.get()
    if not draft_doc.exists:
        flash("Draft not found", "danger")
        return redirect(url_for("chief_dashboard"))

    student = draft_doc.to_dict()
    student["certificate_serial"] = generate_cert_serial(student_id)
    student["security_hex"] = generate_hex_code()
    student["timestamp_finalized"] = datetime.datetime.now().isoformat()
    student["block_hash"] = hash_block(student)
    student["finalized"] = True

    db.collection("students_final").document(student_id).set(student)
    db.collection("blockchain").document(student_id).set(student)
    draft_ref.delete()

    flash(f"Student {student_id} finalized", "success")
    return redirect(url_for("chief_dashboard"))

# ---------------- View Logs (chief) ----------------
@app.route("/admin/view_log/<student_id>", methods=["GET"])
def view_log(student_id):
    if 'admin_id' not in session or session.get('role') != "chief":
        flash("Only Chief Admin can view logs", "danger")
        return redirect(url_for("admin_login"))

    draft_doc = db.collection("students_draft").document(student_id).get()
    final_doc = db.collection("students_final").document(student_id).get()
    student = None
    if draft_doc.exists:
        student = draft_doc.to_dict()
    elif final_doc.exists:
        student = final_doc.to_dict()

    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("chief_dashboard"))

    return render_template("view_log.html", student=student)

# ---------------- Download PDF ----------------
@app.route("/download/<student_id>")
def download_pdf(student_id):
    # Download always pulls from students_final (only finalized documents)
    final_doc = db.collection("students_final").document(student_id).get()
    if not final_doc.exists:
        flash("Finalized certificate not found", "danger")
        return redirect(url_for("home"))
    student = final_doc.to_dict()

    mode = request.args.get("mode", "user")  # "user" or "chief"

    # If chief mode is requested, verify caller is chief
    if mode == "chief" and session.get("role") != "chief":
        flash("Only Chief Admin can download the chief version", "danger")
        return redirect(url_for("home"))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Certificate Chain Certificate", ln=True, align="C")
    pdf.ln(8)
    pdf.cell(200, 8, txt=f"Name: {student.get('name')}", ln=True)
    pdf.cell(200, 8, txt=f"Student ID: {student.get('student_id')}", ln=True)
    pdf.cell(200, 8, txt=f"Birth Date: {student.get('birth_date','N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Major: {student.get('major')}", ln=True)
    pdf.cell(200, 8, txt=f"CGPA: {student.get('cgpa','N/A')}", ln=True)

    # Student/public version: basic + security hex
    pdf.ln(4)
    pdf.cell(200, 8, txt=f"Security Hex: {student.get('security_hex')}", ln=True)

    # Chief version includes extra details
    if mode == "chief":
        pdf.ln(4)
        pdf.cell(200, 8, txt=f"Certificate Serial: {student.get('certificate_serial','N/A')}", ln=True)

    filename = f"{student_id}_certificate_{mode}.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)

# ---------------- Verify (public) ----------------
@app.route("/verify", methods=["GET", "POST"])
def verify_input():
    student = None
    searched = False
    if request.method == "POST":
        searched = True
        code = request.form.get("security_hex", "").strip()
        finals = db.collection("students_final").stream()
        for f in finals:
            s = f.to_dict()
            if s.get("security_hex") == code:
                student = s
                break
    return render_template("verify_input.html", student=student, searched=searched)

# Run
if __name__ == "__main__":
    app.run(debug=True)
