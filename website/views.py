from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from functools import wraps
from . import db
from . import models
from sqlalchemy.orm import aliased
from sqlalchemy import func



views = Blueprint('views', __name__)

# Role-based access control decorator
def role_required(role):
    def wrapper(func):
        @wraps(func)
        @login_required
        def decorated_view(*args, **kwargs):
            if current_user.Role != role:
                flash(f"You do not have access to the {role}'s dashboard.", category="error")
                return redirect(url_for(f'views.{current_user.Role}_dashboard'))
            return func(*args, **kwargs)
        return decorated_view
    return wrapper


def get_diploma_points(tok_grade, ee_grade):
    # Define the mapping based on the provided table
        points_matrix = {
            'A': {'A': 3, 'B': 3, 'C': 2, 'D': 2, 'E': 'Failing condition'},
            'B': {'A': 3, 'B': 2, 'C': 2, 'D': 1, 'E': 'Failing condition'},
            'C': {'A': 2, 'B': 2, 'C': 2, 'D': 1, 'E': 'Failing condition'},
            'D': {'A': 2, 'B': 1, 'C': 1, 'D': 0, 'E': 'Failing condition'},
            'E': {'A': 'Failing condition', 'B': 'Failing condition', 'C': 'Failing condition', 'D': 'Failing condition', 'E': 'Failing condition'},
        }
        # Get the points from the matrix
        points = points_matrix.get(ee_grade, {}).get(tok_grade, 0)
        return points





@views.route('/admin',  methods=['GET', 'POST'])
@role_required('admin')
def admin_dashboard():
    query = request.args.get('query', '')
    students = models.Student.query.all()
    predicted_grades = models.PredictedGrades.query.all()

    if query:
        # Search for students by name (FirstName or LastName)
        students = models.Student.query.filter(
            (models.Student.FirstName.ilike(f'%{query}%')) | 
            (models.Student.LastName.ilike(f'%{query}%'))
        ).all()

    

    if request.method == 'POST':
        student_id = request.form.get('student_id')
         # Fetching EE and TOK grades for the logged-in student
        ee_grade_row = db.session.query(models.PredictedGrades.TeacherPredictedGrade).filter_by(
            StudentID=student_id,
            SubjectID=29  # Subject ID for EE
        ).first()

        tok_grade_row = db.session.query(models.PredictedGrades.TeacherPredictedGrade).filter_by(
            StudentID=student_id,
            SubjectID=30  # Subject ID for TOK
        ).first()

        # Extract the grades from the query results
        ee_grade = ee_grade_row[0] if ee_grade_row else None
        tok_grade = tok_grade_row[0] if tok_grade_row else None

        # Fetching the total predicted grades for the logged-in student
        total_predicted_grades = db.session.query(func.sum(models.PredictedGrades.TeacherPredictedGrade)
        ).filter_by(StudentID=student_id).scalar() + get_diploma_points(tok_grade, ee_grade)
        student =  models.Student.query.filter_by(StudentID=student_id).first()
        student.Total =  total_predicted_grades
        try:
            db.session.commit()
            flash('Predicted Grade Calculated Successfully', category='success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', category='error')
    return render_template("admin.html", admin=current_user, predicted_grades=predicted_grades, students=students, query=query)

@views.route('/choose_subject', methods=['GET', 'POST'])
@role_required('teacher')
def choose_subject():
    subjects = models.Subjects.query.all()
    try:
        if request.method == 'POST':
            subject_name = request.form.get('subject')
            if subject_name:
                subject_id, subject_name = subject_name.split('|')
            subject = models.Subjects.query.filter_by(SubjectID=subject_id).first()
            
            # Count the number of subjects the teacher is currently enrolled in
            subject_count = db.session.query(models.TeacherSubjects).filter_by(TeacherID=current_user.UserID).count()

            if subject_count >= 1:
                flash('You cannot add more than 1 subject', category='error')
                return redirect(url_for("views.teacher_dashboard"))

            if subject:
                teacher_subject = models.TeacherSubjects(TeacherID=current_user.UserID, SubjectID=subject.SubjectID, SubjectName =subject_name)
                try:
                    db.session.add(teacher_subject)
                    db.session.commit()
                    flash('Added Subject', category="success")
                    return redirect(url_for("views.teacher_dashboard"))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error: {e}', category="error")
            else:
                flash('Subject not found', category="error")
            

    except:
        flash('Subject Already Added', category="error")
        return redirect(url_for("views.choose_subject"))
    return render_template("choose_subject.html", teacher=current_user, subjects=subjects)

# Function to get unique StudentID values from query results
def unique_student_ids(results):
    unique_ids = set()
    unique_students = []

    for student in results:
        if student.StudentID not in unique_ids:
            unique_ids.add(student.StudentID)
            unique_students.append(student)

    return unique_students

