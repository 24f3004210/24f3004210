from flask import current_app as app
from flask import render_template, request, redirect, url_for, session
from models import *
from datetime import datetime, date, timedelta

# timedelta: duration or time difference between two dates or times.

#--------------------------------------------------------------------------------------------

@app.route("/")   #decorator  ("/") it is the root route of the application
def home():
    return "Zia, Copyright 2024"  

#--------------------------------------------------------------------------------------------
 
@app.route("/login", methods=["GET","POST"])     # route name is login and function name is signin
def signin():
    err_msg = None
    if request.method=="POST":
        uname = request.form.get("Email")   # data from front end form
        pwd = request.form.get("Password")    
    # check user credentials
        user = db.session.query(Users).filter(Users.email==uname, Users.password_hash==pwd).first()   # only checking the first record as the email id is unique
    # if user does not exist
        if not user:
            err_msg = "Invalid email or password."
            return render_template("login.html", err_msg=err_msg)
        if user.role == "Examiner" and user.status != "Approve":
            err_msg = "Account not approved yet"
            return render_template("login.html", err_msg=err_msg)
        session["user_id"] = user.id  # store user id in session for future use
        session["role"] = user.role  # store user role in session for future use
    # if admin redirect to admin dashboard
        if user.role == "Admin":
            return redirect(url_for("admin_dashboard"))
        elif user.role == "Examiner":
            return redirect(url_for("examiner_dashboard"))
        else:
            return redirect(url_for("student_dashboard"))

    return render_template("login.html")

#--------------------------------------------------------------------------------------------

