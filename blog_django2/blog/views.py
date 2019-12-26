from django.shortcuts import render, get_object_or_404
from .models import Post,Comment
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.views.generic import ListView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .forms import EmailPostForm, CommentForm,SearchForm
from django.core.mail import send_mail
from taggit.models import Tag

def post_share(request,post_id):
    #receipt of an article by id
    post=get_object_or_404(Post, id=post_id,status='published')
    sent=False
    if request.method =='POST':
        #form was sent to save
        form=EmailPostForm(request.POST)
        if form.is_valid():
            #all fields are validate
            cd=form.cleaned_data
            #sending mail
            post_url= request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'],cd['email'],post.title)
            message='Read "{}" at {}\n\n{}\'s comments:{}'.format(post.title,post_url,cd['name'],cd['comments'])
            send_mail(subject,message, 'thonydemidovich@gmail.com',[cd['to']])
            sent=True
            return render(request,'blog/post/share.html',{'post':post,'form':form,'sent':sent})

    else:
            form=EmailPostForm()
            return render(request,'blog/post/share.html',
                          {'post':post , 'form':form ,'sent':sent})

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = "blog/post/list.html"

def post_list(request):
    object_list=Post.published.all()

    paginator=Paginator(object_list,3) #3 articles on page
    page= request.GET.get('page')
    try:
        posts=paginator.page(page)
    except PageNotAnInteger:
        # If page not integer , return firts page
        posts=paginator.page(1)
    except EmptyPage:
        # If page number more than pages count , return last
        posts=paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page':page ,'posts':posts})

def post_detail(request,year,month,day,post):
    post=get_object_or_404(Post,slug=post,status='published',publish__year=year,
                           publish__month=month,publish__day=day)
    #list of active comments
    comments=post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        #user send comment
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            #create comment but not save in database
            new_comment=comment_form.save(commit=False)
            #bind comment and article
            new_comment.post=post
            #save comment in datebase
            new_comment.save()
    else:
            comment_form=CommentForm()
    return render(request, 'blog/post/detail.html',{'post':post,
                                                    'comments':comments,'new_comment':new_comment,
                                                    'comment_form':comment_form})

def post_search(request):
    form = SearchForm()
    query=None
    results = []
    if 'query' in request.GET:
        form=SearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data['query']
        search_vector=SearchVector('title',weight='A')+SearchVector('body',weight='B')
        search_query=SearchQuery(query)
        results=Post.objects.annotate(
        search=search_vector,
        rank=SearchRank(search_vector,search_query)
        ).filter(rank__gte=0.3).order_by('-rank')
    return render(request,'blog/post/search.html',{'form':form,'query':query,'results':results})

# Create your views here.
