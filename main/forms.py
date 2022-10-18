from django.forms import Form, CharField, TextInput


class Room_Name(Form):
    room_name = CharField(max_length=4, required=False, widget=TextInput(attrs={
        'class': 'login_input',
        'id': 'roomcode',
        'autocapitalize': 'none',
        'autocorrect': 'off',
        'autocomplete': 'off',
        'placeholder': '4-ЗНАЧНЫЙ КОД',
    }))
