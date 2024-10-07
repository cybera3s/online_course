from django.contrib import admin

# local imports
from .models import Course, Lesson, Instructor, Learner, Question, Choice


class QuestionInline(admin.StackedInline):
    """
    A Django admin inline class for the Question model.

    This inline class is used to display a set of
    question fields within the admin interface
    of another model. It allows the user to edit
    multiple instances of the Question model
    at once, and includes a form for creating new
    Question instances.

    Attributes:
        model (django.db.models.Model): The model
        class that this inline is based on.
        extra (int): The number of extra forms that
        should be displayed in the admin interface.
    """

    model = Question
    extra = 5


class ChoiceInline(admin.StackedInline):
    """
    A Django admin inline class for the Choice model.

    This inline class is used to display a set of
    choice fields within the admin interface
    of another model. It allows the user to edit
    multiple instances of the Choice model
    at once, and includes a form for creating new
    Choice instances.
    """

    model = Choice
    extra = 4


class LessonInline(admin.StackedInline):
    """
    A Django admin inline class for the Lesson model.

    This inline class is used to display a set of
    lesson fields within the admin interface
    of another model. It allows the user to edit
    multiple instances of the Lesson model
    at once, and includes a form for creating new
    Lesson instances.

    Attributes:
        model (django.db.models.Model): The model
        class that this inline is based on.
        extra (int): The number of extra forms that
         should be displayed in the admin interface.
    """

    model = Lesson
    extra = 5


class CourseAdmin(admin.ModelAdmin):
    """
    Admin interface for the Course model.

    This class defines how the Course model s
    hould be displayed and edited
    in the Django admin panel. It includes a
    list of fields to display, filters,
    search fields, and an inline for related Lesson objects.

    Attributes:
        inlines (list): A list of inline
        classes to include in the edit view.
        list_display (tuple): A tuple of
        field names to display in the list view.
        list_filter (list): A list of
        field names to filter by in the list view.
        search_fields (list): A list of
        field names to search by in the list view.

    """

    inlines = [LessonInline]
    list_display = ("name", "pub_date")
    list_filter = ["pub_date"]
    search_fields = ["name", "description"]


class LessonAdmin(admin.ModelAdmin):
    """
    Admin interface for the Lesson model.

    This class defines how the Lesson model should be displayed and edited
    in the Django admin panel. It includes a list of fields to display and
    an inline for related Question objects.

    Attributes:
        list_display (list): A list of field names to display in the list view.
        inlines (list): A list of inline classes to include in the edit view.
    """

    list_display = ["title", "course"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for the Question model.

    This class defines how the Question model
    should be displayed and edited
    in the Django admin panel. It includes a
    list of fields to display, filters,
    search fields, and an inline for related Choice objects.

    Attributes:
        list_display (tuple): A tuple of field
        names to display in the list view.
        list_filter (tuple): A tuple of field
        names to filter by in the list view.
        search_fields (tuple): A tuple of field
        names to search by in the list view.
        inlines (list): A list of inline classes
        to include in the edit view.

    Methods:
        lesson_title: A method to display the
        title of the related Lesson object
            in the list view.
        question_text: A method to display a
        truncated version of the question text
            in the list view.
    """

    list_display = ("question_text", "lesson_title", "grade")
    list_filter = ("lesson", "grade")
    search_fields = ("question_text", "lesson")
    inlines = [ChoiceInline]

    def lesson_title(self, obj):
        """
        Display a title of related Lesson object.

        This method displays a summary of the related Lesson object
        for a given Question object.

        Args:
            obj: The Question object to display the related Lesson title for.

        Returns:
            A string containing the related Lesson title.
        """

        return obj.lesson.title

    def question_text(self, obj):
        """
        Display truncated question text

        Args:
            obj: The Question object

        Returns:
            A string cataining truncated question text
        """

        return obj.choice_text[:60]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """
    Admin interface for the Choice model.

    This class defines how the Choice model should be displayed and edited
    in the Django admin panel. It i
    ncludes a list of fields to display and filters.

    Attributes:
        list_display (tuple): A tuple of
        field names to display in the list view.
        list_filter (tuple): A tuple of field
        names to filter by in the list view.
        inlines (tuple): A tuple of inline
        classes to include in the edit view.

    Methods:
        text: A method to display truncated
        Choice text in the list view
    """

    list_display = ("question", "text")
    list_filter = ("is_correct",)
    search_fields = ("choice_text",)

    def text(self, obj):
        """
        Display truncated Choice text

        Args:
            obj: The Choice object

        Returns:
            A string cataining truncated choice text

        """
        return obj.choice_text[:50]


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
