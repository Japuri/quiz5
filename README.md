# Quiz5 - Django Exam Management System

A comprehensive web-based examination system built with Django 5.2, designed for educational institutions to create, manage, and conduct online exams with role-based access control.

## 🚀 Quick Start Guide

### 📋 Prerequisites
- Python 3.10.0rc2 was used during development
- Git
- Virtual environment support

### 📥 Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/zanra22/Quiz5.git
cd Quiz5
```

#### 2. Create Virtual Environment

**Windows:**
```bash
# Create virtual environment
python -m venv quiz5_env

# Activate virtual environment
quiz5_env\Scripts\activate
```

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv quiz5_env

# Activate virtual environment
source quiz5_env/bin/activate
```

#### 3. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

#### 4. Database Setup
```bash
# Create migrations for each app (in order)
python manage.py makemigrations accounts
python manage.py makemigrations authentication  
python manage.py makemigrations exam

# Apply all migrations to database
python manage.py migrate
```

#### 5. Collect Static Files (for production)
```bash
# Collect all static files to STATIC_ROOT directory
python manage.py collectstatic --noinput
```

#### 7. Create Sample Users

**Create Teacher Account:**
```bash
python manage.py create_teacher
```
You'll be prompted to enter:
- Email address
- First name
- Last name  
- Password

**Create Student Account:**
```bash
python manage.py create_student
```
You'll be prompted to enter:
- Email address
- First name
- Last name
- Password

#### 8. Run the Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to access the application.

#### 9. Login
- Use the credentials you created with the management commands
- Teachers can access exam creation and management features
- Students can view and take available exams

## 📚 Project Overview

### 🎯 Purpose
Quiz5 is designed to streamline the examination process in educational institutions by providing:
- **Secure exam creation and management**
- **Role-based access control** (Teachers vs Students)
- **Comprehensive analytics and reporting**
- **Flexible exam configurations**
- **Real-time exam monitoring**

### 👥 User Roles

#### 🍎 **Teachers**
- Create and manage exams
- Design multiple-choice questions with up to 4 options
- Set exam parameters (timing, attempts, passing scores)
- Control student access (all students or specific students)
- View comprehensive analytics and reports
- Monitor student performance and progress

#### 📚 **Students**  
- View available exams based on teacher permissions
- Take exams within specified time windows
- Track personal exam history and statistics
- View results and performance analytics
- Limited attempts based on teacher settings

### 🛠️ Core Features

#### 📝 **Exam Management**
- **Flexible Exam Creation**: Teachers can create exams with custom titles, descriptions, and instructions
- **Question Management**: Add, edit, and organize multiple-choice questions
- **Answer Key System**: Automatic grading based on predefined correct answers
- **Time Controls**: Set start/end dates and exam duration limits
- **Attempt Limiting**: Configure maximum attempts per student
- **Passing Thresholds**: Set minimum passing percentages

#### 🔐 **Access Control**
- **Role-Based Security**: Separate interfaces and permissions for teachers and students
- **Flexible Student Access**: Grant access to all students or select specific students
- **Time-Window Restrictions**: Exams only accessible during specified periods
- **Attempt Validation**: Enforce maximum attempt limits per student

#### 📊 **Analytics & Reporting**

**Teacher Analytics:**
- Overall teaching statistics (total exams, submissions, average scores)
- Individual exam performance metrics
- Pass/fail rates and score distributions
- Question difficulty analysis (success rates per question)
- Time efficiency metrics (average completion time vs allocated time)
- Student performance tracking

**Student Analytics:**
- Personal exam history and progress tracking
- Pass/fail statistics and trends
- Grade distribution analysis
- Performance comparisons and improvement tracking

#### ⏰ **Real-Time Features**
- **Live Exam Status**: Dynamic status updates (upcoming, active, expired)
- **Timer Management**: Automatic exam submission when time expires
- **Instant Results**: Immediate score calculation and feedback
- **Progress Tracking**: Real-time monitoring of student submissions

### 🏗️ **Technical Architecture**

#### **Backend Framework**
- **Django 5.2**: Modern Python web framework
- **SQLite Database**: Lightweight database for development
- **Custom User Model**: Email-based authentication system
- **Model Relationships**: Optimized database design for exam data

#### **Frontend Technologies**
- **Bootstrap 5**: Responsive UI framework
- **Custom CSS**: Tailored styling for educational interfaces
- **JavaScript**: Interactive exam taking and form validation
- **Font Awesome**: Professional icon library

#### **Security Features**
- **CSRF Protection**: Built-in Django security
- **Authentication**: Secure login/logout system
- **Authorization**: Role-based access control
- **Input Validation**: Form and data validation
- **Session Management**: Secure user session handling

### 📱 **User Interface**

#### **Teacher Dashboard**
- Quick statistics overview (total exams, active exams, submissions)
- Recent exam submissions with status indicators
- Easy access to exam creation and management tools
- Comprehensive analytics views

#### **Student Dashboard**  
- Available exams with clear status indicators
- Personal statistics and progress tracking
- Exam history with results and performance data
- Intuitive exam taking interface

#### **Exam Taking Interface**
- Clean, distraction-free exam environment
- Question navigation and progress indicators
- Automatic saving and submission
- Time remaining display and warnings

### 🔧 **Configuration Options**

#### **Exam Settings**
- **Duration**: Set exam time limits (minutes)
- **Attempts**: Configure maximum attempts per student (1-10)
- **Passing Score**: Set minimum passing percentage (1-100%)
- **Access Type**: Choose between "All Students" or "Specific Students"
- **Time Windows**: Define when exams are available for taking

#### **Question Types**
- **Multiple Choice**: 2-4 answer options per question
- **Flexible Scoring**: Customizable point values per question
- **Random Order**: Option to randomize question presentation
- **Answer Shuffling**: Randomize answer option order

### 📈 **Performance Metrics**

The system tracks comprehensive metrics including:
- **Student Performance**: Individual and aggregate scoring
- **Question Analytics**: Success rates and difficulty analysis  
- **Time Management**: Completion times and efficiency metrics
- **Access Patterns**: Login frequency and exam participation
- **System Usage**: Teacher activity and exam creation trends

### 🌐 **Deployment Ready**

Quiz5 is designed with deployment in mind:
- **Environment Configuration**: Easy settings management
- **Static File Handling**: Optimized for production deployment
- **Database Migration**: Smooth database updates and changes
- **Scalable Architecture**: Ready for institutional-scale usage

### 📋 **Getting Started Checklist**

1. ✅ Clone repository and setup virtual environment
2. ✅ Install dependencies and run migrations  
3. ✅ Create teacher and student accounts using management commands
4. ✅ Login as teacher and create your first exam
5. ✅ Add questions and configure exam settings
6. ✅ Login as student and take the exam
7. ✅ Review analytics and results in teacher dashboard

### 🤝 **Contributing**

This project is designed for educational purposes and programming assignments. Students working with this codebase should focus on:
- Understanding Django's MVC architecture
- Learning authentication and authorization patterns
- Exploring database relationships and querying
- Practicing form handling and validation
- Implementing user interface improvements

---

**Ready to get started? Follow the installation guide above and begin exploring the Quiz5 examination system!** 🎓
# quiz5
