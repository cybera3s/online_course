from django.db.models import Sum
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(
            request, "onlinecourse/user_registration_bootstrap.html", context
        )
    elif request.method == "POST":
        # Check if user exists
        username = request.POST["username"]
        password = request.POST["psw"]
        first_name = request.POST["firstname"]
        last_name = request.POST["lastname"]
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "User already exists."
            return render(
                request,
                "onlinecourse/user_registration_bootstrap.html",
                context,
            )


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["psw"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "Invalid username or password."
            return render(
                request, "onlinecourse/user_login_bootstrap.html", context
            )
    else:
        return render(
            request, "onlinecourse/user_login_bootstrap.html", context
        )


def logout_request(request):
    logout(request)
    return redirect("onlinecourse:index")


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(
            user=user, course=course
        ).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by("-total_enrollment")[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    """
    A Django class-based view for displaying a single instance of the Course model.

    This view inherits from Django's generic `DetailView` class and is used to display
    detailed information about a specific course. It retrieves the Course instance based
    on the primary key (pk) passed in the URL and renders a template with the course data.

    Attributes:
        model (django.db.models.Model): The model class that this view is based on.
        template_name (str): The name of the template that will be used to render the view.
    """

    model = Course
    template_name = "onlinecourse/course_detail_bootstrap.html"


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode="honor")
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(
        reverse(viewname="onlinecourse:course_details", args=(course.id,))
    )


def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    answers = extract_answers(request)
    submission.choices.add(*answers)
    submission.save()

    return redirect(
        reverse(
            viewname="onlinecourse:exam_result",
            args=(course.id, submission.id),
        )
    )


def extract_answers(request) -> list:
    """
    collects the selected choices from the exam form from the request object
    :param request: request object
    :return: a list contains choices ids
    """
    submitted_answers = []
    for key in request.POST:
        if key.startswith("choice"):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    selected_choices = submission.choices.all()
    selected_ids = selected_choices.values_list("id", flat=True)
    all_questions = course.get_all_questions()

    total_score = 0
    for q in all_questions:
        if q.is_get_score(selected_choices.filter(question=q)):
            total_score += q.grade

    total_grade = all_questions.aggregate(sum_grade=Sum("grade"))
    percent_score = total_score * 100 // total_grade["sum_grade"]

    data = {
        "course": course,
        "grade": percent_score,
        "selected_ids": selected_ids,
    }
    return render(request, "onlinecourse/exam_result_bootstrap.html", data)
