from flask import Blueprint, render_template, request, url_for, flash, redirect
from .models import Users, Teacher, Admin, Student
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login',  methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Users.query.filter_by(Email=email).first()
        if user:
            if check_password_hash(user.Password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                if user.Role == 'admin':
                    return redirect(url_for('views.admin_dashboard'))
                elif user.Role == 'teacher':
                    return redirect(url_for('views.teacher_dashboard'))
                elif user.Role == 'student':
                    return redirect(url_for('views.student_dashboard'))
                
                

            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html")
    
@auth.route('/logout')
@login_required
def logout():
    return redirect(url_for('auth.login'))

@auth.route('/signup',  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form.get('firstName')
        lastname = request.form.get('lastName')
        role = request.form.get('role')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        grade = request.form.get('grade')
        
    


        existing_user = Users.query.filter_by(Email=email).first()
        if existing_user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstname) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(lastname) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif not role:
            flash('All fields are required', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        
        else:
            password_hash = generate_password_hash(password1, method='sha256')
            if role == 'admin':
                admin_count = db.session.query(Admin).count()
                if admin_count >= 1:
                     flash('There can be only one Administrator', category='error')
                     return redirect(url_for('auth.signup'))
                else:
                    new_user = Admin(FirstName=firstname, LastName=lastname, Email=email, Password=password_hash, Role='admin')
            elif role == 'teacher':
                new_user = Teacher(FirstName=firstname, LastName=lastname, Email=email, Password=password_hash, Role='teacher')
            elif role == 'student':
        
                if grade is not None:
                    try:
                        grade = int(grade)
                    except ValueError:
                        print("Invalid input. Please enter a valid integer.")
                else:
                    print("Grade is required.")
                if int(grade) != 12:
                    flash('You must be in grade 12 to use the system', category='error')
                else:    
                    new_user = Student(FirstName=firstname, LastName=lastname, Email=email, Password=password_hash, Role='student', Grade=grade)
            else:
                flash('Invalid role', category='error')
                return redirect(url_for('signup'))
            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
            except Exception as e:
                db.session.rollback()   
                print(f"An error occurred: {e}")
            finally:
                db.session.close()

            flash('Account Created', category='success')

            if role == 'admin':
                return redirect(url_for('views.admin_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('views.teacher_dashboard'))
            elif role == 'student':
                return redirect(url_for('views.student_dashboard'))
            else:
                pass

    return render_template("signup.html")
    