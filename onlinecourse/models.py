import sys
from django.utils.timezone import now

try:
    from django.db import models
except Exception:
    print(
        "There was an error loading django modules. Do you have django installed?"
    )
    sys.exit()

from django.conf import settings


class Instructor(models.Model):
    """
    This class used to implement Instructor model in db

    attributes:
            user: a m-1 relation to user model
            full_time: a boolean to represent full time
            total_learners: a interger that represent total learners
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField()

    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    """
    This class used to implement Learner model in db

    attributes:
            user: a 1-1 relation to user model
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    level = models.IntegerField(
        verbose_name="Level",

    )

    def __str__(self):
        return self.user.username + "," + self.occupation


class Course(models.Model):
    """
    This class used to implement Instructor model in db

    Attributes:
        name: a string field to hold course name
        image: a image field to hold course image
        description: a string field to hold course description
        pub_date: a date field to hold course public date
        instructors: a m-m relation to Instructor object
        users: a m-m relation to User object
        total_enrollment: a integer field to hold course total enrollment
        is_enrolled: a boolian to represent if course is enrolled or not

    Methods:
        get_all_questions: returns list of all course questions
    """

    name = models.CharField(null=False, max_length=30, default="online course")
    image = models.ImageField(upload_to="course_images/")
    description = models.CharField(max_length=1000)
    pub_date = models.DateField(null=True)
    instructors = models.ManyToManyField(Instructor)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Enrollment"
    )
    total_enrollment = models.IntegerField(default=0)
    is_enrolled = False

    def get_all_questions(self):
        """
        Returns list of all Course questions
        """

        return Question.objects.filter(lesson__course=self)

    def __str__(self):
        return "Name: " + self.name + "," + "Description: " + self.description


# Lesson model
class Lesson(models.Model):
    """
    This class used to implement Lesson table in db

    attributes:
        title: a string to represent lesson title
        order: a Number to represent lesson order in template
        course: a 1-m relation to Course model
        content: a string to hold lesson content
    """

    title = models.CharField(max_length=200, default="title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """
    This class used to implement Enrollment table in db
    Once a user enrolled a class, an enrollment entry should be created between the user and course
    And we could use the enrollment to track information such as exam submissions

    attributes:
        user: a 1-m relation to User model
        course: a 1-m relation to Course model
        date_enrolled: a date field to hold joining date (default now)
        mode: a string field with choices to hold type of course (default Audit)
        rating: a decimal field to hold rate of enrollment (default 5.0)

    """

    AUDIT = "audit"
    HONOR = "honor"
    BETA = "BETA"
    COURSE_MODES = [(AUDIT, "Audit"), (HONOR, "Honor"), (BETA, "BETA")]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=5, choices=COURSE_MODES, default=AUDIT)
    rating = models.FloatField(default=5.0)


class Question(models.Model):
    """
    This class used to implement Question table in db

    attributes:
        lesson: a 1-m relation to Lesson model
        question_text: a string filed to hold question text
        grade: a positive number to hold grade of question

    methods:
        is_multi_choice: define if a question has multi choice or not
        is_get_score: define if a question get score or not
    """

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.CharField(max_length=250)
    grade = models.PositiveIntegerField()

    def is_multi_choice(self):
        """
        Define if a question has multi choice or not
        counts the number of correct answers of a question and compares to 1

        Returns:
            a boolean that is True or False
        """

        return self.choices.filter(is_correct=True).count() > 1

    def is_get_score(self, selected_ids):
        """
        Define if a question gets whole scores or not
        compares count of all answers to count of provided correct answer ids
        and returns a boolean that is True or False

        Args:
            selected_ids: a queryset object that represent selected ansewer ids

        Returns:
            a boolean that is True or False
        """

        all_answers = self.choices.filter(is_correct=True).count()
        selected_correct = self.choices.filter(
            is_correct=True, id__in=selected_ids
        ).count()
        if all_answers == selected_correct:
            return True
        else:
            return False

    def __str__(self):
        return f"{self.id} - {self.question_text[:25]}"


class Choice(models.Model):
    """
    This class used to implement Choice table in db

    attributes:
        question: a m-1 relation to Question object
        is_correct: a boolean field that define if choice is true or false
        choice_text: a string field to hold choice text
    """

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    is_correct = models.BooleanField()
    choice_text = models.CharField(max_length=250)


class Submission(models.Model):
    """
    This class used to implement Submission table in db

    attributes:
        enrollment: a m-1 relation to Enrollment object
        choices: a m-m relation to choices object
    """

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice)
