# keyword_app/forms.py
from django import forms

class KeywordForm(forms.Form):
    file = forms.FileField(label="Chọn file từ khóa (Excel)")
    output_filename = forms.CharField(label="Tên file kết quả", max_length=100)
