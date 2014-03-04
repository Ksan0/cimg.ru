from django.forms import *
from django.utils.encoding import smart_str


class EncryptForm(forms.Form):
    imgChooseInput = FileField(widget=ClearableFileInput({"class": "files-loader-into-msg", "accept": "image/*"}))
    imgDifferenceSelect = ChoiceField(widget=Select({"class": "select-difference"}), choices=[("2", "small"), ("4", "medium"), ("6", "high"), ("8", "very high")])
    textField = CharField(max_length=16384, widget=Textarea({"class": "part-center", "rows": "12", "placeholder": "Enter text"}))
    filesChooseInput = FileField(widget=ClearableFileInput({"class": "files-loader-into-msg", "multiple": ""}))
    enterPasswordInput = CharField(widget=PasswordInput({"class": "part-left", "placeholder": "Enter password"}))
    confirmPasswordInput = CharField(widget=PasswordInput({"class": "part-left", "placeholder": "Confirm password"}))

    def is_valid(self):
	return smart_str(self.data['enterPasswordInput']) == smart_str(self.data['confirmPasswordInput'])
      

class DecryptForm(forms.Form):
    imgChooseInput = FileField(widget=ClearableFileInput({"class": "files-loader-into-msg", "accept": "image/*"}))
    enterPasswordInput = CharField(widget=PasswordInput({"class": "part-left", "placeholder": "Enter password"}))