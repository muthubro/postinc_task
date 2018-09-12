from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.models import User

from user.models import Book

# Create your views here.
class IndexView(TemplateView):
    template_name = 'main/index.html'

class BrowseView(LoginRequiredMixin, ListView):
    template_name = 'main/browse.html'
    paginate_by = 5
    model = Book

    def get_queryset(self):
        search = self.request.GET.get('search', '')

        if search:
            search_type = self.request.GET.get('type',)

            if (search_type == 'name'):
                book_list = Book.objects.filter(name__icontains=search)

            elif (search_type == 'author'):
                book_list = Book.objects.filter(author__icontains=search)

            else:
                book_list = Book.objects.filter(Q(name__icontains=search) | Q(author__icontains=search))

        else:
            book_list = Book.objects.all()

        return book_list

class BookView(LoginRequiredMixin, DetailView):
    template_name = 'main/book.html'
    model = Book

class AddToFavoritesView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        id = kwargs['pk']
        book = Book.objects.get(pk=id)

        user = request.user
        user.profile.favorites.add(book)
        user.save()

        return redirect('main:browse')

class RemoveFromFavoritesView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        id = kwargs['pk']
        book = Book.objects.get(pk=id)

        user = request.user
        user.profile.favorites.remove(book)
        user.save()

        return redirect('main:browse')
