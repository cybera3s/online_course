from django.db.models import Sum
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Submission
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

User = get_user_model()
# Get an instance of a logger
logger = logging.getLogger(__name__)


def registration_request(request):
    """
    Handle GET and POST requests for user registration.

    Args:
        request: HttpRequest object containing metadata about the request.

    Returns:
        If the request is a GET request, renders a registration form page.
        If the request is a POST request, attempts to create a new user account
        using the form data. If the username is not already taken, logs the user
        in and redirects them to the course index page. If the username is taken,
        displays an error message on the registration form page and allows the user
        to try again.

    Raises:
        None.
    """

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
    """
    Handle POST requests for user login.

    Args:
        request: HttpRequest object containing metadata about the request.

    Returns:
        If the user credentials are valid, logs the user in and redirects them
        to the course index page. If the user credentials are invalid, displays
        an error message on the login page and allows the user to try again.

    Raises:
        None.
    """

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
    """
    Handle requests for user logout.

    Args:
        request: HttpRequest object containing metadata about the request.

    Returns:
        Logs the user out and redirects them to the course index page.

    Raises:
        None.
    """

    logout(request)
    return redirect("onlinecourse:index")


def check_if_enrolled(user: User, course: Course) -> bool:
    """
    Check if a user is enrolled in a course.

    Args:
        user: User object representing the user to check.
        course: Course object representing the course to check.

    Returns:
        True if the user is enrolled in the course, False otherwise.

    Raises:
        None.
    """

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
    """
    View class for displaying a list of courses.

    Attributes:
        template_name (str): Name of the template to render for this view.
        context_object_name (str): Name of the context variable containing the course list.

    Methods:
        get_queryset(): Return the list of courses to display.
    """

    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        """
        returns custom list of courses and check authenticated user enrollment in them
        """

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
    """
    Enroll a user in a course if user is not already enrolled and authenticated

    Args:
        request: HttpRequest object containing metadata about the request.
        course_id: Course id for enrollment.

    Returns:
        HttpResponseRedirect: redirects to course detail page

    Raises:
        None.
    """

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
    """
    Submit a user exam and redirects to exam results page

    Args:
        request: HttpRequest object containing metadata about the request.
        course_id: Course id for submission.

    Returns:
        HttpResponseRedirect: redirects to exam result page

    Raises:
        None.
    """

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
    Collects the selected choices from the exam form
    from the request object

    Args:
        request: HttpRequest object containing metadata about the request.

    Returns:
        list: a list contains choices ids

    Raises:
        None.
    """

    submitted_answers = []

    for key in request.POST:
        if key.startswith("choice"):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers


def show_exam_result(request, course_id, submission_id):
    """
    Show exam results
    calculates total score percentage,
    selected ids of choices and get course object
    and add them as context to request

    Args:
        request: HttpRequest object containing metadata about the request.
        course_id: Course id for get corrsponding exam course.
        submission_id: submission id for getting submission object
    Returns:
        HttpResponse: renders exam result page

    Raises:
        None.
    """

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
