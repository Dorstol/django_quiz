from django import forms

from .models import QuizResult


class QuizResultForm(forms.ModelForm):
    class Meta:
        model = QuizResult
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ваш email'}),
        }
        labels = {
            'name': 'Имя',
            'email': 'Email',
        }

    def validate_unique(self):
        """
        Переопределяем метод validate_unique, чтобы исключить проверку уникальности поля email.
        """
        exclude = self._get_validation_exclusions()
        exclude.add('email')
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)
