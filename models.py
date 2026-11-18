from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # creating an object from SQLAlchemy class

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String, nullable = False)
    course_name = db.Column(db.String, nullable = False)
    status = db.Column(db.Enum('Active', 'Inactive'), nullable = False, default = 'Active')


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Approve')


class Examination(db.Model):
    __tablename__ = 'examination'
    exam_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    course = db.relationship('Course', backref='examinations')

class Slot(db.Model):
    __tablename__ = 'slot'
    slot_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('examination.exam_id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('Approve', 'Reject', name='slot_status'), nullable=False)
    examination = db.relationship('Examination', backref='slots')
    examiner = db.relationship('Users', backref='examiner_slots', foreign_keys=[examiner_id])

    # counting no. of bookings having status Booked for a particular slot
    # self --> to refer current slot object
    # self.bookings --> to return all bookings record associated with the current slot
    def booked(self):
        return len([b for b in self.bookings if b.status == 'Booked'])

class Booking(db.Model):
    __tablename__ = 'booking'
    booking_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slot.slot_id'), nullable=False)
    status = db.Column(db.Enum('Booked', 'Cancelled', name='booking_status'), nullable=False, default='Booked')
    total_marks = db.Column(db.Integer)
    remarks = db.Column(db.String(255))
    student = db.relationship('Users', backref='student_bookings', foreign_keys=[student_id])
    slot = db.relationship('Slot', backref='bookings')
