from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.shortcuts import render, redirect
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .forms import RenewBookForm
from .models import Book, Author, BookInstance
from django.views import generic
from django.contrib.auth.decorators import login_required, permission_required


# from django.shortcuts import get_object_or_404


def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    context_object_name = 'book_list'
    queryset = Book.objects.filter(title__icontains='war')[:5]
    template_name = 'books/my_arbitrary_template_name_list.html'

    def get_queryset(self):
        return Book.objects.filter(title__icontains='war')[:5]


class BookDetailView(generic.DetailView):
    model = Book
    paginate_by = 10

    def book_detail_view(request, primary_key):
        try:
            book = Book.objects.get(pk=primary_key)
        except Book.DoesNotExist:
            raise Http404('Book does not exist')

        return render(request, 'catalog/book_detail1.html', context={'book': book})


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorListView(generic.ListView):
    model = Author
    context_object_name = 'author_list'
    # queryset = Author.objects.filter(id(1))[:5]
    template_name = 'books/my_arbitrary_template_name_list.html'

    # def get_queryset(self):
    #     return Book.objects.filter(author__first_name='nifemi')[:5]


class AuthorDetailView(generic.DetailView):
    model = Author
    paginate_by = 10

    def author_detail_view(request, primary_key):
        try:
            author = Author.objects.get(pk=primary_key)
        except Author.DoesNotExist:
            raise Http404('Author does not exist')

        return render(request, 'catalog/author_detail.html', context={'author': author})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'registeration/login.html', {'form': form})


class RenewBookModelForm(ModelForm):
    def clean_due_back(self):
        data = self.cleaned_data['due_back']
        if data < datetime.date.today():
            raise ValidationError('Invalid date - renewal in past')
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError('Invalid date - renewal more than 4 weeks ahead')
        return data

    class Meta:
        model = BookInstance
        fields = ['due_back']
        labels = {'due_back': 'New renewal date'}
        help_texts = {'due_back': 'Enter a date between now and 4 weeks (default 3).'}


class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}


class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__'


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
