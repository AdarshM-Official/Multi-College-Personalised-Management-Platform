from django.urls import path
from . import views

urlpatterns = [
    path('teachers/import/', views.import_teachers_excel, name='import_teachers_excel'),
    path('teachers/template/', views.download_teacher_template, name='download_teacher_template'),
    path('settings/', views.college_settings, name='college_settings'),
    path('gallery/delete/<int:image_id>/', views.delete_gallery_image, name='delete_gallery_image'),
    path('leaders/delete/<int:leader_id>/', views.delete_college_leader, name='delete_college_leader'),
    
    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/view/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    
    # Student Dashboard
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/timetable/', views.student_timetable, name='student_timetable'),
    
    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/view/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
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
    
    # Internal Marks
    path('internal-marks/', views.internal_marks_list, name='internal_marks_list'),
    
    # Utilities
    path('setup-data/', views.generate_sample_data, name='generate_sample_data'),
    
    # HOD
    path('hods/', views.hod_list, name='hod_list'),
    path('hods/add/', views.add_hod, name='add_hod'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('timetable/create/', views.create_timetable, name='create_timetable'),
    path('timetable/view/<int:tt_id>/', views.view_timetable, name='view_timetable'),
    path('timetable/edit/<int:tt_id>/', views.edit_timetable, name='edit_timetable'),
    path('timetable/delete/<int:tt_id>/', views.delete_timetable, name='delete_timetable'),
    path('exam-notification/create/', views.create_exam_notification, name='create_exam_notification'),
    path('department/config/', views.department_configuration, name='department_configuration'),
    path('department/config/class/delete/<int:class_id>/', views.delete_academic_class, name='delete_academic_class'),
    path('department/config/subject/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('department/config/category/delete/<int:category_id>/', views.delete_internal_mark_category, name='delete_internal_mark_category'),
    
    # Submissions
    path('assignments/<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('assignments/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
]
