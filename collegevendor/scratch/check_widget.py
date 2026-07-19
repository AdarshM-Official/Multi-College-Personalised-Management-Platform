import os
import sys
import django

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collegevendor.settings')
django.setup()

from management.forms import StudentForm, TeacherForm

s_form = StudentForm()
print("STUDENT PASSWORD WIDGET:")
print(s_form['password'].as_widget())

t_form = TeacherForm()
print("\nTEACHER PASSWORD WIDGET:")
print(t_form['password'].as_widget())
