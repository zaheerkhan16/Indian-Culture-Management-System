from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from validate_email import validate_email
from .models import Profile
from .forms import LoginForm, SignUpForm
from django.core.mail import EmailMessage
from django.conf import settings
from .decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from .utils import generate_token
import threading
from django.contrib.auth import get_user_model
import django.utils.encoding

User = get_user_model()


# Create your views here.
class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_activation_email(user, request):
    current_site = get_current_site(request)
    email_subject = 'Activate your account'
    email_body = render_to_string('Activation.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body,
                         from_email=settings.EMAIL_FROM_USER,
                         to=[user.email]
                         )

    if not settings.TESTING:
        EmailThread(email).start()


@auth_user_should_not_access
def Login(request):
    form = SignUpForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user and not user.is_email_verified:
            messages.error(request, '')
            return render(request, 'Dashboard.html')

        if not user:
            messages.error(request, '⚠️ Invalid credentials, try again')
            return render(request, 'Login.html')

        login(request, user)

        return redirect(reverse('Dashboard'))

    return render(request, 'Login.html', {'form': form})


@auth_user_should_not_access
def Register(request):
    form = SignUpForm()

    if request.method == "POST":
        context = {'has_error': False}
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if len(password1) < 6:
            messages.error(request, '⚠️ Password should be at least 6 characters for greater security')
            return redirect('Register')

        if password1 != password2:
            messages.error(request, '⚠️ Password Mismatch! Your Passwords Do Not Match')
            return redirect('Register')

        if not validate_email(email):
            messages.error(request, '⚠️ Password Mismatch! Your Passwords Do Not Match')
            return redirect('Register')

        if not username:
            messages.error(request, '⚠️ Username is required!')
            return redirect('Register')

        if User.objects.filter(username=username).exists():
            messages.error(request, '⚠️ Username is taken! Choose another one')

            return render(request, 'Register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, '⚠️ Email is taken! Choose another one')

            return render(request, 'Register.html')

        user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email)
        user.set_password(password1)
        user.save()

        if not context['has_error']:
            send_activation_email(user, request)

            messages.success(request, '✅ Sign Up Successful!')
            return redirect('Register')

    return render(request, 'Register.html', {'form': form})


def Logout(request):
    logout(request)
    messages.success(request, '✅ Successfully Logged Out!')

    return redirect(reverse('Login'))


def ActivateUser(request, uidb64, token):
    try:
        uid = django.force_text(urlsafe_base64_decode(uidb64))

        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_email_verified = True
        user.save()

        messages.success(request, '✅ Email Verified! You can now Log in')
        return redirect(reverse('Login'))

    return render(request, 'Activation Failed.html', {"user": user})


def Dashboard(request):
    return render(request, 'Dashboard.html')


def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    return render(request, "contact.html")


def festivals(request):
    return render(request, "festivals.html")


def classical(request):
    return render(request, "classical.html")
def capitals(request):
    return render(request, "capitals.html")
def blogs(request):
    return render(request, "blog.html")
def maps(request):
    return render(request, "map.html")
def sci(request):
    return render(request, "science.html")



