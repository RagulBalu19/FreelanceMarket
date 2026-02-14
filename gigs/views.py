# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Gig
# from .forms import GigForm
# from django.contrib.auth.decorators import login_required

# def gig_list(request):
#     gigs = Gig.objects.all()
#     return render(request, 'gigs/list.html', {'gigs': gigs})


# def gig_detail(request, pk):
#     gig = get_object_or_404(Gig, pk=pk)
#     return render(request, 'gigs/detail.html', {'gig': gig})

# def home(request):
#     return render(request, 'gigs/home.html')

# @login_required
# def create_gig(request):
#     if request.user.role != 'seller':
#         return redirect('/')

#     form = GigForm(request.POST, request.FILES)
#     if form.is_valid():
#         gig = form.save(commit=False)
#         gig.seller = request.user
#         gig.save()

#         return redirect('/')

#     return render(request, 'gigs/create.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Gig
from .forms import GigForm
from accounts.models import Notification

def home(request):
    gigs = Gig.objects.all()

    unread_count = 0
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, 'gigs/home.html', {
        'gigs': gigs,
        'unread_count': unread_count
    })

def gig_list(request):
    gigs = Gig.objects.filter(is_active=True)
    return render(request, 'gigs/list.html', {'gigs': gigs})


def gig_detail(request, slug):
    gig = get_object_or_404(Gig, slug=slug, is_active=True)
    return render(request, 'gigs/detail.html', {'gig': gig})



@login_required
def create_gig(request):

    if request.user.role != 'seller':
        return redirect('home')

    if request.method == 'POST':
        form = GigForm(request.POST, request.FILES)

        if form.is_valid():
            gig = form.save(commit=False)
            gig.seller = request.user
            gig.save()
            return redirect('gig_detail', slug=gig.slug)
    else:
        form = GigForm()

    return render(request, 'gigs/create.html', {'form': form})