@app.route("/register", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        uname = request.form.get("Email")
        pwd = request.form.get("Password")
        full_name = request.form.get("f_name")
        role = request.form.get("user_type")
        phno = request.form.get("phone")
        dept = request.form.get("Department")

        # check if user already exists
        if role not in ["Examiner", "Student"]:
            return render_template("signup.html", err_msg="Please select the user type.")
        user = db.session.query(Users).filter(Users.email == uname).first()
        if user:
            return render_template("signup.html", err_msg="User already exists.")
        else:
            # storing data in Users in database
            status = "Approve"
            msg = "Registration successful."
            if role == "Examiner":
                status = "Pending"
                msg = "Successfully registered as Examiner. Please wait for admin approval"
            uc = Users(email=uname, password_hash=pwd, full_name=full_name, role=role, phone=phno, department=dept, status=status)
            db.session.add(uc)
            db.session.commit()   # save in the database

            return render_template("login.html", err_msg = msg)
        
    # request type is get 
    return render_template("signup.html")

#--------------------------------------------------------------------------------------------

@app.route("/logout")
def signout():
    session.clear()  # to clear session data
    return redirect(url_for("signin"))  # redirect to login page after logout

#--------------------------------------------------------------------------------------------

@app.route("/admin")
def admin_dashboard():
    if not logged_in("Admin"):   # authentication and access for admin
        return redirect(url_for("signin"))
    courses = get_courses()
    examinations = get_examinations()
    examiners = get_examiners()
    # getting slots data and ordering by slot_date
    slots = db.session.query(Slot).order_by(Slot.slot_date).all()
    # getting bookings data
    bookings = db.session.query(Booking).all()
    return render_template("admin_dashboard.html", Courses=courses, Examinations=examinations, Examiners=examiners, Slots=slots, Bookings=bookings)

#--------------------------------------------------------------------------------------------

@app.route("/course", methods=["GET","POST"])
def course():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    if request.method == "POST":
        id = request.form.get("id")
        course_code = request.form.get("course_code")
        name = request.form.get("name")
        status = request.form.get("status")
        # searching course from database using course_id
        old_course = db.session.query(Course).filter(Course.course_id == id).first()
        # checking for duplicate course code
        same_code = db.session.query(Course).filter(Course.course_code == course_code).first()
        # if we found the same then
        if same_code and same_code != old_course:
            return render_template("course.html", course=old_course, err_msg="Course code already exists")
        #now updating the existing course
        if old_course:
            old_course.course_code = course_code
            old_course.course_name = name
            old_course.status = status
        else:
            new_course = Course(course_code=course_code, course_name = name, status=status)
            db.session.add(new_course)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    # when user clicks on edit button
    id = request.args.get("id")
    old_course = db.session.query(Course).filter(Course.course_id == id).first()
    return render_template("course.html", course=old_course)

#---------------------------------------------------------------------------------------------

# This route is not for specific template
# it will dellte the specific course record

@app.route("/delete_course")
def delete_course():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    id = request.args.get("id")
    old_course = db.session.query(Course).filter(Course.course_id == id).first()
    if old_course.examinations:
        return redirect(url_for("admin_dashboard", err_msg="Course is having examinations. Delete them first."))
    db.session.delete(old_course)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#-----------------------------------------------------------------------------------------------------

@app.route("/exam", methods=["GET","POST"])
def examination():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    if request.method == "POST":
        id = request.form.get("id")
        course_code = request.form.get("course_code")
        name = request.form.get("name")
        exam_type = request.form.get("exam_type")
        duration = int(request.form.get("duration"))
        max_marks = int(request.form.get("max_marks"))
        old_exam = db.session.query(Examination).filter(Examination.exam_id == id).first()
        found_course = db.session.query(Course).filter(Course.course_code == course_code).first()
        if not found_course:
            return render_template("examination.html", exam=old_exam, err_msg="Course code not found")
        if old_exam:
            old_exam.course_id = found_course.course_id
            old_exam.name = name
            old_exam.exam_type = exam_type
            old_exam.duration = duration
            old_exam.max_marks = max_marks
        else:
            new_exam = Examination(course_id=found_course.course_id, name=name, exam_type=exam_type, duration=duration, max_marks=max_marks)  
            db.session.add(new_exam)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    id = request.args.get("id")
    old_exam = db.session.query(Examination).filter(Examination.exam_id == id).first()
    return render_template("examination.html", exam=old_exam)

#----------------------------------------------------------------------------------------------------------------------------------

@app.route("/delete_exam")
def delete_examination():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    id = request.args.get("id")
    old_exam = db.session.query(Examination).filter(Examination.exam_id == id).first()
    if old_exam.slots:
        return redirect(url_for("admin_dashboard", err_msg="Examination has slots. Remove them first."))
    db.session.delete(old_exam)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#-----------------------------------------------------------------------------------------------

# Examiner related routes

@app.route("/examiner")
def examiner_dashboard():
    if not logged_in("Examiner"):
        return redirect (url_for("signin"))
    examinations = get_examinations()
    slots = db.session.query(Slot).filter(Slot.examiner_id == session["user_id"]).order_by(Slot.slot_date).all()
    return render_template("examiner_dashboard.html", Examinations=examinations, Slots=slots, err_msg=request.args.get("err_msg"))

#------------------------------------------------------------------------------------------------

@app.route("/v_e")
def view_examiner():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    id = request.args.get("id")
    examiner = db.session.query(Users).filter(Users.id == id).first()
    return render_template("view_examiner.html", examiner=examiner)

#--------------------------------------------------------------------------------------------------

@app.route("/u_e", methods=["POST"])
def update_examiner():
    if not logged_in("Admin"):
        return redirect(url_for("signin"))
    id = request.form.get("id")
    full_name = request.form.get("Name")
    phone = request.form.get("contact_details")
    department = request.form.get("department")
    status = request.form.get("status")
    old_examiner = db.session.query(Users).filter(Users.id == id).first()
    # To update the values
    old_examiner.full_name = full_name
    old_examiner.phone = phone
    old_examiner.department = department
    old_examiner.status = status
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#-------------------------------------------------------------------------------------------

@app.route("/c_e_s", methods=["GET","POST"])
def create_edit_slots():
    if not logged_in("Examiner"):
        return redirect(url_for("signin"))
    uid = session["user_id"]
    if request.method == "POST":
        id = request.form.get("id")
        exam_id = request.form.get("exam_id")
        slot_date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
        start_time = datetime.strptime(request.form.get("start_time"), "%H:%M").time()
        end_time = datetime.strptime(request.form.get("end_time"), "%H:%M").time()
        capacity = int(request.form.get("capacity"))
        status = request.form.get("status")
        old_slot = db.session.query(Slot).filter(Slot.slot_id == id, Slot.examiner_id == uid).first()
        exam = db.session.query(Examination).filter(Examination.exam_id == exam_id).first()
        err_msg = None
        if not exam:
            err_msg = "Examination not found."
        elif end_time <= start_time:
            err_msg = "End time must be after start time"
        elif slot_date < date.today():
            err_msg = "Slot date cannot be in the past"
        elif old_slot and old_slot.booked() > 0:
            err_msg = "Slot already booked"
        if err_msg:
            return render_template("create_edit_slots.html", slot=old_slot, exam_id=exam_id, err_msg=err_msg)
        if old_slot:
            old_slot.exam_id = exam.exam_id
            old_slot.slot_date = slot_date
            old_slot.start_time = start_time
            old_slot.end_time = end_time
            old_slot.capacity = capacity
            old_slot.status = status
        else:
            new_slot = Slot(exam_id=exam.exam_id, examiner_id = uid, slot_date=slot_date, start_time=start_time, end_time=end_time, capacity=capacity, status=status)
            db.session.add(new_slot)
        db.session.commit()
        return redirect(url_for("examiner_dashboard"))
    slot_id = request.args.get("slot_id")
    exam_id = request.args.get("exam_id")
    slot = db.session.query(Slot).filter(Slot.slot_id == slot_id, Slot.examiner_id==uid).first()
    if slot:
        exam_id = slot.exam_id
    return render_template("create_edit_slots.html", slot=slot, exam_id=exam_id)

#---------------------------------------------------------------------------------------------------------

@app.route("/d_s")
def delete_slot():
    if not logged_in("Examiner"):
        return redirect(url_for("signin"))
    id = request.args.get("id")
    old_slot = db.session.query(Slot).filter(Slot.slot_id==id, Slot.examiner_id==session["user_id"]).first()
    if old_slot and old_slot.bookings:
        return redirect(url_for("examiner_dashboard", err_msg="Slot already has booking."))
    if old_slot:
        db.session.delete(old_slot)
        db.session.commit()
    return redirect(url_for("examiner_dashboard"))

#--------------------------------------------------------------------------------------------------------

@app.route("/r_s", methods=["GET","POST"])
def registered_students():
    if not logged_in("Examiner"):
        return redirect(url_for("signin"))
    if request.method == "POST":
        booking_id = request.form.get("booking_id")
        marks = int(request.form.get("marks"))
        booking = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking or booking.slot.examiner_id != session["user_id"]:
            return redirect(url_for("examiner_dashboard"))
        slot_id = booking.slot_id
        if marks < 0 or marks > booking.slot.examination.max_marks:
            return redirect(url_for("registered_students", slot_id=slot_id, err_msg="Marks must be between 0 and the max marks."))
        booking.total_marks = marks
        booking.remarks = request.form.get("remarks")
        db.session.commit()
        return redirect(url_for("registered_students", slot_id=slot_id))
    slot_id = request.args.get("slot_id")
    slot = db.session.query(Slot).filter(Slot.slot_id == slot_id, Slot.examiner_id == session["user_id"]).first()
    if not slot:
        return redirect(url_for("examiner_dashboard"))
    bookings = [b for b in slot.bookings if b.status == "Booked"]
    return render_template("registered_students.html", slot=slot, Bookings=bookings, err_msg=request.args.get("err_msg"))

#--------------------------------------------------------------------------------------------------------------------------------

@app.route("/student")
def student_dashboard():
    if not logged_in("Student"):
        return redirect(url_for("signin"))
    uid = session["user_id"]
    slots = get_available_slots(uid)
    bookings = db.session.query(Booking).filter(Booking.student_id == uid).order_by(Booking.booking_id.desc()).all()
    return render_template("student_dashboard.html", Slots=slots, Bookings=bookings, today=date.today(), err_msg=request.args.get("err_msg"))

#---------------------------------------------------------------------------------------------------------------------------------------------------

@app.route("/book")
def book_slot():
    if not logged_in("Student"):
        return redirect(url_for("signin"))
    uid = session["user_id"]
    slot_id = request.args.get("slot_id")
    slot = db.session.query(Slot).filter(Slot.slot_id == slot_id).first()
    if not slot or slot not in get_available_slots(uid):
        return redirect(url_for("student_dashboard", err_msg="This slot is not available for booking."))
    new_booking = Booking(student_id=uid, slot_id=slot.slot_id, status="Booked")
    db.session.add(new_booking)
    db.session.commit()
    if slot.booked() >= slot.capacity:
        slot.status = "Reject"
        db.session.commit()
    return redirect(url_for("student_dashboard"))

#-----------------------------------------------------------

def get_available_slots(student_id):
    my_bookings = db.session.query(Booking).filter(Booking.student_id == student_id, Booking.status == "Booked").all()
    booked_exams = [b.slot.exam_id for b in my_bookings]
    all_slots = db.session.query(Slot).filter(Slot.status == "Approve", Slot.slot_date >= date.today()).all()
    slots = []
    for slot in all_slots:
        if slot.booked() < slot.capacity and slot.exam_id not in booked_exams:
            slots.append(slot)
    return slots

#------------------------------------------------------------------------------------------

@app.route("/cancel")
def cancel_booking():
    if not logged_in("Student"):
        return redirect(url_for("signin"))
    booking_id = request.args.get("booking_id")
    booking = db.session.query(Booking).filter(Booking.booking_id == booking_id, Booking.student_id == session["user_id"]).first()
    if booking and booking.status == "Booked" and booking.slot.slot_date >= date.today():
        slot = booking.slot
        was_full = slot.booked() >= slot.capacity
        booking.status = "Cancelled"
        if was_full and slot.status == "Reject":
            slot.status = "Approve"
        db.session.commit()
    return redirect(url_for("student_dashboard"))

#---------------------------------------------------------------------------------------------------------------------------

# additional python functions

def logged_in(role):
    return session.get("role") == role

def get_courses():
    courses = db.session.query(Course).all()
    return courses

def get_examinations():
    examinations = db.session.query(Examination).all()
    return examinations

def get_examiners():
    examiners = db.session.query(Users).filter(Users.role == 'Examiner').all()
    return examiners

