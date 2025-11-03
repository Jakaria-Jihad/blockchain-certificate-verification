# CertificateChain

CertificateChain is a **secure digital certificate management system** built using **Flask, Firebase Firestore, and Blockchain concepts**. It enables admins to manage student records, generate certificates, and provide verification in a tamper-proof manner. This project implements a **role-based system** for admins with different access levels and functionality.


## Features

### Admin Roles
- **Entry Admin**: Can add new student entries and view their status.
- **Editor Admin**: Can view all student entries and edit non-finalized student records.
- **Chief Admin**: Full control over all records, including finalizing student certificates, viewing logs, and downloading certificates. Can see complete certificate metadata, including serial numbers and security hex.

### Student Records
- Store student data in a **draft** and **finalized** collection.
- Blockchain-inspired hash verification for finalized records.
- Automatic certificate serial generation and security hex codes.
- Downloadable certificates in PDF format:
  - **Student version**: limited info + security hex.
  - **Chief version**: full certificate info, including serial and metadata.

### Verification
- Public verification via a **security hex code**.
- Ensures authenticity without revealing private certificate data.

### Dashboard
- Role-based dashboards with:
  - List of draft and finalized students.
  - Edit, view, finalize, and log actions based on role.
- Floating **refresh button** to reload lists dynamically.



## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Firebase Firestore
- **PDF Generation**: FPDF
- **Authentication**: Role-based session management
- **Frontend**: HTML, CSS (Dark/Mauve/Purple theme)
- **Security**: Hashing with SHA256, Blockchain-inspired data integrity


## Project Structure:

CertificateChain/
- app.py                       # Flask backend
- serviceAccountKey.json        # Firebase credentials (ignored in git)
- serviceAccountKey_example.json # Placeholder JSON for setup
- templates/                    # HTML templates
  -- admin_login.html          # Admin login page
  -- dashboard.html            # Role-based dashboard
  -- add_student.html          # Form to add new students
  -- edit_student.html         # Edit student (Entry/Editor)
  -- edit_student_chief.html   # Edit student (Chief Admin)
  -- view_student.html         # View student details
  -- view_log.html             # View student action logs
  -- verify_input.html         # Public certificate verification page
- static/                       # Static files
  --style.css                 # Unified dark/mauve/purple CSS
- .gitignore                    # Git ignore file (includes serviceAccountKey.json)
- README.md                     # Project documentation and usage guide




## Setup Instructions

### 1. Clone the Repository

git clone https://github.com/Jakaria-Jihad/blockchain-certificate-verification.git

`cd CertificateChain`


### 2. Install Dependencies

`pip install -r requirements.txt`


Dependencies include:

- flask

- firebase-admin

- fpdf


### 3. Firebase Configuration

Go to Firebase Console

- Create a new project.

- Navigate to Project Settings → Service Accounts → Generate New Private Key.

- Download the serviceAccountKey.json file. (you may need to rename it)

- Place it in the project root.

⚠️ Do not commit serviceAccountKey.json to GitHub.


### 4. Environment Variables

Set a secret key for Flask sessions (optional; defaults are provided):

`export SECRET_KEY="your_secret_key_here"`


### 5. Running the Application

`python app.py`


Open your browser at: http://127.0.0.1:5000/

Access admin login at: http://127.0.0.1:5000/admin/login


## Usage
### Admin Workflow

#### 1. Entry Admin

1. Add new students (name, major, student ID).

2. View the status of all students (cannot edit finalized records).

#### 2. Editor Admin

1. Edit existing students that are not finalized.

2. Cannot add new students or edit finalized ones.

#### 3. Chief Admin

1. Edit draft students and finalize certificates.

2. View all students (draft & finalized).

3. Access detailed logs, certificate serial, and security hex.

4. Download student and chief versions of certificates.

### Public Verification

1. Navigate to /verify.

2. Enter the Security Hex from a certificate to verify authenticity.

## Future Enhancements

1. Multi-factor Authentication for admins.

2. PDF Logs download for auditing.

3. Notification System when students are finalized.

4. Role Management Panel for dynamic admin roles.

5. Analytics Dashboard to track student certificates and verification statistics.

## 🔒 Security Notes

**Never commit serviceAccountKey.json to GitHub.**

**Finalized student data is immutable after blockchain hashing.**

**Only the Chief Admin can access the full certificate metadata.**

## 📬 Contact

Developed as a demonstration of a secure certificate management system.
For inquiries, contact:

Md. Jakaria Hossain Jihad

📧 jakariahossen669@gmail.com

🏫 jakaria.jihad@northsouth.edu
