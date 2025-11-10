from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """Book Review Form"""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Review Title'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review...'}),
        }
