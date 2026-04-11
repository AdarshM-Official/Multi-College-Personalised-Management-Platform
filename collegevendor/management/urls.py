from django.urls import path
from . import views

# URL patterns for management app - Triggered Reload
urlpatterns = [
    path('teachers/import/', views.import_teachers_excel, name='import_teachers_excel'),
    path('teachers/template/', views.download_teacher_template, name='download_teacher_template'),
    path('settings/', views.college_settings, name='college_settings'),
    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    
    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/view/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/edit/<int:dept_id>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
    path('departments/import/', views.import_departments_excel, name='import_departments_excel'),
    path('departments/template/', views.download_department_template, name='download_department_template'),
    
    # Specializations
    path('specializations/add/', views.add_specialization, name='add_specialization'),
    path('specializations/edit/<int:spec_id>/', views.edit_specialization, name='edit_specialization'),
    path('specializations/delete/<int:spec_id>/', views.delete_specialization, name='delete_specialization'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),
    
    # Attendance
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    
    # Utilities
    path('setup-data/', views.generate_sample_data, name='generate_sample_data'),
]
