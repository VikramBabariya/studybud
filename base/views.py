from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from .models import Room, Topic, Message, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.contrib import messages


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, "User does not exist.")

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)  # it automatically creates session in db for user.
            return redirect('home')
        else:
            messages.error(request, 'Username or Password does not match')

    context = {}
    return render(request, 'base/login-register.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


def register_page(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        # implement: Unique username
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Enter valid data.')

    context = {'form': form, 'page': 'register'}
    return render(request, 'base/login-register.html', context)


def home(request):
    q = request.GET.get('q') if None != request.GET.get('q') else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()[:5]
    room_count = rooms.count()
    room_messages = Message.objects.all().filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
               'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    rm = Room.objects.get(id=pk)
    room_messages = rm.message_set.all()  # getting all child of room
    participants = rm.participants.all()  # don't nees child_set here because of mana-to-many relation

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=rm,
            body=request.POST.get('body')
        )
        rm.participants.add(request.user)
        return redirect('room', pk=pk)

    context = {'room': rm, 'room_messages': room_messages, 'participants':participants}
    return render(request, 'base/room.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='/login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room-form.html', context)


@login_required(login_url='/login')
def update_room(request, pk):
    rm = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    form = RoomForm(instance=rm)

    if request.user != rm.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        rm.name = request.POST.get('name')
        rm.topic = topic
        rm.description = request.POST.get('description')
        rm.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': rm}
    return render(request, 'base/room-form.html', context)


@login_required(login_url='/login')
def delete_room(request, pk):
    rm = Room.objects.get(id=pk)

    if request.user != rm.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        rm.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': rm})


@login_required(login_url='/login')
def delete_message(request, pk):
    mes = Message.objects.get(id=pk)

    if request.user != mes.user:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        mes.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': mes})


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/update-user.html', context)


def topics_page(request):
    q = request.GET.get('q') if None != request.GET.get('q') else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)
