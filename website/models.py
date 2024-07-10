from . import db
from flask_login import UserMixin

class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(100), nullable=False)
    LastName = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.String(50), nullable=False)

    def get_id(self):
        return self.UserID

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': Role
    }

class Admin(Users):
    __tablename__ = 'Admin'
    AdminID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

class Teacher(Users):  # Changed from Teachers to Teacher for consistency
    __tablename__ = 'Teachers'
    TeacherID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)

    subjects = db.relationship('Subjects', secondary='TeacherSubjects', backref=db.backref('teachers', lazy='dynamic'))
    predicted_grades = db.relationship('PredictedGrades', backref='predictedgrades_teacher', lazy=True, overlaps="teachers,predicted_grades")

    __mapper_args__ = {
        'polymorphic_identity': 'teacher',
    }

class Student(Users):  # Changed from Students to Student for consistency
    __tablename__ = 'Students'
    StudentID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)
    Grade = db.Column(db.Integer, nullable=False)
    Total = db.Column(db.Integer, nullable=True)

    subjects = db.relationship('Subjects', secondary='StudentsSubjects', backref=db.backref('students', lazy='dynamic'))
    predicted_grades = db.relationship('PredictedGrades', backref='predictedgrades_student', lazy=True, overlaps="students,predicted_grades")

    __mapper_args__ = {
        'polymorphic_identity': 'student',  # Ensure this matches the Role value
    }

class Subjects(db.Model):
    __tablename__ = 'Subjects'
    SubjectID = db.Column(db.Integer, primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    Level = db.Column(db.String(100), nullable=True) #change nullable to true


class StudentsSubjects(db.Model):
    __tablename__ = 'StudentsSubjects'
    StudentID = db.Column(db.Integer, db.ForeignKey('Students.StudentID'), primary_key=True)
    SubjectID = db.Column(db.Integer, db.ForeignKey('Subjects.SubjectID'), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=True)

class TeacherSubjects(db.Model):
    __tablename__ = 'TeacherSubjects'
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teachers.TeacherID'), primary_key=True)
    SubjectID = db.Column(db.Integer, db.ForeignKey('Subjects.SubjectID'), primary_key=True)
    SubjectName = db.Column(db.String(100), nullable=True)

class PredictedGrades(db.Model):
    __tablename__ = 'PredictedGrades'
    StudentID = db.Column(db.Integer, db.ForeignKey('Students.StudentID'), primary_key=True, nullable=True)
    SubjectID = db.Column(db.Integer, db.ForeignKey('Subjects.SubjectID'), primary_key=True, nullable=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teachers.TeacherID'), nullable=True)
    StudentPredictedGrade = db.Column(db.VARCHAR(100), nullable=True) #change db.Integer to varchar
    TeacherPredictedGrade = db.Column(db.VARCHAR(100), nullable=True)
    Comment = db.Column(db.String(255), nullable=True)
    
    student = db.relationship('Student', backref=db.backref('predictedgrades_student', lazy=True, overlaps="predicted_grades,students"))
    teacher = db.relationship('Teacher', backref=db.backref('predictedgrades_teacher', lazy=True, overlaps="teachers,predicted_grades"))
    subject = db.relationship('Subjects', backref=db.backref('predictedgrades', lazy=True))