@views.route('/teacher',  methods=['GET', 'POST'])
@role_required('teacher')
def teacher_dashboard():
    # Aliasing models
    Teacher = aliased(models.Teacher)
    Student = aliased(models.Student)
    Subject = aliased(models.Subjects)
    TeacherSubject = aliased(models.TeacherSubjects)
    StudentSubject = aliased(models.StudentsSubjects)
    PredictedGrade = aliased(models.PredictedGrades)

    # Query to get all students in a teacher's class
    teacher_id = current_user.UserID  # Replace with the specific teacher's ID


    students_in_class_query = (
    db.session.query(
        Student.StudentID,
        Student.FirstName,  
        Student.LastName,
        Subject.SubjectName,
        TeacherSubject.SubjectName,
        StudentSubject.SubjectName,
        StudentSubject.SubjectID,
        PredictedGrade.StudentPredictedGrade,
        PredictedGrade.Comment
    )
    .join(StudentSubject, Student.StudentID == StudentSubject.StudentID)
    .join(Teacher, TeacherSubject.TeacherID == Teacher.TeacherID)
    .join(Subject, StudentSubject.SubjectID == Subject.SubjectID)
    .join(PredictedGrade, (Student.StudentID == PredictedGrade.StudentID) & (Subject.SubjectID == PredictedGrade.SubjectID))
    .filter(StudentSubject.SubjectName == TeacherSubject.SubjectName, Teacher.TeacherID == teacher_id)
    .all()
)



    # Get unique students based on StudentID
    students_in_class = unique_student_ids(students_in_class_query)

    # Print unique student information
    print("Unique students:")
    for student in students_in_class:
        print(f"Student ID: {student.StudentID}, Name: {student.FirstName} {student.LastName}, Subject: {student.SubjectName}, {student.SubjectID}, {student.Comment}")

    if request.method == 'POST':
        pg = request.form.get('pg')
        student_id = request.form.get('student_id')
        subject_id = student.SubjectID
        subject_name = request.form.get('subject_name')

       
        subject = Subject.query.filter_by(SubjectName=subject_name).first()
        print(f"Received - StudentID: {student_id}, SubjectID: {subject_id}")

        
        if not pg:
            flash('Select a predicted grade', category='error')
        elif (subject_name == 'Theory of Knowledge' or subject_name == 'Extended Essay') and pg not in ['A', 'B', 'C', 'D', 'E']:
            flash(f'{subject_name} can not be assigned this grade', category='error')
        else:
            predicted_grade = models.PredictedGrades.query.filter_by(
            StudentID=student_id, 
            SubjectID=subject_id).first()

            
            predicted_grade.TeacherID = teacher_id
            predicted_grade.TeacherPredictedGrade = pg    
            try:
                db.session.commit()
                flash('Predicted Grade Updated Successfully', category='success')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {e}', category='error')
            
                

    return render_template("teacher.html",  teachers=current_user, students_in_class=students_in_class)

@views.route('/student', methods=['GET', 'POST'])
@role_required('student')
def student_dashboard():
    subjects = models.Subjects.query.all()
    try:
        if request.method == 'POST':
            # subject_id = request.form.get('subject_id')
            subject_name = request.form.get('subject')
            if subject_name:
                subject_id, subject_name = subject_name.split('|')

            pg = request.form.get('pg')
            comment =  request.form.get('comment')
            # Count the number of subjects the student is currently enrolled in
            subject_count = db.session.query(models.StudentsSubjects).filter_by(StudentID=current_user.UserID).count()
            if subject_count >= 8:
                flash('You can not add more than 8 predicted grades', category='error')
            elif not pg:
                flash('Select a predicted grade', category='error')
            elif len(comment) < 4:
                flash('Enter an appropriate comment', category='error')
            elif (subject_name == 'Theory of Knowledge' or subject_name == 'Extended Essay') and pg not in ['A', 'B', 'C', 'D', 'E']:
                flash(f'{subject_name} can not be assigned this grade', category='error')
            else:
                
                predicted_grade = models.PredictedGrades(
                    StudentID=current_user.UserID, 
                    SubjectID=subject_id, 
                    StudentPredictedGrade=pg, 
                    Comment=comment
                )
                student_subject = models.StudentsSubjects(
                    StudentID=current_user.UserID, 
                    SubjectID=subject_id,
                    SubjectName = subject_name
                )
                try:
                    db.session.add(predicted_grade)
                    db.session.add(student_subject)
                    db.session.commit()
                    flash('Predicted Grade Added', category="success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Subject Already Added", category="error")


    except:
        flash('Select a Subject', category="error")
        return redirect(url_for("views.student_dashboard"))
        
     # Fetching EE and TOK grades for the logged-in student
    student_id = current_user.UserID
    ee_grade_row = db.session.query(models.PredictedGrades.TeacherPredictedGrade).filter_by(
        StudentID=student_id,
        SubjectID=29  # Subject ID for EE
    ).first()

    tok_grade_row = db.session.query(models.PredictedGrades.TeacherPredictedGrade).filter_by(
        StudentID=student_id,
        SubjectID=30  # Subject ID for TOK
    ).first()

    # Extract the grades from the query results
    ee_grade = ee_grade_row[0] if ee_grade_row else 0
    tok_grade = tok_grade_row[0] if tok_grade_row else 0

    # Fetching the total predicted grades for the logged-in student
    total_predicted_grades = db.session.query(func.sum(models.PredictedGrades.TeacherPredictedGrade)
    ).filter_by(StudentID=student_id).scalar() 
    if total_predicted_grades == None:
        total_predicted_grades = 0
    else:
        total_predicted_grades+= get_diploma_points(tok_grade, ee_grade)
    student =  models.Student.query.filter_by(StudentID=student_id).first()
    student.Total =  total_predicted_grades
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', category='error')
    return render_template("student.html", subjects=subjects, students=current_user)


@views.route('/delete_predicted_grade/<int:student_id>/<int:subject_id>/', methods=['GET', 'POST'])
@role_required('student')
def delete_predicted_grade(student_id, subject_id):
    predicted_grade = models.PredictedGrades.query.filter_by(StudentID=student_id, SubjectID=subject_id).first()
    student_subject = models.StudentsSubjects.query.filter_by(StudentID=student_id, SubjectID=subject_id).first()
    if predicted_grade and predicted_grade.StudentID == student_id:
        try:
            db.session.delete(predicted_grade)
            db.session.delete(student_subject)
            db.session.commit()
            flash('Predicted Grade deleted Successfully', category="success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", category="error")
    else:
        flash('Predicted Grade not found or you do not have permission to delete it', category="error")

    return redirect(url_for('views.student_dashboard'))


