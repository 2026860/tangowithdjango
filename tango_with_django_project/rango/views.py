from django.shortcuts import render
from django.http.response import HttpResponse

#Models Imports
from rango.models import Page
from rango.models import Category

from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm

from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from datetime import datetime
from rango.bing_search import run_query

from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User

from django.template import RequestContext

# Create your views here.
def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list}

    # old
    # visits = int(request.COOKIES.get('visits', '1'))
    visits = request.session.get('visits')
    
    # reset_last_visit_time = False
    # response = render(request, 'rango/index.html', context_dict)
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visits')
    if last_visit:
        # last_visit = request.COOKIES['last_visit']
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        # If it's been more than a day since the last visit...
        if (datetime.now() - last_visit_time).seconds > 0:
            visits = visits + 1
            # ...and flag that the cookie last visit needs to be updated
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so flag that it should be set.
        reset_last_visit_time = True

        # context_dict['visits'] = visits

        #Obtain our Response object early so we can add cookie information.
        # response = render(request, 'rango/index.html', context_dict)

    if reset_last_visit_time:
        # response.set_cookie('last_visit', datetime.now())
        # response.set_cookie('visits', visits)
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits
    # Return response back to the user, updating any cookies that need changed.
    response = render(request, 'rango/index.html', context_dict)

    return response
    #  OLD!!!
    # request.session.set_test_cookie()   
    # category_list = Category.objects.order_by('-views')[:5]
    # context_dict = {'categories': category_list}
    # return render(request, 'rango/index.html', context_dict)
def about(request):
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0 
    return render(request, 'rango/about.html', {'visits':count})

def category(request, category_name_slug):
    context_dict = {}
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

            context_dict['result_list'] = result_list
            context_dict['query'] = query

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        pass

    if not context_dict['query']:
        context_dict['query'] = category.name

    return render(request, 'rango/category.html', context_dict)
# context_dict = {}

# try:
#     category = Category.objects.get(slug = category_name_slug)
#     context_dict['category_name'] = category.name
#     context_dict['category_name_slug'] = category_name_slug
#     pages = Page.objects.filter(category=category).order_by('-views')
#     context_dict['pages'] = pages
    
#     context_dict['category'] = category

# except Category.DoesNotExist:
#     pass

# return render(request, 'rango/category.html', context_dict)
@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
            
        if form.is_valid():
            form.save(commit=True)
            return index(request)
            
        else:
            print form.errors
    else:
        form = CategoryForm()
        
        return render(request, 'rango/add_category.html', {'form': form})    
    
@login_required   
def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
                cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                # probably better to use a redirect here.
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form':form, 'category': cat, 'category_name_slug': category_name_slug}

    return render(request, 'rango/add_page.html', context_dict)    
    
def register(request):
    # if request.session.test_cookie_worked():
    #     print ">>>> TEST COOKIE WORKED!"
    #     request.session.delete_test_cookie()

    registered = False

    if request.method == 'POST':
        
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user

            
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            
            profile.save()
            registered = True

        
        else:
            print user_form.errors, profile_form.errors

    
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request,
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered} )    


def user_login(request):

   
    if request.method == 'POST':
        
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user:
            
            if user.is_active:
                
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                
                return HttpResponse("Your Rango account is disabled.")
        else:
          
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html', {})
    
@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')


def search(request):
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
    return render(request, 'rango/search.html', {'result_list': result_list})

def track_url(request):
        page_id = None
        url = '/rango/'
        if request.method == 'GET':
            if 'page_id' in request.GET:
                page_id = request.GET['page_id']
                try:
                    page = Page.objects.get(id=page_id)
                    page.views = page.views + 1
                    page.save()
                    url = page.url
                except:
                    pass
            return redirect(url)

@login_required
def like_category(request):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes =  likes
            cat.save()

    return HttpResponse(likes)

